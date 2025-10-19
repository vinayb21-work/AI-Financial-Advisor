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
            "Content-Type": "application/json",
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
                "refresh_token": self.user.hubspot_refresh_token,
            }

            response = requests.post(url, data=data)
            response.raise_for_status()

            token_data = response.json()

            # Update user tokens
            self.user.hubspot_access_token = token_data["access_token"]
            self.user.hubspot_refresh_token = token_data["refresh_token"]
            self.access_token = token_data["access_token"]

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
                "properties": "firstname,lastname,email,company,phone,notes",
            }

            response = await self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("results", [])

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
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "CONTAINS_TOKEN",
                                "value": query,
                            }
                        ]
                    }
                ],
                "properties": [
                    "firstname",
                    "lastname",
                    "email",
                    "company",
                    "phone",
                    "hs_object_id",
                ],
            }

            response = await self._make_request("POST", url, json=email_body)
            if response.status_code == 200:
                data = response.json()
                results.extend(data.get("results", []))
                if results:
                    logger.info(f"Found {len(results)} contacts by email search")
                    return results

            # Strategy 2: Search by first name OR last name
            name_body = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "firstname",
                                "operator": "CONTAINS_TOKEN",
                                "value": query,
                            }
                        ]
                    },
                    {
                        "filters": [
                            {
                                "propertyName": "lastname",
                                "operator": "CONTAINS_TOKEN",
                                "value": query,
                            }
                        ]
                    },
                ],
                "properties": [
                    "firstname",
                    "lastname",
                    "email",
                    "company",
                    "phone",
                    "hs_object_id",
                ],
            }

            response = await self._make_request("POST", url, json=name_body)
            if response.status_code == 200:
                data = response.json()
                results.extend(data.get("results", []))
                if results:
                    logger.info(f"Found {len(results)} contacts by name search")
                    return results

            # Strategy 3: Try splitting query (e.g., "Vinay B" -> search "Vinay")
            if " " in query:
                first_part = query.split()[0]
                simple_body = {
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "firstname",
                                    "operator": "CONTAINS_TOKEN",
                                    "value": first_part,
                                }
                            ]
                        }
                    ],
                    "properties": [
                        "firstname",
                        "lastname",
                        "email",
                        "company",
                        "phone",
                        "hs_object_id",
                    ],
                }

                response = await self._make_request("POST", url, json=simple_body)
                if response.status_code == 200:
                    data = response.json()
                    results.extend(data.get("results", []))
                    if results:
                        logger.info(
                            f"Found {len(results)} contacts by partial name search"
                        )
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
            if "email" in contact_data:
                properties["email"] = contact_data["email"]
            if "firstname" in contact_data:
                properties["firstname"] = contact_data["firstname"]
            if "lastname" in contact_data:
                properties["lastname"] = contact_data["lastname"]
            if "company" in contact_data:
                properties["company"] = contact_data["company"]
            if "phone" in contact_data:
                properties["phone"] = contact_data["phone"]

            body = {"properties": properties}

            logger.info(f"Creating Hubspot contact with data: {properties}")
            response = await self._make_request("POST", url, json=body)

            if response.status_code != 200 and response.status_code != 201:
                logger.error(
                    f"Hubspot API error: Status {response.status_code}, Response: {response.text}"
                )

            response.raise_for_status()

            result = response.json()
            logger.info(f"Contact created: {result['id']}")
            return result

        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Hubspot HTTP error: {e}, Response: {e.response.text if hasattr(e, 'response') else 'No response'}"
            )
            raise Exception(
                f"Hubspot API error: {e.response.status_code if hasattr(e, 'response') else 'Unknown'} - {e.response.text if hasattr(e, 'response') else str(e)}"
            )
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

            contact_id = contacts[0]["id"]

            # Create note
            url = f"{self.base_url}/crm/v3/objects/notes"

            # Hubspot expects timestamp in milliseconds since epoch
            timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

            body = {
                "properties": {
                    "hs_note_body": note,
                    "hs_timestamp": str(timestamp_ms),  # Must be string format
                },
                "associations": [
                    {
                        "to": {"id": contact_id},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": 202,  # Note to Contact association
                            }
                        ],
                    }
                ],
            }

            logger.info(f"Adding note to contact {contact_id} with body: {body}")
            response = await self._make_request("POST", url, json=body)

            logger.info(f"Hubspot response status: {response.status_code}")

            if response.status_code != 200 and response.status_code != 201:
                logger.error(
                    f"Hubspot API error: Status {response.status_code}, Response: {response.text}"
                )

            response.raise_for_status()

            result = response.json()
            logger.info(f"Note added to contact {contact_id}")
            return result

        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Hubspot HTTP error: {e}, Response: {e.response.text if hasattr(e, 'response') else 'No response'}"
            )
            raise Exception(
                f"Hubspot API error: {e.response.status_code if hasattr(e, 'response') else 'Unknown'} - {e.response.text if hasattr(e, 'response') else str(e)}"
            )
        except Exception as e:
            logger.error(f"Error adding note to Hubspot contact: {e}")
            raise

    # ==================== PHASE 1: ENGAGEMENTS (ACTIVITIES) ====================

    async def fetch_notes(
        self, contact_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch notes from Hubspot, optionally filtered by contact"""
        try:
            url = f"{self.base_url}/crm/v3/objects/notes"
            params = {
                "limit": limit,
                "properties": "hs_note_body,hs_timestamp,hs_lastmodifieddate",
            }

            response = await self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()
            notes = data.get("results", [])

            # If contact_id specified, fetch associations and filter
            if contact_id:
                filtered_notes = []
                for note in notes:
                    # Get associations for this note
                    assoc_url = f"{self.base_url}/crm/v4/objects/notes/{note['id']}/associations/contacts"
                    assoc_response = await self._make_request("GET", assoc_url)
                    if assoc_response.status_code == 200:
                        assoc_data = assoc_response.json()
                        # Check if associated with target contact
                        for result in assoc_data.get("results", []):
                            if result.get("toObjectId") == contact_id:
                                filtered_notes.append(note)
                                break
                return filtered_notes

            logger.info(f"Fetched {len(notes)} notes from Hubspot")
            return notes

        except Exception as e:
            logger.error(f"Error fetching Hubspot notes: {e}")
            return []

    async def fetch_emails(
        self, contact_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch emails from Hubspot, optionally filtered by contact"""
        try:
            url = f"{self.base_url}/crm/v3/objects/emails"
            params = {
                "limit": limit,
                "properties": "hs_email_subject,hs_email_text,hs_timestamp,hs_email_direction,hs_email_status",
            }

            response = await self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()
            emails = data.get("results", [])

            if contact_id:
                filtered_emails = []
                for email in emails:
                    assoc_url = f"{self.base_url}/crm/v4/objects/emails/{email['id']}/associations/contacts"
                    assoc_response = await self._make_request("GET", assoc_url)
                    if assoc_response.status_code == 200:
                        assoc_data = assoc_response.json()
                        for result in assoc_data.get("results", []):
                            if result.get("toObjectId") == contact_id:
                                filtered_emails.append(email)
                                break
                return filtered_emails

            logger.info(f"Fetched {len(emails)} emails from Hubspot")
            return emails

        except Exception as e:
            logger.error(f"Error fetching Hubspot emails: {e}")
            return []

    async def fetch_calls(
        self, contact_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch calls from Hubspot, optionally filtered by contact"""
        try:
            url = f"{self.base_url}/crm/v3/objects/calls"
            params = {
                "limit": limit,
                "properties": "hs_call_title,hs_call_body,hs_timestamp,hs_call_duration,hs_call_status,hs_call_direction",
            }

            response = await self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()
            calls = data.get("results", [])

            if contact_id:
                filtered_calls = []
                for call in calls:
                    assoc_url = f"{self.base_url}/crm/v4/objects/calls/{call['id']}/associations/contacts"
                    assoc_response = await self._make_request("GET", assoc_url)
                    if assoc_response.status_code == 200:
                        assoc_data = assoc_response.json()
                        for result in assoc_data.get("results", []):
                            if result.get("toObjectId") == contact_id:
                                filtered_calls.append(call)
                                break
                return filtered_calls

            logger.info(f"Fetched {len(calls)} calls from Hubspot")
            return calls

        except Exception as e:
            logger.error(f"Error fetching Hubspot calls: {e}")
            return []

    async def fetch_meetings(
        self, contact_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch meetings from Hubspot, optionally filtered by contact"""
        try:
            url = f"{self.base_url}/crm/v3/objects/meetings"
            params = {
                "limit": limit,
                "properties": "hs_meeting_title,hs_meeting_body,hs_timestamp,hs_meeting_start_time,hs_meeting_end_time,hs_meeting_outcome",
            }

            response = await self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()
            meetings = data.get("results", [])

            if contact_id:
                filtered_meetings = []
                for meeting in meetings:
                    assoc_url = f"{self.base_url}/crm/v4/objects/meetings/{meeting['id']}/associations/contacts"
                    assoc_response = await self._make_request("GET", assoc_url)
                    if assoc_response.status_code == 200:
                        assoc_data = assoc_response.json()
                        for result in assoc_data.get("results", []):
                            if result.get("toObjectId") == contact_id:
                                filtered_meetings.append(meeting)
                                break
                return filtered_meetings

            logger.info(f"Fetched {len(meetings)} meetings from Hubspot")
            return meetings

        except Exception as e:
            logger.error(f"Error fetching Hubspot meetings: {e}")
            return []

    async def fetch_tasks_hubspot(
        self, contact_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch tasks from Hubspot, optionally filtered by contact"""
        try:
            url = f"{self.base_url}/crm/v3/objects/tasks"
            params = {
                "limit": limit,
                "properties": "hs_task_subject,hs_task_body,hs_timestamp,hs_task_status,hs_task_priority,hs_task_type",
            }

            response = await self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()
            tasks = data.get("results", [])

            if contact_id:
                filtered_tasks = []
                for task in tasks:
                    assoc_url = f"{self.base_url}/crm/v4/objects/tasks/{task['id']}/associations/contacts"
                    assoc_response = await self._make_request("GET", assoc_url)
                    if assoc_response.status_code == 200:
                        assoc_data = assoc_response.json()
                        for result in assoc_data.get("results", []):
                            if result.get("toObjectId") == contact_id:
                                filtered_tasks.append(task)
                                break
                return filtered_tasks

            logger.info(f"Fetched {len(tasks)} tasks from Hubspot")
            return tasks

        except Exception as e:
            logger.error(f"Error fetching Hubspot tasks: {e}")
            return []

    async def get_contact_timeline(self, contact_email: str) -> Dict[str, Any]:
        """Get complete activity timeline for a contact (all engagements)"""
        try:
            # First find contact
            contacts = await self.search_contacts(contact_email)
            if not contacts:
                return {
                    "error": f"Contact not found: {contact_email}",
                    "notes": [],
                    "emails": [],
                    "calls": [],
                    "meetings": [],
                    "tasks": [],
                }

            contact_id = contacts[0]["id"]

            # Fetch all engagement types for this contact
            notes = await self.fetch_notes(contact_id=contact_id)
            emails = await self.fetch_emails(contact_id=contact_id)
            calls = await self.fetch_calls(contact_id=contact_id)
            meetings = await self.fetch_meetings(contact_id=contact_id)
            tasks = await self.fetch_tasks_hubspot(contact_id=contact_id)

            return {
                "contact": contacts[0],
                "notes": notes,
                "emails": emails,
                "calls": calls,
                "meetings": meetings,
                "tasks": tasks,
                "total_activities": len(notes)
                + len(emails)
                + len(calls)
                + len(meetings)
                + len(tasks),
            }

        except Exception as e:
            logger.error(f"Error fetching contact timeline: {e}")
            return {"error": str(e)}

    # ==================== PHASE 2: COMPANIES (REVENUE) ====================

    async def fetch_companies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch companies from Hubspot with revenue data"""
        try:
            url = f"{self.base_url}/crm/v3/objects/companies"
            params = {
                "limit": limit,
                "properties": "name,domain,industry,annualrevenue,numberofemployees,city,state,country,phone,type,description",
            }

            response = await self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()
            companies = data.get("results", [])

            logger.info(f"Fetched {len(companies)} companies from Hubspot")
            return companies

        except Exception as e:
            logger.error(f"Error fetching Hubspot companies: {e}")
            return []

    async def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific company"""
        try:
            url = f"{self.base_url}/crm/v3/objects/companies/{company_id}"
            params = {
                "properties": "name,domain,industry,annualrevenue,numberofemployees,city,state,country,phone,type,description,createdate,hs_lastmodifieddate"
            }

            response = await self._make_request("GET", url, params=params)
            response.raise_for_status()

            company = response.json()
            logger.info(f"Fetched company {company_id}")
            return company

        except Exception as e:
            logger.error(f"Error fetching company {company_id}: {e}")
            return None

    async def search_companies(self, query: str) -> List[Dict[str, Any]]:
        """Search companies by name or domain"""
        try:
            url = f"{self.base_url}/crm/v3/objects/companies/search"

            # Search by name or domain
            body = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "name",
                                "operator": "CONTAINS_TOKEN",
                                "value": query,
                            }
                        ]
                    },
                    {
                        "filters": [
                            {
                                "propertyName": "domain",
                                "operator": "CONTAINS_TOKEN",
                                "value": query,
                            }
                        ]
                    },
                ],
                "properties": [
                    "name",
                    "domain",
                    "industry",
                    "annualrevenue",
                    "numberofemployees",
                    "city",
                    "state",
                    "hs_object_id",
                ],
            }

            response = await self._make_request("POST", url, json=body)
            response.raise_for_status()

            data = response.json()
            companies = data.get("results", [])

            logger.info(f"Found {len(companies)} companies for query: {query}")
            return companies

        except Exception as e:
            logger.error(f"Error searching Hubspot companies: {e}")
            return []

    async def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company in Hubspot"""
        try:
            url = f"{self.base_url}/crm/v3/objects/companies"

            properties = {}
            allowed_props = [
                "name",
                "domain",
                "industry",
                "annualrevenue",
                "numberofemployees",
                "city",
                "state",
                "country",
                "phone",
                "type",
                "description",
            ]

            for prop in allowed_props:
                if prop in company_data:
                    properties[prop] = company_data[prop]

            body = {"properties": properties}

            logger.info(f"Creating Hubspot company with data: {properties}")
            response = await self._make_request("POST", url, json=body)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Company created: {result['id']}")
            return result

        except Exception as e:
            logger.error(f"Error creating Hubspot company: {e}")
            raise

    async def update_company(
        self, company_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing company in Hubspot"""
        try:
            url = f"{self.base_url}/crm/v3/objects/companies/{company_id}"
            body = {"properties": properties}

            logger.info(f"Updating company {company_id} with: {properties}")
            response = await self._make_request("PATCH", url, json=body)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Company {company_id} updated")
            return result

        except Exception as e:
            logger.error(f"Error updating company {company_id}: {e}")
            raise

    async def get_company_contacts(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all contacts associated with a company"""
        try:
            url = f"{self.base_url}/crm/v4/objects/companies/{company_id}/associations/contacts"

            response = await self._make_request("GET", url)
            response.raise_for_status()

            data = response.json()
            contact_ids = [result["toObjectId"] for result in data.get("results", [])]

            # Fetch full contact details
            contacts = []
            for contact_id in contact_ids:
                contact_url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
                params = {"properties": "firstname,lastname,email,phone,jobtitle"}
                contact_response = await self._make_request(
                    "GET", contact_url, params=params
                )
                if contact_response.status_code == 200:
                    contacts.append(contact_response.json())

            logger.info(f"Fetched {len(contacts)} contacts for company {company_id}")
            return contacts

        except Exception as e:
            logger.error(f"Error fetching contacts for company {company_id}: {e}")
            return []

    async def update_contact(
        self, contact_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing contact in Hubspot"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
            body = {"properties": properties}

            logger.info(f"Updating contact {contact_id} with: {properties}")
            response = await self._make_request("PATCH", url, json=body)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Contact {contact_id} updated")
            return result

        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            raise
