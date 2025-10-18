from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from typing import List, Dict, Any
import logging
from datetime import datetime

from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

class GmailService:
    """Gmail API service"""
    
    def __init__(self, user: User):
        self.user = user
        self.credentials = Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        self.service = build('gmail', 'v1', credentials=self.credentials)
    
    async def fetch_emails(self, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent emails"""
        try:
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            emails = []
            for message in messages:
                # Get full message details
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Extract headers
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                to_email = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                # Extract body
                body = self._get_email_body(msg['payload'])
                
                emails.append({
                    'id': msg['id'],
                    'subject': subject,
                    'from': from_email,
                    'to': to_email,
                    'date': date,
                    'body': body,
                    'snippet': msg.get('snippet', '')
                })
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        
        return ""
    
    async def send_email(self, to: str, subject: str, body: str) -> str:
        """Send an email"""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"Email sent to {to}, message ID: {result['id']}")
            return result['id']
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
    
    async def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search emails with a query"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            emails = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['Subject', 'From', 'To', 'Date']
                ).execute()
                
                headers = msg['payload'].get('headers', [])
                
                emails.append({
                    'id': msg['id'],
                    'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject'),
                    'from': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                    'to': next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown'),
                    'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                    'snippet': msg.get('snippet', '')
                })
            
            return emails
            
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []

