from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from datetime import datetime, timedelta
import logging
import asyncio

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.services.gmail_service import GmailService
from app.services.rag_service import RAGService
from app.services.proactive_agent_service import ProactiveAgentService

logger = logging.getLogger(__name__)

# Create scheduler instance
scheduler = AsyncIOScheduler()

async def poll_gmail_for_all_users():
    """Check Gmail for all users and trigger proactive actions"""
    logger.info("Starting Gmail polling cycle...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all users with Gmail synced
            result = await db.execute(
                select(User).where(User.gmail_synced == True)
            )
            users = result.scalars().all()
            
            logger.info(f"Polling Gmail for {len(users)} user(s)")
            
            for user in users:
                try:
                    await poll_gmail_for_user(db, user)
                except Exception as e:
                    logger.error(f"Error polling Gmail for user {user.email}: {e}")
                    continue
            
            logger.info("Gmail polling cycle complete")
            
        except Exception as e:
            logger.error(f"Error in Gmail polling cycle: {e}")

async def poll_gmail_for_user(db, user: User):
    """Poll Gmail for a specific user"""
    try:
        # Determine since when to check
        if user.last_gmail_check:
            since_datetime = user.last_gmail_check
        else:
            # First time - check last 24 hours
            since_datetime = datetime.utcnow() - timedelta(hours=24)
        
        logger.info(f"Checking Gmail for {user.email} since {since_datetime}")
        
        # Fetch new emails
        gmail_service = GmailService(user)
        new_emails = await gmail_service.fetch_emails_since(since_datetime)
        
        if not new_emails:
            logger.info(f"No new emails for {user.email}")
            user.last_gmail_check = datetime.utcnow()
            await db.commit()
            return
        
        logger.info(f"Found {len(new_emails)} new email(s) for {user.email}")
        
        # Import new emails to RAG
        rag_service = RAGService(db, user)
        await rag_service.import_emails(new_emails)
        logger.info(f"Imported {len(new_emails)} emails to RAG for {user.email}")
        
        # Trigger proactive agent for each new email
        proactive_service = ProactiveAgentService(db, user)
        
        for email in new_emails:
            try:
                logger.info(f"Processing proactive actions for email: {email.get('subject', 'No subject')}")
                
                # Prepare event data
                event_data = {
                    'subject': email.get('subject', 'No subject'),
                    'from': email.get('from', 'Unknown'),
                    'to': email.get('to', 'Unknown'),
                    'date': email.get('date', ''),
                    'body': email.get('body', ''),
                    'snippet': email.get('snippet', '')
                }
                
                # Process event with proactive agent
                result = await proactive_service.process_event('gmail', event_data)
                
                if result.get('action_taken'):
                    logger.info(f"Proactive action taken for email from {email.get('from')}")
                    if result.get('tool_calls'):
                        logger.info(f"Tools called: {len(result.get('tool_calls', []))}")
                else:
                    logger.info(f"No proactive action needed for email from {email.get('from')}")
                
            except Exception as e:
                logger.error(f"Error processing proactive action for email: {e}")
                continue
        
        # Update last check time
        user.last_gmail_check = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Gmail polling complete for {user.email}")
        
    except Exception as e:
        logger.error(f"Error in poll_gmail_for_user: {e}")
        await db.rollback()

def start_gmail_poller():
    """Start the Gmail polling scheduler"""
    # Schedule polling every 5 minutes
    scheduler.add_job(
        poll_gmail_for_all_users,
        'interval',
        minutes=5,
        id='gmail_poller',
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )
    
    scheduler.start()
    logger.info("Gmail poller started - checking every 5 minutes")

def stop_gmail_poller():
    """Stop the Gmail polling scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Gmail poller stopped")

