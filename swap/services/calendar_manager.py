from typing import Optional
from datetime import datetime
from swap.models.calendar import Calendar
from swap.core.database import get_db
from swap.utils.logger import logger
from swap.services.google_calendar import GoogleCalendarService

class CalendarManager:
    def __init__(self, service_account_file: str):
        self.service_account_file = service_account_file
        self.google_calendar = GoogleCalendarService(service_account_file)
    
    async def get_or_create_calendar(self, name: str, owner_email: str) -> Calendar:
        """
        Get an existing calendar or create a new one based on name and owner.
        
        Args:
            name: Calendar name (from spreadsheet)
            owner_email: Email of the calendar owner
            
        Returns:
            Calendar object
        """
        with get_db() as session:
            # Try to find existing calendar
            calendar = session.query(Calendar).filter(
                Calendar.name == name,
                Calendar.main_email == owner_email
            ).first()
            
            if calendar:
                return calendar
                
            # Create new calendar in Google
            gcal = await self.google_calendar.create_calendar(
                summary=name,
                description=f"Calendar for {name}",
                timezone="UTC"  # TODO: Make configurable
            )
            
            # Create calendar in our database
            calendar = Calendar(
                google_calendar_id=gcal["id"],
                name=name,
                key=f"{name.lower().replace(' ', '-')}-{datetime.utcnow().year}",
                main_email=owner_email,
                is_active=True
            )
            
            session.add(calendar)
            session.commit()
            
            # Share calendar with owner
            await self.google_calendar.share_calendar(
                email=owner_email,
                calendar_id=gcal["id"],
                role="owner"
            )
            
            logger.info(f"Created new calendar: {name} for {owner_email}")
            return calendar
    
    async def update_calendar_access(self, calendar: Calendar, new_emails: list[str]):
        """
        Update calendar access permissions.
        
        Args:
            calendar: Calendar object
            new_emails: List of email addresses that should have access
        """
        try:
            # Get current access list
            current_users = await self.google_calendar.list_shared_users(calendar.google_calendar_id)
            current_emails = {rule["scope"]["value"] for rule in current_users if "scope" in rule}
            
            # Add new users
            for email in new_emails:
                if email not in current_emails and email != calendar.main_email:
                    await self.google_calendar.share_calendar(
                        email=email,
                        calendar_id=calendar.google_calendar_id,
                        role="writer"
                    )
                    logger.info(f"Granted access to {email} for calendar {calendar.name}")
            
            # Remove users who should no longer have access
            for email in current_emails:
                if email not in new_emails and email != calendar.main_email:
                    await self.google_calendar.remove_calendar_access(
                        email=email,
                        calendar_id=calendar.google_calendar_id
                    )
                    logger.info(f"Removed access for {email} from calendar {calendar.name}")
                    
        except Exception as e:
            logger.error(f"Error updating calendar access: {e}")
            raise
