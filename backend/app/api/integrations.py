from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.instruction import OngoingInstruction
from app.models.task import Task, TaskStatus
from app.services.gmail_service import GmailService
from app.services.calendar_service import CalendarService
from app.services.hubspot_service import HubspotService
from app.services.rag_service import RAGService
from app.services.webhook_manager import WebhookManager
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


def format_datetime(dt: datetime) -> str:
    """Format datetime as ISO string with UTC indicator"""
    if dt is None:
        return None
    return dt.isoformat() + "Z" if not dt.tzinfo else dt.isoformat()


# Request models
class InstructionCreate(BaseModel):
    instruction: str
    trigger_type: str  # 'gmail', 'calendar', 'hubspot'


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    context: Optional[dict] = None


@router.post("/sync/gmail")
async def sync_gmail(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync Gmail emails and import into RAG system"""
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Google account not connected")

    # Run sync in background, pass user_id instead of user object
    background_tasks.add_task(sync_gmail_background, current_user.id)

    return {"message": "Gmail sync started", "status": "processing"}


async def sync_gmail_background(user_id: str):
    """Background task to sync Gmail"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    from datetime import datetime
    import logging

    logger = logging.getLogger(__name__)

    async with AsyncSessionLocal() as db:
        try:
            # Fetch user from database
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found")
                return

            gmail_service = GmailService(user)
            emails = await gmail_service.fetch_emails(max_results=100)

            rag_service = RAGService(db, user)
            await rag_service.import_emails(emails)

            # Trigger proactive agent for new emails
            from app.services.proactive_agent_service import ProactiveAgentService

            proactive_service = ProactiveAgentService(db, user)

            for email in emails:
                try:
                    event_data = {
                        "subject": email.get("subject", "No subject"),
                        "from": email.get("from", "Unknown"),
                        "to": email.get("to", "Unknown"),
                        "date": email.get("date", ""),
                        "body": email.get("body", ""),
                        "snippet": email.get("snippet", ""),
                    }
                    await proactive_service.process_event("gmail", event_data)
                except Exception as e:
                    logger.error(f"Error processing proactive action for email: {e}")
                    continue

            # Update user sync status
            user.gmail_synced = True
            user.last_gmail_sync = datetime.utcnow()
            user.last_gmail_check = datetime.utcnow()  # Also update check time
            await db.commit()

            logger.info(
                f"Gmail sync completed for user {user_id} - processed {len(emails)} emails"
            )

        except Exception as e:
            logger.error(f"Error syncing Gmail: {e}")
            await db.rollback()


@router.post("/sync/calendar")
async def sync_calendar(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync Google Calendar events"""
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Google account not connected")

    # Run sync in background, pass user_id instead of user object
    background_tasks.add_task(sync_calendar_background, current_user.id)

    return {"message": "Calendar sync started", "status": "processing"}


async def sync_calendar_background(user_id: str):
    """Background task to sync Calendar"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    from datetime import datetime
    import logging

    logger = logging.getLogger(__name__)

    async with AsyncSessionLocal() as db:
        try:
            # Fetch user from database
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found")
                return

            calendar_service = CalendarService(user)
            events = await calendar_service.fetch_events()

            rag_service = RAGService(db, user)
            await rag_service.import_calendar_events(events)

            # Trigger proactive agent for calendar events
            from app.services.proactive_agent_service import ProactiveAgentService

            proactive_service = ProactiveAgentService(db, user)

            for event in events:
                try:
                    event_data = {
                        "summary": event.get("summary", "Unknown event"),
                        "start": event.get("start", ""),
                        "end": event.get("end", ""),
                        "attendees": event.get("attendees", []),
                    }
                    await proactive_service.process_event("calendar", event_data)
                except Exception as e:
                    logger.error(
                        f"Error processing proactive action for calendar event: {e}"
                    )
                    continue

            # Update user sync status
            user.calendar_synced = True
            user.last_calendar_sync = datetime.utcnow()
            await db.commit()

            logger.info(
                f"Calendar sync completed for user {user_id} - processed {len(events)} events"
            )

        except Exception as e:
            logger.error(f"Error syncing Calendar: {e}")
            await db.rollback()


@router.post("/sync/hubspot")
async def sync_hubspot(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync Hubspot contacts and notes"""
    if not current_user.hubspot_access_token:
        raise HTTPException(status_code=400, detail="Hubspot account not connected")

    # Run sync in background, pass user_id instead of user object
    background_tasks.add_task(sync_hubspot_background, current_user.id)

    return {"message": "Hubspot sync started", "status": "processing"}


async def sync_hubspot_background(user_id: str):
    """Background task to sync Hubspot"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    from datetime import datetime
    import logging

    logger = logging.getLogger(__name__)

    async with AsyncSessionLocal() as db:
        try:
            # Fetch user from database
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found")
                return

            hubspot_service = HubspotService(user, db)
            contacts = await hubspot_service.fetch_contacts()

            rag_service = RAGService(db, user)
            await rag_service.import_hubspot_contacts(contacts)

            # Trigger proactive agent for hubspot contacts
            from app.services.proactive_agent_service import ProactiveAgentService

            proactive_service = ProactiveAgentService(db, user)

            for contact in contacts:
                try:
                    event_data = {
                        "id": contact.get("id"),
                        "email": contact.get("properties", {}).get("email", ""),
                        "firstname": contact.get("properties", {}).get("firstname", ""),
                        "lastname": contact.get("properties", {}).get("lastname", ""),
                    }
                    await proactive_service.process_event("hubspot", event_data)
                except Exception as e:
                    logger.error(
                        f"Error processing proactive action for hubspot contact: {e}"
                    )
                    continue

            # Update user sync status
            user.hubspot_synced = True
            user.last_hubspot_sync = datetime.utcnow()
            await db.commit()

            logger.info(
                f"Hubspot sync completed for user {user_id} - processed {len(contacts)} contacts"
            )

        except Exception as e:
            logger.error(f"Error syncing Hubspot: {e}")
            await db.rollback()


@router.get("/sync/status")
async def get_sync_status(current_user: User = Depends(get_current_user)):
    """Get sync status for all integrations"""
    return {
        "gmail": {
            "synced": current_user.gmail_synced,
            "last_sync": (
                current_user.last_gmail_sync.isoformat()
                if current_user.last_gmail_sync
                else None
            ),
        },
        "calendar": {
            "synced": current_user.calendar_synced,
            "last_sync": (
                current_user.last_calendar_sync.isoformat()
                if current_user.last_calendar_sync
                else None
            ),
        },
        "hubspot": {
            "synced": current_user.hubspot_synced,
            "last_sync": (
                current_user.last_hubspot_sync.isoformat()
                if current_user.last_hubspot_sync
                else None
            ),
        },
    }


@router.post("/webhooks/setup")
async def setup_webhooks(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Set up webhooks for all connected services"""
    webhook_manager = WebhookManager(db, current_user)

    results = {}

    # Setup Calendar webhook (most reliable)
    if current_user.google_access_token:
        calendar_result = await webhook_manager.setup_calendar_webhook()
        results["calendar"] = calendar_result

    # Setup Hubspot webhook
    if current_user.hubspot_access_token:
        hubspot_result = await webhook_manager.setup_hubspot_webhook()
        results["hubspot"] = hubspot_result

    # Gmail requires Pub/Sub setup (more complex)
    results["gmail"] = {
        "status": "not_implemented",
        "message": "Gmail webhooks require Google Cloud Pub/Sub setup",
    }

    return results


# Ongoing Instructions Management
@router.get("/instructions")
async def get_instructions(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all ongoing instructions"""
    result = await db.execute(
        select(OngoingInstruction)
        .where(OngoingInstruction.user_id == current_user.id)
        .order_by(OngoingInstruction.created_at.desc())
    )
    instructions = result.scalars().all()

    return {
        "instructions": [
            {
                "id": str(inst.id),
                "instruction": inst.instruction,
                "trigger_type": inst.trigger_type,
                "active": inst.active,
                "created_at": format_datetime(inst.created_at),
            }
            for inst in instructions
        ]
    }


@router.post("/instructions")
async def create_instruction(
    instruction_data: InstructionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new ongoing instruction"""
    instruction = OngoingInstruction(
        user_id=current_user.id,
        instruction=instruction_data.instruction,
        trigger_type=instruction_data.trigger_type,
        active=True,
    )
    db.add(instruction)
    await db.commit()
    await db.refresh(instruction)

    return {
        "id": str(instruction.id),
        "instruction": instruction.instruction,
        "trigger_type": instruction.trigger_type,
        "active": instruction.active,
    }


@router.delete("/instructions/{instruction_id}")
async def delete_instruction(
    instruction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an ongoing instruction"""
    from uuid import UUID

    result = await db.execute(
        select(OngoingInstruction).where(
            OngoingInstruction.id == UUID(instruction_id),
            OngoingInstruction.user_id == current_user.id,
        )
    )
    instruction = result.scalar_one_or_none()

    if not instruction:
        raise HTTPException(status_code=404, detail="Instruction not found")

    await db.delete(instruction)
    await db.commit()

    return {"message": "Instruction deleted"}


# Task Management
@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all tasks"""
    query = select(Task).where(Task.user_id == current_user.id)

    if status:
        query = query.where(Task.status == TaskStatus(status.upper()))

    query = query.order_by(Task.created_at.desc())

    result = await db.execute(query)
    tasks = result.scalars().all()

    return {
        "tasks": [
            {
                "id": str(task.id),
                "description": task.description,
                "status": task.status.value,
                "waiting_for": task.waiting_for,
                "context": task.context,
                "created_at": format_datetime(task.created_at),
                "updated_at": (
                    format_datetime(task.updated_at) if task.updated_at else None
                ),
            }
            for task in tasks
        ]
    }


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a task"""
    from uuid import UUID
    from datetime import datetime

    result = await db.execute(
        select(Task).where(Task.id == UUID(task_id), Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_data.status:
        task.status = TaskStatus(task_data.status.upper())
    if task_data.context is not None:
        task.context = task_data.context

    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    return {
        "id": str(task.id),
        "description": task.description,
        "status": task.status.value,
        "context": task.context,
    }
