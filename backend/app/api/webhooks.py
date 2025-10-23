from fastapi import APIRouter, Depends, Request, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.webhook_subscription import WebhookSubscription
from app.services.rag_service import RAGService
from app.services.gmail_service import GmailService
from app.services.calendar_service import CalendarService
from app.services.hubspot_service import HubspotService
from app.services.proactive_agent_service import ProactiveAgentService
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/gmail")
async def gmail_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Handle Gmail webhook notifications"""
    try:
        data = await request.json()
        logger.info(f"Gmail webhook received: {data}")
        
        # Process webhook in background
        background_tasks.add_task(process_gmail_webhook, db, data)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing Gmail webhook: {e}")
        return {"status": "error", "message": str(e)}

async def process_gmail_webhook(data: dict):
    """Process Gmail webhook in background"""
    async with AsyncSessionLocal() as db:
        try:
            # Gmail pushes use Cloud Pub/Sub, which sends base64 encoded data
            # For now, log and skip detailed processing
            logger.info(f"Gmail webhook data: {data}")
            
            # In production, you would:
            # 1. Decode the Pub/Sub message
            # 2. Extract the history ID
            # 3. Fetch changes since last sync
            # 4. Update RAG database
            
        except Exception as e:
            logger.error(f"Error in Gmail webhook processing: {e}")

@router.post("/calendar")
async def calendar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_goog_channel_id: str = Header(None),
    x_goog_resource_id: str = Header(None),
    x_goog_resource_state: str = Header(None)
):
    """Handle Calendar webhook notifications"""
    try:
        logger.info(f"Calendar webhook received - State: {x_goog_resource_state}, Channel: {x_goog_channel_id}")
        
        # Ignore sync messages (just webhook setup confirmation)
        if x_goog_resource_state == 'sync':
            return {"status": "ok"}
        
        # Process actual changes
        background_tasks.add_task(
            process_calendar_webhook,
            x_goog_channel_id,
            x_goog_resource_id
        )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing Calendar webhook: {e}")
        return {"status": "error", "message": str(e)}

async def process_calendar_webhook(channel_id: str, resource_id: str):
    """Process Calendar webhook in background"""
    async with AsyncSessionLocal() as db:
        try:
            # Find subscription
            result = await db.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.channel_id == channel_id,
                    WebhookSubscription.resource_id == resource_id,
                    WebhookSubscription.active == True
                )
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                logger.warning(f"No active subscription found for channel {channel_id}")
                return
            
            # Fetch user
            result = await db.execute(
                select(User).where(User.id == subscription.user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User not found for subscription {subscription.id}")
                return
            
            logger.info(f"Syncing calendar for user {user.id} due to webhook")
            
            # Fetch latest calendar events
            calendar_service = CalendarService(user, db)
            events = await calendar_service.fetch_events()
            
            # Update RAG database
            rag_service = RAGService(db, user)
            await rag_service.import_calendar_events(events)
            
            # Update user sync timestamp
            from datetime import datetime
            user.last_calendar_sync = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Calendar sync completed for user {user.id}")
            
            # Trigger proactive agent to check if action needed
            proactive_service = ProactiveAgentService(db, user)
            for event in events:
                event_data = {
                    'summary': event.get('summary', ''),
                    'start': event.get('start', ''),
                    'end': event.get('end', ''),
                    'attendees': event.get('attendees', [])
                }
                await proactive_service.process_event('calendar', event_data)
            
        except Exception as e:
            logger.error(f"Error in Calendar webhook processing: {e}")
            await db.rollback()

@router.post("/hubspot")
async def hubspot_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle Hubspot webhook notifications"""
    try:
        data = await request.json()
        logger.info(f"Hubspot webhook received: {data}")
        
        background_tasks.add_task(process_hubspot_webhook, data)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing Hubspot webhook: {e}")
        return {"status": "error", "message": str(e)}

async def process_hubspot_webhook(data: dict):
    """Process Hubspot webhook in background"""
    async with AsyncSessionLocal() as db:
        try:
            # Hubspot sends an array of events
            for event in data:
                object_id = event.get('objectId')
                portal_id = event.get('portalId')
                
                # Find user by portal/account
                # For now, we'll sync all Hubspot users
                result = await db.execute(
                    select(User).where(
                        User.hubspot_connected == True
                    )
                )
                users = result.scalars().all()
                
                for user in users:
                    logger.info(f"Syncing Hubspot for user {user.id} due to webhook")
                    
                    # Fetch updated contacts
                    hubspot_service = HubspotService(user, db)
                    contacts = await hubspot_service.fetch_contacts()
                    
                    # Update RAG database
                    rag_service = RAGService(db, user)
                    await rag_service.import_hubspot_contacts(contacts)
                    
                    # Trigger proactive agent for hubspot contacts
                    proactive_service = ProactiveAgentService(db, user)
                    for contact in contacts:
                        try:
                            event_data = {
                                'id': contact.get('id'),
                                'email': contact.get('properties', {}).get('email', ''),
                                'firstname': contact.get('properties', {}).get('firstname', ''),
                                'lastname': contact.get('properties', {}).get('lastname', '')
                            }
                            await proactive_service.process_event('hubspot', event_data)
                        except Exception as e:
                            logger.error(f"Error processing proactive action for hubspot contact: {e}")
                            continue

                    # Update user sync timestamp
                    from datetime import datetime
                    user.last_hubspot_sync = datetime.utcnow()
                    await db.commit()

                    logger.info(f"Hubspot sync completed for user {user.id} - processed {len(contacts)} contacts")
            
        except Exception as e:
            logger.error(f"Error in Hubspot webhook processing: {e}")
            await db.rollback()

