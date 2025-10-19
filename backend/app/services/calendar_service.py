from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
import logging

from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class CalendarService:
    """Google Calendar API service"""

    def __init__(self, user: User):
        self.user = user
        self.credentials = Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        self.service = build("calendar", "v3", credentials=self.credentials)

    async def fetch_events(self, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent calendar events"""
        try:
            # Get events from the past 30 days and next 90 days
            time_min = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
            time_max = (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z"

            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])

            formatted_events = []
            for event in events:
                formatted_events.append(
                    {
                        "id": event["id"],
                        "summary": event.get("summary", "Untitled"),
                        "description": event.get("description", ""),
                        "start": event["start"].get(
                            "dateTime", event["start"].get("date")
                        ),
                        "end": event["end"].get("dateTime", event["end"].get("date")),
                        "attendees": event.get("attendees", []),
                        "location": event.get("location", ""),
                        "status": event.get("status", ""),
                    }
                )

            return formatted_events

        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}")
            return []

    async def get_availability(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, str]]:
        """Get available time slots"""
        try:
            # Convert dates to datetime (always timezone-aware UTC)
            # Handle both date-only (YYYY-MM-DD) and full datetime strings
            if "T" not in start_date:
                # Date only - set to start of day in UTC
                start = datetime.fromisoformat(start_date).replace(
                    hour=0, minute=0, second=0, tzinfo=timezone.utc
                )
            else:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

            if "T" not in end_date:
                # Date only - set to end of day in UTC
                end = datetime.fromisoformat(end_date).replace(
                    hour=23, minute=59, second=59, tzinfo=timezone.utc
                )
            else:
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            # Ensure end is after start
            if end <= start:
                end = start + timedelta(days=1)

            logger.info(
                f"Checking availability from {start.isoformat()} to {end.isoformat()}"
            )

            # Get busy times
            # Remove timezone info and add 'Z' for UTC (Google Calendar API expects this format)
            body = {
                "timeMin": start.replace(tzinfo=None).isoformat() + "Z",
                "timeMax": end.replace(tzinfo=None).isoformat() + "Z",
                "items": [{"id": "primary"}],
            }

            freebusy = self.service.freebusy().query(body=body).execute()
            busy_times = freebusy["calendars"]["primary"].get("busy", [])

            # Generate available slots (9 AM to 5 PM, excluding busy times)
            available_slots = []
            current_date = start.replace(hour=0, minute=0, second=0, microsecond=0)

            while current_date < end:
                # Check each hour from 9 AM to 5 PM
                for hour in range(9, 17):
                    # Ensure slot times are timezone-aware
                    slot_start = current_date.replace(
                        hour=hour, minute=0, second=0, microsecond=0
                    )
                    slot_end = slot_start + timedelta(hours=1)

                    # Skip if slot is in the past
                    if slot_end < start:
                        continue

                    # Check if slot is busy
                    is_busy = False
                    for busy in busy_times:
                        busy_start = datetime.fromisoformat(
                            busy["start"].replace("Z", "+00:00")
                        )
                        busy_end = datetime.fromisoformat(
                            busy["end"].replace("Z", "+00:00")
                        )

                        if slot_start < busy_end and slot_end > busy_start:
                            is_busy = True
                            break

                    if not is_busy:
                        available_slots.append(
                            {
                                "start": slot_start.isoformat(),
                                "end": slot_end.isoformat(),
                            }
                        )

                current_date += timedelta(days=1)

            return available_slots[:10]  # Return first 10 available slots

        except Exception as e:
            logger.error(f"Error getting availability: {e}")
            return []

    async def list_events(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """List calendar events for a specific date range"""
        try:
            # Convert dates to datetime (always timezone-aware UTC)
            if "T" not in start_date:
                # Date only - set to start of day in UTC
                start = datetime.fromisoformat(start_date).replace(
                    hour=0, minute=0, second=0, tzinfo=timezone.utc
                )
            else:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

            if "T" not in end_date:
                # Date only - set to end of day in UTC
                end = datetime.fromisoformat(end_date).replace(
                    hour=23, minute=59, second=59, tzinfo=timezone.utc
                )
            else:
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            logger.info(f"Listing events from {start.isoformat()} to {end.isoformat()}")

            # Fetch events from Google Calendar
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=start.replace(tzinfo=None).isoformat() + "Z",
                    timeMax=end.replace(tzinfo=None).isoformat() + "Z",
                    maxResults=100,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            logger.info(f"Found {len(events)} events in the specified date range")

            formatted_events = []
            for event in events:
                # Parse start and end times
                start_dt = event["start"].get("dateTime", event["start"].get("date"))
                end_dt = event["end"].get("dateTime", event["end"].get("date"))

                # Format attendees
                attendees = []
                for attendee in event.get("attendees", []):
                    attendees.append(attendee.get("email", ""))

                formatted_events.append(
                    {
                        "id": event["id"],
                        "title": event.get("summary", "Untitled"),
                        "description": event.get("description", ""),
                        "start": start_dt,
                        "end": end_dt,
                        "attendees": attendees,
                        "location": event.get("location", ""),
                    }
                )

            return formatted_events

        except Exception as e:
            logger.error(f"Error listing calendar events: {e}")
            return []

    async def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        attendees: List[str] = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """Create a calendar event"""
        try:
            event = {
                "summary": title,
                "description": description,
                "start": {
                    "dateTime": start_time,
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": "UTC",
                },
            }

            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            created_event = (
                self.service.events()
                .insert(calendarId="primary", body=event, sendUpdates="all")
                .execute()
            )

            logger.info(f"Event created: {created_event['id']}")
            return created_event

        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise
