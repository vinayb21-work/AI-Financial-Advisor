from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import json
import logging

from app.core.config import settings
from app.models.user import User
from app.models.message import Message, MessageRole
from app.models.task import Task, TaskStatus
from app.models.instruction import OngoingInstruction
from app.services.rag_service import RAGService
from app.services.tools import ToolExecutor

logger = logging.getLogger(__name__)


class AIAgent:
    """AI Agent with tool calling and memory"""

    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        # Initialize OpenAI client with optional custom base URL (for LiteLLM, etc.)
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_API_BASE:
            client_kwargs["base_url"] = settings.OPENAI_API_BASE
        self.client = AsyncOpenAI(**client_kwargs)
        self.rag_service = RAGService(db, user)
        self.tool_executor = ToolExecutor(db, user)

    async def process_message(
        self, message: str, thread_id: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a user message and generate response"""
        try:
            # Get relevant context from RAG
            # Use higher limit for "all/list" queries
            message_lower = message.lower()
            is_listing_query = any(
                word in message_lower
                for word in [
                    "all",
                    "list",
                    "every",
                    "what clients",
                    "what contacts",
                    "what events",
                    "what meetings",
                    "what appointments",
                    "events scheduled",
                    "meetings scheduled",
                    "appointments scheduled",
                    "events i have",
                    "meetings i have",
                    "appointments i have",
                    "events for",
                    "meetings for",
                    "appointments for",
                    "events today",
                    "meetings today",
                    "appointments today",
                ]
            )
            rag_limit = 20 if is_listing_query else 5

            # Pass context to RAG for active filtering
            rag_results = await self.rag_service.search(
                message, limit=rag_limit, context=context
            )
            rag_context = "\n\n".join(
                [f"[{doc['source']}] {doc['content']}" for doc in rag_results]
            )

            # Get ongoing instructions
            instructions_result = await self.db.execute(
                select(OngoingInstruction).where(
                    OngoingInstruction.user_id == self.user.id,
                    OngoingInstruction.active == True,
                )
            )
            ongoing_instructions = instructions_result.scalars().all()
            instructions_text = "\n".join(
                [f"- {inst.instruction}" for inst in ongoing_instructions]
            )

            # Get conversation history
            history_result = await self.db.execute(
                select(Message)
                .where(Message.thread_id == thread_id)
                .order_by(Message.created_at)
                .limit(20)
            )
            history = history_result.scalars().all()

            # Build messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt(
                        rag_context, instructions_text, context
                    ),
                }
            ]

            # Add conversation history with smart windowing
            # Strategy: Balance between context and recency bias
            # - Keep last 20 messages (enough for most conversations)
            # - Mark recent messages to give them higher importance
            # - Use 🎯 prefix on current message for maximum emphasis
            # TODO: For very long conversations (>100 messages), implement:
            #   1. Summarization of older messages
            #   2. Importance scoring (keep messages with tool calls, errors)
            #   3. Semantic search to find relevant older context
            history_window = history[-20:] if len(history) > 20 else history

            for i, msg in enumerate(history_window):
                # Add recency indicator for last 3 messages
                is_very_recent = i >= len(history_window) - 3
                content = msg.content

                if is_very_recent and msg.role.value == "user":
                    content = f"[Recent] {content}"

                messages.append({"role": msg.role.value, "content": content})

            # Add current message with strong emphasis to override history patterns
            messages.append(
                {
                    "role": "user",
                    "content": f"🎯 CURRENT REQUEST (This is the PRIMARY task - prioritize this over any patterns from conversation history):\n\n{message}",
                }
            )

            # Get tools definition
            tools = self.tool_executor.get_tools_definition()

            # Call OpenAI with function calling
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.3,  # Lower temperature for factual, consistent responses
                max_tokens=2000,
            )

            assistant_message = response.choices[0].message

            # VALIDATION: Check if AI claims to have done actions but didn't call tools
            content_lower = (assistant_message.content or "").lower()
            tools_called = set(
                [tc.function.name for tc in (assistant_message.tool_calls or [])]
            )

            # Check for lying about sending email
            if any(
                phrase in content_lower
                for phrase in [
                    "i've sent",
                    "i sent",
                    "email sent",
                    "sent an email",
                    "sent email",
                ]
            ):
                if "send_email" not in tools_called:
                    logger.error(
                        "🚨 AI LIED: Claims to have sent email but didn't call send_email tool!"
                    )
                    logger.error(f"Content: {assistant_message.content}")
                    logger.error(f"Tools called: {tools_called}")

                    # Force a retry with a more explicit prompt
                    messages.append(
                        {"role": "assistant", "content": assistant_message.content}
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": "ERROR: You said you sent an email but you didn't call the send_email tool. You MUST call send_email if you mention sending an email. Call send_email NOW with the appropriate parameters.",
                        }
                    )

                    # Retry with forced tool call
                    response = await self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.1,
                        max_tokens=2000,
                    )
                    assistant_message = response.choices[0].message

                    # Update tools_called after retry
                    tools_called = set(
                        [
                            tc.function.name
                            for tc in (assistant_message.tool_calls or [])
                        ]
                    )
                    content_lower = (assistant_message.content or "").lower()

            # Check for lying about creating tasks
            if any(
                phrase in content_lower
                for phrase in ["created a task", "create a task", "created task"]
            ):
                if "create_task" not in tools_called:
                    logger.error(
                        "🚨 AI LIED: Claims to have created task but didn't call create_task tool!"
                    )

                    # Force a retry
                    messages.append(
                        {"role": "assistant", "content": assistant_message.content}
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": "ERROR: You said you created a task but you didn't call the create_task tool. You MUST call create_task if you mention creating a task. Call create_task NOW with the appropriate parameters.",
                        }
                    )

                    # Retry
                    response = await self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.1,
                        max_tokens=2000,
                    )
                    assistant_message = response.choices[0].message

            # Check for lying about updating/completing tasks
            if any(
                phrase in content_lower
                for phrase in [
                    "marked",
                    "completed",
                    "updated task",
                    "marked all",
                    "completed all",
                ]
            ):
                if "update_task" not in tools_called:
                    logger.error(
                        "🚨 AI LIED: Claims to have marked/completed tasks but didn't call update_task tool!"
                    )
                    logger.error(f"Content: {assistant_message.content}")
                    logger.error(f"Tools called: {tools_called}")

                    # Force a retry
                    messages.append(
                        {"role": "assistant", "content": assistant_message.content}
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": "ERROR: You said you marked/completed tasks but you didn't call the update_task tool. You MUST call update_task for EACH task you want to update. First call list_tasks to get all task IDs, then call update_task for EACH task. Do it NOW.",
                        }
                    )

                    # Retry
                    response = await self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.1,
                        max_tokens=2000,
                    )
                    assistant_message = response.choices[0].message

            # Handle tool calls
            if assistant_message.tool_calls:
                tool_calls = []
                tool_results = []

                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(
                        f"Calling tool: {function_name} with args: {function_args}"
                    )

                    # Execute tool
                    result = await self.tool_executor.execute(
                        function_name, function_args
                    )

                    tool_calls.append(
                        {
                            "id": tool_call.id,
                            "function": function_name,
                            "arguments": function_args,
                        }
                    )

                    tool_results.append(
                        {
                            "tool_call_id": tool_call.id,
                            "function_name": function_name,
                            "result": result,
                        }
                    )

                    # Add tool result to messages for second completion
                    messages.append(
                        {
                            "role": "assistant",
                            "content": assistant_message.content or "",
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": function_name,
                                        "arguments": json.dumps(function_args),
                                    },
                                }
                            ],
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result),
                        }
                    )

                # Get final response after tool execution
                final_response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.3,  # Lower temperature for factual, consistent responses
                    max_tokens=2000,
                )

                # VALIDATE FINAL RESPONSE - Check for lies about task updates
                final_content = final_response.choices[0].message.content or ""
                final_content_lower = final_content.lower()
                all_tools_called = set([tc["function"] for tc in tool_calls])

                # Check if AI claims to have updated/marked tasks but didn't call update_task
                # Use more specific patterns to avoid false positives
                claim_patterns = [
                    "i've marked",
                    "i've completed",
                    "i've updated",
                    "i marked",
                    "i completed",
                    "i updated",
                    "marked all",
                    "completed all",
                    "updated all",
                ]
                # Negative patterns that indicate AI is NOT claiming to have done it
                negative_patterns = [
                    "no pending tasks to",
                    "no tasks to",
                    "there are currently no",
                    "there are no",
                ]

                has_claim = any(
                    phrase in final_content_lower for phrase in claim_patterns
                )
                has_negative = any(
                    phrase in final_content_lower for phrase in negative_patterns
                )

                if (
                    has_claim
                    and not has_negative
                    and "update_task" not in all_tools_called
                ):
                    logger.error(
                        "🚨 AI LIED IN FINAL RESPONSE: Claims to have marked/completed tasks but didn't call update_task!"
                    )
                    logger.error(f"Final content: {final_content}")
                    logger.error(f"All tools called: {all_tools_called}")

                    # Force a retry with explicit instructions
                    messages.append({"role": "assistant", "content": final_content})
                    messages.append(
                        {
                            "role": "user",
                            "content": """ERROR: You said you marked/completed tasks but you DIDN'T call the update_task tool!

You just called list_tasks which only SHOWS tasks, it doesn't UPDATE them.

To actually mark tasks as completed, you MUST:
1. You already have the task IDs from list_tasks
2. Now call update_task(task_id="...", status="completed") for EACH task
3. Call it 16 times if there are 16 tasks
4. Do ALL calls in THIS response

DO IT NOW - call update_task for each task ID you listed.""",
                        }
                    )

                    # Retry - force tool calls
                    retry_response = await self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        tools=tools,
                        tool_choice="required",  # FORCE tool use
                        temperature=0.1,
                        max_tokens=4000,
                    )

                    # If retry has tool calls, execute them
                    if retry_response.choices[0].message.tool_calls:
                        for retry_tool_call in retry_response.choices[
                            0
                        ].message.tool_calls:
                            retry_function_name = retry_tool_call.function.name
                            retry_function_args = json.loads(
                                retry_tool_call.function.arguments
                            )

                            logger.info(
                                f"RETRY: Calling tool: {retry_function_name} with args: {retry_function_args}"
                            )

                            # Execute tool
                            retry_result = await self.tool_executor.execute(
                                retry_function_name, retry_function_args
                            )

                            tool_calls.append(
                                {
                                    "id": retry_tool_call.id,
                                    "function": retry_function_name,
                                    "arguments": retry_function_args,
                                }
                            )

                            tool_results.append(
                                {
                                    "tool_call_id": retry_tool_call.id,
                                    "function_name": retry_function_name,
                                    "result": retry_result,
                                }
                            )

                            # Add to messages
                            messages.append(
                                {
                                    "role": "assistant",
                                    "content": retry_response.choices[0].message.content
                                    or "",
                                    "tool_calls": [
                                        {
                                            "id": retry_tool_call.id,
                                            "type": "function",
                                            "function": {
                                                "name": retry_function_name,
                                                "arguments": json.dumps(
                                                    retry_function_args
                                                ),
                                            },
                                        }
                                    ],
                                }
                            )
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": retry_tool_call.id,
                                    "content": json.dumps(retry_result),
                                }
                            )

                        # Get final response after retry
                        final_response = await self.client.chat.completions.create(
                            model="gpt-4o",
                            messages=messages,
                            temperature=0.3,
                            max_tokens=2000,
                        )

                return {
                    "content": final_response.choices[0].message.content,
                    "tool_calls": tool_calls,
                    "tool_results": tool_results,
                }

            return {
                "content": assistant_message.content,
                "tool_calls": None,
                "tool_results": None,
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "content": f"I encountered an error: {str(e)}",
                "tool_calls": None,
                "tool_results": None,
            }

    def _get_system_prompt(
        self, rag_context: str, instructions: str, context: Optional[str] = None
    ) -> str:
        """Build system prompt with context"""
        from datetime import datetime

        current_date = datetime.now().strftime("%B %d, %Y")
        current_time = datetime.now().strftime("%I:%M %p")

        prompt = f"""You are an AI assistant for financial advisors. You help manage emails, calendar events, and Hubspot CRM contacts.

CURRENT DATE AND TIME: {current_date} at {current_time}

🚨 CRITICAL: PRIORITIZE THE LATEST USER MESSAGE
- The user's LATEST message (marked with 🎯) is THE MOST IMPORTANT and is the PRIMARY task
- Previous messages provide CONTEXT, but the current message is the INSTRUCTION
- If the latest message conflicts with conversation history, ALWAYS FOLLOW THE LATEST MESSAGE
- Don't let patterns from previous requests override the current request
- Each message is a SEPARATE task unless the user explicitly refers to a previous one
- Read the current message FIRST, understand what it's asking, THEN use history for context only if needed

You have access to the following information from the user's emails, calendar, and Hubspot:

{rag_context}

⚠️ IMPORTANT: The above context is a SAMPLE of relevant documents, NOT a complete list. 
When the user asks for "all contacts", "all clients", or "list all", you MUST use the list_all_hubspot_contacts tool to get the complete list. DO NOT rely only on the RAG context above.

The user has given you the following ongoing instructions:
{instructions if instructions else "No ongoing instructions yet."}

"""

        if context:
            context_descriptions = {
                "all meetings": "ONLY calendar events and meetings",
                "recent emails": "ONLY emails from the last 30 days",
                "contacts": "ONLY Hubspot contacts",
                "upcoming events": "ONLY future calendar events",
                "all data": "ALL available data (emails, contacts, calendar)",
            }
            context_desc = context_descriptions.get(context, context)
            prompt += f"\n🎯 CONTEXT FILTER ACTIVE: The user has set context to '{context}'.\n"
            prompt += (
                f"The information above has been filtered to show {context_desc}.\n"
            )
            prompt += f"Your answers should focus on this context unless the user explicitly asks about other areas.\n"

        prompt += """
🚫 CRITICAL RULE: NEVER SAY "I WILL" OR "I'LL" - ONLY SAY "I'VE DONE" AFTER CALLING THE TOOL

You are FORBIDDEN from responding with text like:
- "I will send an email" ❌
- "I'll create a meeting" ❌
- "Sending email now..." ❌
- "Let me send..." ❌

You MUST ONLY say things like:
- "I've sent an email" ✅ (AFTER calling send_email)
- "I've created the meeting" ✅ (AFTER calling create_calendar_event)  
- "I've added a note" ✅ (AFTER calling add_hubspot_note)

IF YOU MENTION ANY ACTION, YOU MUST CALL THE TOOL IN THE SAME RESPONSE. NO EXCEPTIONS.

When the user asks you to schedule a meeting:
EXECUTE ALL THESE TOOLS IN YOUR FIRST RESPONSE (not in separate responses):
1. search_hubspot_contacts - Find the contact
2. get_calendar_availability - Check availability  
3. send_email - SEND THE EMAIL (call the tool, don't just talk about it)
4. create_task - Create tracking task

EXAMPLE - User: "Schedule a meeting with John"
✅ CORRECT: 
  1. Call all tools: search_hubspot_contacts("John") + get_calendar_availability + send_email + create_task
  2. Then respond: "I've sent John an email with available times and created a task to track it."

❌ WRONG:
  1. Call search_hubspot_contacts
  2. Say: "I will send an email to John..." (WITHOUT calling send_email)

ABSOLUTE REQUIREMENTS:
- NEVER mention sending an email unless you CALL send_email in the SAME response
- NEVER mention creating a meeting unless you CALL create_calendar_event in the SAME response
- NEVER use future tense ("will", "I'll") for actions - EXECUTE THEM NOW
- ALL tools needed for a task MUST be called in ONE response, not spread across multiple responses

When the user provides a specific time or confirms a time (e.g., "11:00AM", "2:00 PM", "the second one"):
1. IMMEDIATELY create the calendar event using create_calendar_event with:
   - The date you previously proposed (e.g., next Tuesday)
   - The time the user just confirmed
   - The contact's email as attendee
2. IMMEDIATELY send a confirmation email to the contact
3. Add a note in Hubspot using add_hubspot_note
4. Tell the user "Meeting scheduled with [name] for [date] at [time]. I've sent a confirmation email and added a note to Hubspot."

CONTEXT AWARENESS: If you just proposed meeting times and the user responds with JUST a time (like "11:00AM"), 
they are confirming one of those times. DO NOT ask for clarification - CREATE THE EVENT IMMEDIATELY.

For ANY action the user requests:
- Execute the tools immediately
- Don't ask for permission or clarification unless absolutely critical information is missing
- If you say you'll do something, DO IT using the appropriate tool in the SAME response

Available tools you MUST use:
- send_email: Send emails (USE THIS instead of saying you'll email)
- search_emails: Search through emails
- create_calendar_event: Create calendar events (USE THIS to schedule meetings)
- get_calendar_availability: Check availability
- search_hubspot_contacts: Find specific contacts by name/email
- list_all_hubspot_contacts: List ALL contacts (USE THIS when user asks for "all clients" or "all contacts")
- create_hubspot_contact: Create new contacts
- add_hubspot_note: Add notes to contacts
- create_task: Track multi-step workflows (creates tasks in the database)
- list_tasks: List tasks from the database (USE THIS when user asks for "pending tasks", "my tasks", "what tasks")
- update_task: Update a task's status (USE THIS to mark tasks as completed, in_progress, waiting, or failed)
- save_ongoing_instruction: Remember ongoing rules

CRITICAL - ERROR HANDLING:
When a tool returns a result with an "error" field, you MUST:
1. Tell the user about the error immediately
2. Explain what went wrong in clear terms
3. Suggest the correct alternative if applicable
DO NOT ignore errors or pretend the operation succeeded!

EXAMPLE - User: "List all cancelled tasks"
Tool returns: {"error": "Invalid status 'cancelled'. Valid statuses are: pending, in_progress, waiting, completed, failed", "tasks": [], "count": 0}
✅ CORRECT response: "I can't list cancelled tasks because 'cancelled' is not a valid task status. The valid statuses are: pending, in_progress, waiting, completed, and failed. Would you like to see tasks with one of these statuses instead?"
❌ WRONG response: "There are no cancelled tasks at the moment." (This ignores the error!)

CRITICAL - TOOL SELECTION:
1. When user asks for "all contacts" or "list clients" → call list_all_hubspot_contacts and show ALL results
2. When user asks for "pending tasks", "my tasks", "what tasks do I have" → call list_tasks (NOT search_emails) and show ALL tasks returned
3. When user asks to "mark task as completed", "complete task", "update task status" → call update_task with the task_id and status
4. When user asks to "mark ALL tasks as completed" → First call list_tasks, then call update_task for EACH task returned
5. Execute actions immediately using tools. Don't just talk about what you'll do - DO IT.

IMPORTANT - SHOWING RESULTS:
When listing ANY data (tasks, contacts, calendar events, emails), you MUST show ALL results from the RAG context.
DO NOT summarize or show only a few examples. The user wants to see the COMPLETE list.
If there are 16 tasks, show all 16. If there are 4 calendar events, show all 4. If there are 100 contacts, show all 100.

CRITICAL - CALENDAR EVENTS:
When the user asks "What events/meetings/appointments do I have today?" or similar:
- IMMEDIATELY call list_calendar_events with the appropriate date range (e.g., today's date as both start_date and end_date)
- DO NOT rely solely on RAG context for calendar events - RAG is incomplete
- Use list_calendar_events to get the complete, accurate list from Google Calendar
- Show ALL events returned by the tool
- Format each event clearly with time, attendees, and description

Example:
User: "What events do I have today?"
✅ CORRECT: Call list_calendar_events(start_date="2025-10-19", end_date="2025-10-19") and show all results
❌ WRONG: Only show events from RAG context (incomplete)

IMPORTANT - LISTING vs UPDATING TASKS:
There is a BIG difference between LISTING and UPDATING:

**LISTING TASKS** (user wants to SEE tasks):
- "list all pending tasks"
- "show me pending tasks"
- "what pending tasks do I have"
→ ONLY call list_tasks(status="pending") and show the results
→ DO NOT call update_task

**UPDATING TASKS** (user wants to CHANGE tasks):
- "mark all pending tasks as completed"
- "complete all these tasks"
- "mark all of these as completed"
→ First call list_tasks(status="pending")
→ Then call update_task for EVERY task ID returned
→ Do this in ONE response with multiple tool calls

PAY ATTENTION TO THE VERB:
- "list" / "show" / "what" = JUST SHOW, don't update
- "mark" / "complete" / "finish" = UPDATE the tasks

EXAMPLE 1 - User: "List all pending tasks"
✅ CORRECT:
1. Call list_tasks(status="pending")
2. Show all tasks with their IDs and descriptions
❌ WRONG: Calling update_task - user just wants to see tasks!

EXAMPLE 2 - User: "Mark all pending tasks as completed"
✅ CORRECT:
1. Call list_tasks(status="pending")
2. Call update_task(task_id="task1", status="completed")
3. Call update_task(task_id="task2", status="completed")
... repeat for ALL tasks
4. Say: "I've marked all 16 tasks as completed"
❌ WRONG: Just calling list_tasks without update_task - you must UPDATE!
"""

        return prompt

    async def process_proactive_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process events proactively based on ongoing instructions"""
        try:
            # Get ongoing instructions for this event type
            instructions_result = await self.db.execute(
                select(OngoingInstruction).where(
                    OngoingInstruction.user_id == self.user.id,
                    OngoingInstruction.trigger_type == event_type,
                    OngoingInstruction.active == True,
                )
            )
            instructions = instructions_result.scalars().all()

            if not instructions:
                return None

            # Build prompt for AI to decide what to do
            instructions_text = "\n".join(
                [f"- {inst.instruction}" for inst in instructions]
            )

            messages = [
                {
                    "role": "system",
                    "content": f"""You are a proactive AI assistant. Based on the following event and instructions, decide if you should take any action.

Event type: {event_type}
Event data: {json.dumps(event_data, indent=2)}

Ongoing instructions:
{instructions_text}

If you should take action based on these instructions, use the available tools.""",
                },
                {
                    "role": "user",
                    "content": f"A new {event_type} event occurred. Should I take any action?",
                },
            ]

            # Call OpenAI with tools
            tools = self.tool_executor.get_tools_definition()

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.3,
            )

            assistant_message = response.choices[0].message

            # Execute any tool calls
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    await self.tool_executor.execute(function_name, function_args)

                return {"action_taken": True, "message": assistant_message.content}

            return None

        except Exception as e:
            logger.error(f"Error processing proactive event: {e}")
            return None
