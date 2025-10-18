from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import logging
from datetime import datetime

from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.instruction import OngoingInstruction
from app.services.gmail_service import GmailService
from app.services.calendar_service import CalendarService
from app.services.hubspot_service import HubspotService

logger = logging.getLogger(__name__)

class ToolExecutor:
    """Execute tools called by the AI agent"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.gmail_service = GmailService(user)
        self.calendar_service = CalendarService(user)
        self.hubspot_service = HubspotService(user, db)
    
    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """Get OpenAI function calling tools definition"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send an email to a recipient",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Email address of recipient"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body content"
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_emails",
                    "description": "Search through emails for specific content or sender",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (e.g., 'from:john@example.com', 'subject:meeting')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_calendar_availability",
                    "description": "Get available time slots from calendar",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in ISO format (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in ISO format (YYYY-MM-DD)"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_calendar_event",
                    "description": "Create a new calendar event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Event title"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Start time in ISO format"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "End time in ISO format"
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of attendee email addresses"
                            },
                            "description": {
                                "type": "string",
                                "description": "Event description"
                            }
                        },
                        "required": ["title", "start_time", "end_time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_hubspot_contacts",
                    "description": "Search for contacts in Hubspot CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (name, email, company)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_all_hubspot_contacts",
                    "description": "List ALL contacts in Hubspot CRM. Use this when user asks for 'all clients', 'all contacts', or 'what clients are in hubspot'. Returns complete list of all contacts.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of contacts to return",
                                "default": 100
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_hubspot_contact",
                    "description": "Create a new contact in Hubspot CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Contact email address"
                            },
                            "firstname": {
                                "type": "string",
                                "description": "First name"
                            },
                            "lastname": {
                                "type": "string",
                                "description": "Last name"
                            },
                            "company": {
                                "type": "string",
                                "description": "Company name"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Phone number"
                            }
                        },
                        "required": ["email"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_hubspot_note",
                    "description": "Add a note to a Hubspot contact",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contact_email": {
                                "type": "string",
                                "description": "Contact email address"
                            },
                            "note": {
                                "type": "string",
                                "description": "Note content"
                            }
                        },
                        "required": ["contact_email", "note"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a task that needs to be completed over time",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Task description"
                            },
                            "context": {
                                "type": "object",
                                "description": "Context needed to complete the task"
                            },
                            "waiting_for": {
                                "type": "string",
                                "description": "What the task is waiting for (e.g., 'email response')"
                            }
                        },
                        "required": ["description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_ongoing_instruction",
                    "description": "Save an ongoing instruction that should be applied to future events",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "instruction": {
                                "type": "string",
                                "description": "The instruction to remember"
                            },
                            "trigger_type": {
                                "type": "string",
                                "enum": ["gmail", "calendar", "hubspot"],
                                "description": "What type of event should trigger this instruction"
                            }
                        },
                        "required": ["instruction", "trigger_type"]
                    }
                }
            }
        ]
    
    async def execute(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function"""
        try:
            if function_name == "send_email":
                return await self._send_email(args)
            elif function_name == "search_emails":
                return await self._search_emails(args)
            elif function_name == "get_calendar_availability":
                return await self._get_calendar_availability(args)
            elif function_name == "create_calendar_event":
                return await self._create_calendar_event(args)
            elif function_name == "search_hubspot_contacts":
                return await self._search_hubspot_contacts(args)
            elif function_name == "list_all_hubspot_contacts":
                return await self._list_all_hubspot_contacts(args)
            elif function_name == "create_hubspot_contact":
                return await self._create_hubspot_contact(args)
            elif function_name == "add_hubspot_note":
                return await self._add_hubspot_note(args)
            elif function_name == "create_task":
                return await self._create_task(args)
            elif function_name == "save_ongoing_instruction":
                return await self._save_ongoing_instruction(args)
            else:
                return {"error": f"Unknown function: {function_name}"}
        except Exception as e:
            logger.error(f"Error executing {function_name}: {e}")
            return {"error": str(e)}
    
    async def _send_email(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email"""
        logger.info(f"[SEND_EMAIL] Attempting to send email to: {args.get('to')}")
        logger.info(f"[SEND_EMAIL] Subject: {args.get('subject')}")
        logger.info(f"[SEND_EMAIL] Body preview: {args.get('body', '')[:100]}...")
        
        result = await self.gmail_service.send_email(
            to=args["to"],
            subject=args["subject"],
            body=args["body"]
        )
        
        logger.info(f"[SEND_EMAIL] ✅ SUCCESS - Email sent to {args['to']}, message_id: {result}")
        return {"status": "sent", "message_id": result, "sent_to": args["to"]}
    
    async def _search_emails(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search emails"""
        emails = await self.gmail_service.search_emails(
            query=args["query"],
            max_results=args.get("max_results", 10)
        )
        return {"emails": emails}
    
    async def _get_calendar_availability(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get calendar availability"""
        availability = await self.calendar_service.get_availability(
            start_date=args["start_date"],
            end_date=args["end_date"]
        )
        return {"availability": availability}
    
    async def _create_calendar_event(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create calendar event"""
        event = await self.calendar_service.create_event(
            title=args["title"],
            start_time=args["start_time"],
            end_time=args["end_time"],
            attendees=args.get("attendees", []),
            description=args.get("description", "")
        )
        return {"status": "created", "event_id": event["id"]}
    
    async def _search_hubspot_contacts(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search Hubspot contacts"""
        contacts = await self.hubspot_service.search_contacts(args["query"])
        return {"contacts": contacts}
    
    async def _list_all_hubspot_contacts(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all Hubspot contacts"""
        limit = args.get("limit", 100)
        contacts = await self.hubspot_service.fetch_contacts(limit=limit)
        return {
            "contacts": contacts,
            "total": len(contacts),
            "message": f"Found {len(contacts)} total contacts in Hubspot"
        }
    
    async def _create_hubspot_contact(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create Hubspot contact"""
        contact = await self.hubspot_service.create_contact(args)
        return {"status": "created", "contact_id": contact["id"]}
    
    async def _add_hubspot_note(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add note to Hubspot contact"""
        note = await self.hubspot_service.add_note(
            contact_email=args["contact_email"],
            note=args["note"]
        )
        return {"status": "added", "note_id": note["id"]}
    
    async def _create_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task"""
        task = Task(
            user_id=self.user.id,
            description=args["description"],
            context=args.get("context"),
            waiting_for=args.get("waiting_for"),
            status=TaskStatus.PENDING
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        return {"status": "created", "task_id": str(task.id)}
    
    async def _save_ongoing_instruction(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Save an ongoing instruction"""
        instruction = OngoingInstruction(
            user_id=self.user.id,
            instruction=args["instruction"],
            trigger_type=args["trigger_type"],
            active=True
        )
        self.db.add(instruction)
        await self.db.commit()
        await self.db.refresh(instruction)
        
        return {"status": "saved", "instruction_id": str(instruction.id)}

