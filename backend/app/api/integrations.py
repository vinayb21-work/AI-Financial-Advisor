from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.gmail_service import GmailService
from app.services.calendar_service import CalendarService
from app.services.hubspot_service import HubspotService
from app.services.rag_service import RAGService
from app.services.webhook_manager import WebhookManager

router = APIRouter()

@router.post("/sync/gmail")
async def sync_gmail(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync Gmail emails and import into RAG system"""
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Google account not connected")
    
    # Run sync in background, pass user_id instead of user object
    background_tasks.add_task(
        sync_gmail_background,
        current_user.id
    )
    
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
            
            # Update user sync status
            user.gmail_synced = True
            user.last_gmail_sync = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Gmail sync completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error syncing Gmail: {e}")
            await db.rollback()

@router.post("/sync/calendar")
async def sync_calendar(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync Google Calendar events"""
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Google account not connected")
    
    # Run sync in background, pass user_id instead of user object
    background_tasks.add_task(
        sync_calendar_background,
        current_user.id
    )
    
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
            
            # Update user sync status
            user.calendar_synced = True
            user.last_calendar_sync = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Calendar sync completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error syncing Calendar: {e}")
            await db.rollback()

@router.post("/sync/hubspot")
async def sync_hubspot(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync Hubspot contacts and notes"""
    if not current_user.hubspot_access_token:
        raise HTTPException(status_code=400, detail="Hubspot account not connected")
    
    # Run sync in background, pass user_id instead of user object
    background_tasks.add_task(
        sync_hubspot_background,
        current_user.id
    )
    
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
            
            hubspot_service = HubspotService(user)
            contacts = await hubspot_service.fetch_contacts()
            
            rag_service = RAGService(db, user)
            await rag_service.import_hubspot_contacts(contacts)
            
            # Update user sync status
            user.hubspot_synced = True
            user.last_hubspot_sync = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Hubspot sync completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error syncing Hubspot: {e}")
            await db.rollback()

@router.get("/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user)
):
    """Get sync status for all integrations"""
    return {
        "gmail": {
            "synced": current_user.gmail_synced,
            "last_sync": current_user.last_gmail_sync.isoformat() if current_user.last_gmail_sync else None
        },
        "calendar": {
            "synced": current_user.calendar_synced,
            "last_sync": current_user.last_calendar_sync.isoformat() if current_user.last_calendar_sync else None
        },
        "hubspot": {
            "synced": current_user.hubspot_synced,
            "last_sync": current_user.last_hubspot_sync.isoformat() if current_user.last_hubspot_sync else None
        }
    }

@router.post("/webhooks/setup")
async def setup_webhooks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set up webhooks for all connected services"""
    webhook_manager = WebhookManager(db, current_user)
    
    results = {}
    
    # Setup Calendar webhook (most reliable)
    if current_user.google_access_token:
        calendar_result = await webhook_manager.setup_calendar_webhook()
        results['calendar'] = calendar_result
    
    # Setup Hubspot webhook
    if current_user.hubspot_access_token:
        hubspot_result = await webhook_manager.setup_hubspot_webhook()
        results['hubspot'] = hubspot_result
    
    # Gmail requires Pub/Sub setup (more complex)
    results['gmail'] = {
        "status": "not_implemented",
        "message": "Gmail webhooks require Google Cloud Pub/Sub setup"
    }
    
    return results

