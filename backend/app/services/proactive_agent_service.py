from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List
import logging
import json

from app.models.user import User
from app.models.instruction import OngoingInstruction
from app.models.task import Task, TaskStatus
from app.services.ai_agent import AIAgent
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

class ProactiveAgentService:
    """Service to handle proactive agent actions based on webhooks"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.ai_agent = AIAgent(db, user)
        self.rag_service = RAGService(db, user)
    
    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an event and trigger proactive actions"""
        try:
            logger.info(f"Processing {event_type} event for user {self.user.id}")
            
            # Get relevant ongoing instructions
            instructions = await self._get_relevant_instructions(event_type)
            
            # Get pending tasks
            pending_tasks = await self._get_pending_tasks()
            
            # If no instructions and no pending tasks, skip
            if not instructions and not pending_tasks:
                logger.info(f"No ongoing instructions or tasks for {event_type}")
                return {"action_taken": False}
            
            # Build context for the agent
            context = await self._build_event_context(event_type, event_data, instructions, pending_tasks)
            
            # Ask the agent if it wants to take action
            prompt = self._build_proactive_prompt(event_type, event_data, instructions, pending_tasks)
            
            # Process with AI agent
            response = await self.ai_agent.process_message(
                message=prompt,
                thread_id=None,  # No specific thread for proactive actions
                context=context
            )
            
            logger.info(f"Proactive agent response: {response.get('content', '')[:200]}")
            
            return {
                "action_taken": True,
                "response": response.get('content'),
                "tool_calls": response.get('tool_calls', [])
            }
            
        except Exception as e:
            logger.error(f"Error in proactive agent processing: {e}")
            return {"action_taken": False, "error": str(e)}
    
    async def _get_relevant_instructions(self, event_type: str) -> List[OngoingInstruction]:
        """Get ongoing instructions relevant to this event type"""
        result = await self.db.execute(
            select(OngoingInstruction).where(
                OngoingInstruction.user_id == self.user.id,
                OngoingInstruction.trigger_type == event_type,
                OngoingInstruction.active == True
            )
        )
        return list(result.scalars().all())
    
    async def _get_pending_tasks(self) -> List[Task]:
        """Get pending tasks that might be relevant"""
        result = await self.db.execute(
            select(Task).where(
                Task.user_id == self.user.id,
                Task.status == TaskStatus.PENDING
            ).order_by(Task.created_at.desc()).limit(10)
        )
        return list(result.scalars().all())
    
    async def _build_event_context(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        instructions: List[OngoingInstruction],
        tasks: List[Task]
    ) -> str:
        """Build context for the agent"""
        context_parts = []
        
        # Add event information
        context_parts.append(f"## Event Type: {event_type}")
        context_parts.append(f"## Event Data:\n{json.dumps(event_data, indent=2)}")
        
        # Add ongoing instructions
        if instructions:
            context_parts.append("\n## Active Instructions:")
            for inst in instructions:
                context_parts.append(f"- {inst.instruction}")
        
        # Add pending tasks
        if tasks:
            context_parts.append("\n## Pending Tasks:")
            for task in tasks:
                context_parts.append(f"- {task.description}")
                if task.waiting_for:
                    context_parts.append(f"  Waiting for: {task.waiting_for}")
        
        return "\n".join(context_parts)
    
    def _build_proactive_prompt(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        instructions: List[OngoingInstruction],
        tasks: List[Task]
    ) -> str:
        """Build prompt for proactive agent"""
        prompt_parts = []
        
        prompt_parts.append(f"A {event_type} event has occurred.")
        
        # Extract key information based on event type
        if event_type == "gmail":
            sender = event_data.get('from', 'Unknown')
            subject = event_data.get('subject', 'No subject')
            prompt_parts.append(f"New email from {sender}: '{subject}'")
            
        elif event_type == "calendar":
            event_name = event_data.get('summary', 'Unknown event')
            prompt_parts.append(f"Calendar event: '{event_name}'")
            
        elif event_type == "hubspot":
            change_type = event_data.get('changeType', 'Unknown')
            prompt_parts.append(f"Hubspot change: {change_type}")
        
        # Add instructions context
        if instructions:
            prompt_parts.append("\nYou have the following ongoing instructions:")
            for inst in instructions:
                prompt_parts.append(f"- {inst.instruction}")
        
        # Add task context
        if tasks:
            prompt_parts.append("\nYou have pending tasks:")
            for task in tasks:
                prompt_parts.append(f"- {task.description}")
                if task.waiting_for:
                    prompt_parts.append(f"  (Waiting for: {task.waiting_for})")
        
        prompt_parts.append("\nBased on this event, your instructions, and pending tasks:")
        prompt_parts.append("1. Should you take any action?")
        prompt_parts.append("2. If yes, what tools should you use?")
        prompt_parts.append("3. If this relates to a pending task, should the task be updated or completed?")
        prompt_parts.append("\nPlease evaluate and take appropriate action using the available tools.")
        
        return "\n".join(prompt_parts)
    
    async def check_new_email_sender(self, email_from: str) -> bool:
        """Check if email sender is a new contact (not in Hubspot)"""
        try:
            # Extract email address from "Name <email>" format
            if '<' in email_from and '>' in email_from:
                email = email_from.split('<')[1].split('>')[0].strip()
            else:
                email = email_from.strip()
            
            # Search in RAG for this email in Hubspot contacts
            query = f"contact email {email}"
            results = await self.rag_service.search(query, limit=5)
            
            # Check if any result is from Hubspot with this email
            for result in results:
                if result.get('source') == 'hubspot':
                    content = result.get('content', '').lower()
                    if email.lower() in content:
                        return False  # Found in Hubspot
            
            return True  # Not found - new sender
            
        except Exception as e:
            logger.error(f"Error checking new sender: {e}")
            return False

