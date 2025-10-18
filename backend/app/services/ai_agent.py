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
        self,
        message: str,
        thread_id: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a user message and generate response"""
        try:
            # Get relevant context from RAG
            # Use higher limit for "all/list" queries
            message_lower = message.lower()
            is_listing_query = any(word in message_lower for word in ['all', 'list', 'every', 'what clients', 'what contacts'])
            rag_limit = 20 if is_listing_query else 5
            
            # Pass context to RAG for active filtering
            rag_results = await self.rag_service.search(message, limit=rag_limit, context=context)
            rag_context = "\n\n".join([
                f"[{doc['source']}] {doc['content']}"
                for doc in rag_results
            ])
            
            # Get ongoing instructions
            instructions_result = await self.db.execute(
                select(OngoingInstruction)
                .where(
                    OngoingInstruction.user_id == self.user.id,
                    OngoingInstruction.active == True
                )
            )
            ongoing_instructions = instructions_result.scalars().all()
            instructions_text = "\n".join([
                f"- {inst.instruction}"
                for inst in ongoing_instructions
            ])
            
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
                        rag_context,
                        instructions_text,
                        context
                    )
                }
            ]
            
            # Add conversation history
            for msg in history[-10:]:  # Last 10 messages
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Get tools definition
            tools = self.tool_executor.get_tools_definition()
            
            # Call OpenAI with function calling
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.3,  # Lower temperature for factual, consistent responses
                max_tokens=2000
            )
            
            assistant_message = response.choices[0].message
            
            # Handle tool calls
            if assistant_message.tool_calls:
                tool_calls = []
                tool_results = []
                
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Calling tool: {function_name} with args: {function_args}")
                    
                    # Execute tool
                    result = await self.tool_executor.execute(
                        function_name,
                        function_args
                    )
                    
                    tool_calls.append({
                        "id": tool_call.id,
                        "function": function_name,
                        "arguments": function_args
                    })
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "result": result
                    })
                    
                    # Add tool result to messages for second completion
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": json.dumps(function_args)
                                }
                            }
                        ]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Get final response after tool execution
                final_response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.3,  # Lower temperature for factual, consistent responses
                    max_tokens=2000
                )
                
                return {
                    "content": final_response.choices[0].message.content,
                    "tool_calls": tool_calls,
                    "tool_results": tool_results
                }
            
            return {
                "content": assistant_message.content,
                "tool_calls": None,
                "tool_results": None
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "content": f"I encountered an error: {str(e)}",
                "tool_calls": None,
                "tool_results": None
            }
    
    def _get_system_prompt(
        self,
        rag_context: str,
        instructions: str,
        context: Optional[str] = None
    ) -> str:
        """Build system prompt with context"""
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        current_time = datetime.now().strftime("%I:%M %p")
        
        prompt = f"""You are an AI assistant for financial advisors. You help manage emails, calendar events, and Hubspot CRM contacts.

CURRENT DATE AND TIME: {current_date} at {current_time}

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
                "all data": "ALL available data (emails, contacts, calendar)"
            }
            context_desc = context_descriptions.get(context, context)
            prompt += f"\n🎯 CONTEXT FILTER ACTIVE: The user has set context to '{context}'.\n"
            prompt += f"The information above has been filtered to show {context_desc}.\n"
            prompt += f"Your answers should focus on this context unless the user explicitly asks about other areas.\n"
        
        prompt += """
CRITICAL INSTRUCTIONS - YOU MUST EXECUTE ALL TOOLS IN THE SAME RESPONSE:

When the user asks you to schedule a meeting:
YOU MUST CALL ALL THESE TOOLS IN YOUR FIRST RESPONSE (not in separate responses):
1. search_hubspot_contacts - Find the contact
2. get_calendar_availability - Check availability  
3. send_email - ACTUALLY SEND THE EMAIL with time options (DO NOT just say you'll send it)
4. create_task - Create tracking task

IMPORTANT: Call ALL FOUR tools in your FIRST response. Do not say "I will send an email" - ACTUALLY call send_email tool NOW.

EXAMPLE - User says: "Schedule a meeting with John"
CORRECT RESPONSE: Call these tools in ONE response:
  - search_hubspot_contacts(query="John")
  - get_calendar_availability(start_date="2025-10-21", end_date="2025-10-21")
  - send_email(to="john@example.com", subject="Meeting Request", body="Hi John, would these times work: 10am, 2pm, 4pm?")
  - create_task(description="Schedule John meeting", waiting_for="email response")
Then say: "I've sent John an email and created a task"

WRONG RESPONSE: Call search_hubspot_contacts, then say "I'll send an email" WITHOUT actually calling send_email

DO NOT:
- Ask the user what time to schedule
- Ask for clarification on dates  
- Say "I will send" or "I'll send" - CALL THE TOOL NOW
- Return a response without calling send_email if you said you would send email
- Wait for the user to make decisions
- Call only ONE tool when you need to call MULTIPLE tools

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
- create_calendar_event: Create calendar events (USE THIS to schedule meetings)
- search_hubspot_contacts: Find specific contacts by name/email
- list_all_hubspot_contacts: List ALL contacts (USE THIS when user asks for "all clients" or "all contacts")
- create_hubspot_contact: Create new contacts
- add_hubspot_note: Add notes to contacts
- get_calendar_availability: Check availability
- create_task: Track multi-step workflows
- save_ongoing_instruction: Remember ongoing rules

REMEMBER: 
1. When user asks for "all contacts" or "list clients", call list_all_hubspot_contacts
2. Execute actions immediately using tools. Don't just talk about what you'll do - DO IT.
"""
        
        return prompt
    
    async def process_proactive_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process events proactively based on ongoing instructions"""
        try:
            # Get ongoing instructions for this event type
            instructions_result = await self.db.execute(
                select(OngoingInstruction)
                .where(
                    OngoingInstruction.user_id == self.user.id,
                    OngoingInstruction.trigger_type == event_type,
                    OngoingInstruction.active == True
                )
            )
            instructions = instructions_result.scalars().all()
            
            if not instructions:
                return None
            
            # Build prompt for AI to decide what to do
            instructions_text = "\n".join([
                f"- {inst.instruction}"
                for inst in instructions
            ])
            
            messages = [
                {
                    "role": "system",
                    "content": f"""You are a proactive AI assistant. Based on the following event and instructions, decide if you should take any action.

Event type: {event_type}
Event data: {json.dumps(event_data, indent=2)}

Ongoing instructions:
{instructions_text}

If you should take action based on these instructions, use the available tools."""
                },
                {
                    "role": "user",
                    "content": f"A new {event_type} event occurred. Should I take any action?"
                }
            ]
            
            # Call OpenAI with tools
            tools = self.tool_executor.get_tools_definition()
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.3
            )
            
            assistant_message = response.choices[0].message
            
            # Execute any tool calls
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    await self.tool_executor.execute(function_name, function_args)
                
                return {
                    "action_taken": True,
                    "message": assistant_message.content
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing proactive event: {e}")
            return None

