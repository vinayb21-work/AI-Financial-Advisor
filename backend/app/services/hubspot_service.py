import requests
from typing import List, Dict, Any
import logging

from app.models.user import User

logger = logging.getLogger(__name__)

class HubspotService:
    """Hubspot CRM API service"""
    
    def __init__(self, user: User):
        self.user = user
        self.access_token = user.hubspot_access_token
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def fetch_contacts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch Hubspot contacts"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts"
            params = {
                "limit": limit,
                "properties": "firstname,lastname,email,company,phone,notes"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            logger.error(f"Error fetching Hubspot contacts: {e}")
            return []
    
    async def search_contacts(self, query: str) -> List[Dict[str, Any]]:
        """Search Hubspot contacts"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts/search"
            
            body = {
                "filterGroups": [{
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "CONTAINS_TOKEN",
                            "value": query
                        }
                    ]
                }],
                "properties": ["firstname", "lastname", "email", "company", "phone"]
            }
            
            # Also search by name
            name_body = {
                "filterGroups": [{
                    "filters": [
                        {
                            "propertyName": "firstname",
                            "operator": "CONTAINS_TOKEN",
                            "value": query
                        }
                    ]
                }, {
                    "filters": [
                        {
                            "propertyName": "lastname",
                            "operator": "CONTAINS_TOKEN",
                            "value": query
                        }
                    ]
                }],
                "properties": ["firstname", "lastname", "email", "company", "phone"]
            }
            
            # Try email search first
            response = requests.post(url, headers=self.headers, json=body)
            
            if response.status_code != 200:
                # Try name search
                response = requests.post(url, headers=self.headers, json=name_body)
            
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
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
            
            response = requests.post(url, headers=self.headers, json=body)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Contact created: {result['id']}")
            return result
            
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
            
            body = {
                "properties": {
                    "hs_note_body": note,
                    "hs_timestamp": datetime.utcnow().isoformat()
                },
                "associations": [{
                    "to": {"id": contact_id},
                    "types": [{
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 202  # Note to Contact association
                    }]
                }]
            }
            
            response = requests.post(url, headers=self.headers, json=body)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Note added to contact {contact_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error adding note to Hubspot contact: {e}")
            raise

from datetime import datetime

