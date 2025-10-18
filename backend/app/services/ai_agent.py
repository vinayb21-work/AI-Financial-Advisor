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
            rag_results = await self.rag_service.search(message, limit=5)
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
        prompt = f"""You are an AI assistant for financial advisors. You help manage emails, calendar events, and Hubspot CRM contacts.

You have access to the following information from the user's emails, calendar, and Hubspot:

{rag_context}

The user has given you the following ongoing instructions:
{instructions if instructions else "No ongoing instructions yet."}

"""
        
        if context:
            prompt += f"\nThe user has set the context to: {context}\n"
        
        prompt += """
When the user asks you to do something:
1. Use the available tools to complete the task
2. If a task requires multiple steps or waiting for a response, create a task to track it
3. Be proactive and helpful
4. When scheduling meetings, check the calendar for availability
5. When emailing, be professional and concise
6. When creating Hubspot contacts, include relevant information from emails

When the user gives you an ongoing instruction (e.g., "When someone emails me..."), remember it and apply it proactively.

Be conversational and helpful!
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

