from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.models.user import User
from app.models.webhook_subscription import WebhookSubscription
from app.core.config import settings
from datetime import datetime, timedelta
import uuid
import logging
import aiohttp

logger = logging.getLogger(__name__)

class WebhookManager:
    """Manages webhook subscriptions for Google and Hubspot services"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def setup_gmail_webhook(self) -> dict:
        """Set up Gmail push notifications"""
        try:
            if not self.user.google_access_token:
                raise ValueError("User not connected to Google")
            
            credentials = Credentials(
                token=self.user.google_access_token,
                refresh_token=self.user.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET
            )
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create unique channel ID
            channel_id = str(uuid.uuid4())
            
            # Set up watch
            request = {
                'labelIds': ['INBOX'],
                'topicName': f'projects/{settings.GOOGLE_PROJECT_ID}/topics/gmail-notifications'
            }
            
            # Note: This requires Google Cloud Pub/Sub to be set up
            # For now, we'll use polling as a fallback
            logger.info(f"Gmail watch setup would require Pub/Sub topic")
            
            return {
                "status": "pending",
                "message": "Gmail webhooks require Google Cloud Pub/Sub setup"
            }
            
        except Exception as e:
            logger.error(f"Error setting up Gmail webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def setup_calendar_webhook(self) -> dict:
        """Set up Google Calendar push notifications"""
        try:
            if not self.user.google_access_token:
                raise ValueError("User not connected to Google")
            
            credentials = Credentials(
                token=self.user.google_access_token,
                refresh_token=self.user.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET
            )
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Create unique channel ID
            channel_id = str(uuid.uuid4())
            
            # Webhook URL
            webhook_url = f"{settings.BACKEND_URL}/webhooks/calendar"
            
            # Set up watch on primary calendar
            watch_request = {
                'id': channel_id,
                'type': 'web_hook',
                'address': webhook_url,
                'expiration': int((datetime.utcnow() + timedelta(days=7)).timestamp() * 1000)
            }
            
            response = service.events().watch(
                calendarId='primary',
                body=watch_request
            ).execute()
            
            # Save subscription to database
            subscription = WebhookSubscription(
                user_id=self.user.id,
                service='calendar',
                resource_id=response['resourceId'],
                channel_id=channel_id,
                expiration=datetime.utcnow() + timedelta(days=7),
                active=True
            )
            
            self.db.add(subscription)
            await self.db.commit()
            
            logger.info(f"Calendar webhook setup for user {self.user.id}")
            
            return {
                "status": "success",
                "channel_id": channel_id,
                "resource_id": response['resourceId'],
                "expiration": subscription.expiration.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error setting up Calendar webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def setup_hubspot_webhook(self) -> dict:
        """Set up Hubspot webhook subscriptions"""
        try:
            if not self.user.hubspot_access_token:
                raise ValueError("User not connected to Hubspot")
            
            # Webhook URL
            webhook_url = f"{settings.BACKEND_URL}/webhooks/hubspot"
            
            # Subscribe to contact property changes
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.user.hubspot_access_token}',
                    'Content-Type': 'application/json'
                }
                
                # Create webhook subscription
                subscription_data = {
                    'eventType': 'contact.propertyChange',
                    'propertyName': '*',  # All properties
                    'active': True,
                    'webhookUrl': webhook_url
                }
                
                async with session.post(
                    'https://api.hubapi.com/webhooks/v3/subscriptions',
                    headers=headers,
                    json=subscription_data
                ) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        
                        # Save subscription to database
                        subscription = WebhookSubscription(
                            user_id=self.user.id,
                            service='hubspot',
                            resource_id=str(result['id']),
                            channel_id=str(uuid.uuid4()),
                            active=True
                        )
                        
                        self.db.add(subscription)
                        await self.db.commit()
                        
                        logger.info(f"Hubspot webhook setup for user {self.user.id}")
                        
                        return {
                            "status": "success",
                            "subscription_id": result['id']
                        }
                    else:
                        error_text = await resp.text()
                        logger.error(f"Hubspot webhook error: {error_text}")
                        return {"status": "error", "message": error_text}
            
        except Exception as e:
            logger.error(f"Error setting up Hubspot webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def renew_calendar_webhook(self, subscription: WebhookSubscription) -> bool:
        """Renew a calendar webhook subscription"""
        try:
            # Stop old channel
            credentials = Credentials(
                token=self.user.google_access_token,
                refresh_token=self.user.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET
            )
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Stop old channel
            service.channels().stop(body={
                'id': subscription.channel_id,
                'resourceId': subscription.resource_id
            }).execute()
            
            # Create new subscription
            result = await self.setup_calendar_webhook()
            
            if result['status'] == 'success':
                # Mark old subscription as inactive
                subscription.active = False
                await self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error renewing calendar webhook: {e}")
            return False
    
    async def cleanup_expired_subscriptions(self):
        """Clean up expired webhook subscriptions"""
        try:
            # Find expired subscriptions
            result = await self.db.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.user_id == self.user.id,
                    WebhookSubscription.active == True,
                    WebhookSubscription.expiration < datetime.utcnow()
                )
            )
            expired = result.scalars().all()
            
            for subscription in expired:
                if subscription.service == 'calendar':
                    await self.renew_calendar_webhook(subscription)
            
            logger.info(f"Cleaned up {len(expired)} expired subscriptions")
            
        except Exception as e:
            logger.error(f"Error cleaning up subscriptions: {e}")

