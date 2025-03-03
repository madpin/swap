import asyncio
import datetime
import logging

from googleapiclient.errors import HttpError

# Assuming GoogleCalendarService class is defined in a file named 'google_calendar_service.py'
from swap.services.google_calendar import (
    GoogleCalendarService,
    CalendarCreationError,
    CalendarSharingError,
    EventCreationError,
    EventDeletionError,
)

# from app.services.google_calendar

# Path to your Google Cloud service account key file
SERVICE_ACCOUNT_FILE = "./gcal_service_account.json"

# Email to share the calendar with
SHARE_EMAIL = "madpin@gmail.com"

# Timezone for the event (you can change this)
EVENT_TIMEZONE = "America/Sao_Paulo"


async def main():
    """
    Creates a new calendar, shares it, creates an event, waits for confirmation, and deletes the event.
    """
    try:
        # Initialize the Google Calendar service
        calendar_service = GoogleCalendarService(
            service_account_file=SERVICE_ACCOUNT_FILE, calendar_id=None
        )

        # 1. Create a new calendar
        try:
            new_calendar = await calendar_service.create_calendar(
                summary="SWAP Test Calendar",
                description="Calendar for testing SWAP application",
                timezone=EVENT_TIMEZONE,
            )
            new_calendar_id = new_calendar["id"]()
            logging.info(f"New calendar created with ID: {new_calendar_id}")
        except CalendarCreationError as e:
            logging.error(f"Failed to create calendar: {e}")
            return  # Stop if calendar creation fails
        except HttpError as e:
            logging.exception(f"HTTP error occurred while creating calendar: {e}")
            return
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return

        # 2. Share the calendar
        try:
            await calendar_service.share_calendar(
                calendar_id=new_calendar_id, email=SHARE_EMAIL, role="writer"
            )
            logging.info(f"Calendar shared with {SHARE_EMAIL}")
        except CalendarSharingError as e:
            logging.error(f"Failed to share calendar: {e}")
        except HttpError as e:
            logging.exception(f"HTTP error occurred while sharing calendar: {e}")
            return
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return

        # 3. Create an event
        try:
            start_time = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(minutes=10)
            end_time = start_time + datetime.timedelta(minutes=45)
            created_event = await calendar_service.create_event(
                calendar_id=new_calendar_id,
                summary="SWAP Test Event",
                description="Test event for SWAP application",
                start_time=start_time,
                end_time=end_time,
                timezone=EVENT_TIMEZONE,
            )
            logging.info(f"Event created: {created_event.get('htmlLink')}")
            event_id = created_event["id"]
        except EventCreationError as e:
            logging.error(f"Failed to create event: {e}")
        except HttpError as e:
            logging.exception(f"HTTP error occurred while creating event: {e}")
            return
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return

        # 4. Wait for user confirmation
        input("Press Enter to delete the event...")

        # 5. Delete the event
        try:
            await calendar_service.delete_event(
                calendar_id=new_calendar_id, event_id=event_id
            )
            logging.info(f"Event deleted: {event_id}")
        except EventDeletionError as e:
            logging.error(f"Failed to delete event: {e}")
        except HttpError as e:
            logging.exception(f"HTTP error occurred while deleting event: {e}")
            return
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return
        # 6. Delete the calendar
        try:
            await calendar_service.delete_calendar(
                calendar_id=new_calendar_id,
            )
            logging.info(f"Calendar deleted: {new_calendar_id}")
        except CalendarCreationError as e:
            logging.error(f"Failed to delete calendar: {e}")
        except HttpError as e:
            logging.exception(f"HTTP error occurred while deleting calendar: {e}")
            return
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return

    except Exception as e:
        logging.exception(f"An unexpected error occurred during script execution: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
