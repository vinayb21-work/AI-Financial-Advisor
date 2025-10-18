import requests
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

class HubspotService:
    """Hubspot CRM API service"""
    
    def __init__(self, user: User, db_session: Optional[Any] = None):
        self.user = user
        self.db = db_session
        self.access_token = user.hubspot_access_token
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def refresh_token(self) -> bool:
        """Refresh Hubspot access token"""
        try:
            if not self.user.hubspot_refresh_token:
                logger.error("No refresh token available")
                return False
            
            url = "https://api.hubapi.com/oauth/v1/token"
            data = {
                "grant_type": "refresh_token",
                "client_id": settings.HUBSPOT_CLIENT_ID,
                "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                "refresh_token": self.user.hubspot_refresh_token
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Update user tokens
            self.user.hubspot_access_token = token_data['access_token']
            self.user.hubspot_refresh_token = token_data['refresh_token']
            self.access_token = token_data['access_token']
            
            # Update headers
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            
            # Save to database if session provided
            if self.db:
                await self.db.commit()
            
            logger.info("Hubspot token refreshed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing Hubspot token: {e}")
            return False
    
    async def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with automatic token refresh on 401"""
        response = requests.request(method, url, headers=self.headers, **kwargs)
        
        # If unauthorized, try refreshing token
        if response.status_code == 401:
            logger.info("Got 401, attempting to refresh Hubspot token")
            if await self.refresh_token():
                # Retry request with new token
                response = requests.request(method, url, headers=self.headers, **kwargs)
        
        return response
    
    async def fetch_contacts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch Hubspot contacts"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts"
            params = {
                "limit": limit,
                "properties": "firstname,lastname,email,company,phone,notes"
            }
            
            response = await self._make_request('GET', url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            logger.error(f"Error fetching Hubspot contacts: {e}")
            return []
    
    async def search_contacts(self, query: str) -> List[Dict[str, Any]]:
        """Search Hubspot contacts - tries multiple search strategies"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts/search"
            results = []
            
            # Strategy 1: Search by email (most accurate)
            email_body = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "email",
                        "operator": "CONTAINS_TOKEN",
                        "value": query
                    }]
                }],
                "properties": ["firstname", "lastname", "email", "company", "phone", "hs_object_id"]
            }
            
            response = await self._make_request('POST', url, json=email_body)
            if response.status_code == 200:
                data = response.json()
                results.extend(data.get('results', []))
                if results:
                    logger.info(f"Found {len(results)} contacts by email search")
                    return results
            
            # Strategy 2: Search by first name OR last name
            name_body = {
                "filterGroups": [
                    {
                        "filters": [{
                            "propertyName": "firstname",
                            "operator": "CONTAINS_TOKEN",
                            "value": query
                        }]
                    },
                    {
                        "filters": [{
                            "propertyName": "lastname",
                            "operator": "CONTAINS_TOKEN",
                            "value": query
                        }]
                    }
                ],
                "properties": ["firstname", "lastname", "email", "company", "phone", "hs_object_id"]
            }
            
            response = await self._make_request('POST', url, json=name_body)
            if response.status_code == 200:
                data = response.json()
                results.extend(data.get('results', []))
                if results:
                    logger.info(f"Found {len(results)} contacts by name search")
                    return results
            
            # Strategy 3: Try splitting query (e.g., "Vinay B" -> search "Vinay")
            if ' ' in query:
                first_part = query.split()[0]
                simple_body = {
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "firstname",
                            "operator": "CONTAINS_TOKEN",
                            "value": first_part
                        }]
                    }],
                    "properties": ["firstname", "lastname", "email", "company", "phone", "hs_object_id"]
                }
                
                response = await self._make_request('POST', url, json=simple_body)
                if response.status_code == 200:
                    data = response.json()
                    results.extend(data.get('results', []))
                    if results:
                        logger.info(f"Found {len(results)} contacts by partial name search")
                        return results
            
            logger.warning(f"No contacts found for query: {query}")
            return []
            
        except Exception as e:
            logger.error(f"Error searching Hubspot contacts: {e}")
            return []
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Hubspot contact"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts"
            
            properties = {}
            if 'email' in contact_data:
                properties['email'] = contact_data['email']
            if 'firstname' in contact_data:
                properties['firstname'] = contact_data['firstname']
            if 'lastname' in contact_data:
                properties['lastname'] = contact_data['lastname']
            if 'company' in contact_data:
                properties['company'] = contact_data['company']
            if 'phone' in contact_data:
                properties['phone'] = contact_data['phone']
            
            body = {"properties": properties}
            
            logger.info(f"Creating Hubspot contact with data: {properties}")
            response = await self._make_request('POST', url, json=body)
            
            if response.status_code != 200 and response.status_code != 201:
                logger.error(f"Hubspot API error: Status {response.status_code}, Response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Contact created: {result['id']}")
            return result
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Hubspot HTTP error: {e}, Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            raise Exception(f"Hubspot API error: {e.response.status_code if hasattr(e, 'response') else 'Unknown'} - {e.response.text if hasattr(e, 'response') else str(e)}")
        except Exception as e:
            logger.error(f"Error creating Hubspot contact: {e}")
            raise
    
    async def add_note(self, contact_email: str, note: str) -> Dict[str, Any]:
        """Add a note to a Hubspot contact"""
        try:
            # First, find the contact by email
            contacts = await self.search_contacts(contact_email)
            
            if not contacts:
                raise ValueError(f"Contact not found: {contact_email}")
            
            contact_id = contacts[0]['id']
            
            # Create note
            url = f"{self.base_url}/crm/v3/objects/notes"
            
            # Hubspot expects timestamp in milliseconds since epoch
            timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
            
            body = {
                "properties": {
                    "hs_note_body": note,
                    "hs_timestamp": str(timestamp_ms)  # Must be string format
                },
                "associations": [{
                    "to": {"id": contact_id},
                    "types": [{
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 202  # Note to Contact association
                    }]
                }]
            }
            
            logger.info(f"Adding note to contact {contact_id} with body: {body}")
            response = await self._make_request('POST', url, json=body)
            
            logger.info(f"Hubspot response status: {response.status_code}")
            
            if response.status_code != 200 and response.status_code != 201:
                logger.error(f"Hubspot API error: Status {response.status_code}, Response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Note added to contact {contact_id}")
            return result
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Hubspot HTTP error: {e}, Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            raise Exception(f"Hubspot API error: {e.response.status_code if hasattr(e, 'response') else 'Unknown'} - {e.response.text if hasattr(e, 'response') else str(e)}")
        except Exception as e:
            logger.error(f"Error adding note to Hubspot contact: {e}")
            raise

