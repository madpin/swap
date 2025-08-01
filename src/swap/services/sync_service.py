"""Main synchronization service coordinating all components."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .sheets_service import SheetsService
from .calendar_service import CalendarService
from .rota_parser import RotaParser
from ..data.repositories import UserRepository, ShiftRepository, SyncHistoryRepository
from ..config.settings import Settings, UserConfig
from ..config.logging import get_logger

logger = get_logger(__name__)


class SyncService:
    """Main service for orchestrating rota to calendar synchronization."""
    
    def __init__(
        self,
        settings: Settings,
        db: Session,
        sheets_service: SheetsService,
        calendar_service: CalendarService,
    ):
        """Initialize sync service with dependencies."""
        self.settings = settings
        self.db = db
        self.sheets_service = sheets_service
        self.calendar_service = calendar_service
        self.rota_parser = RotaParser(sheets_service)
        
        # Initialize repositories
        self.user_repo = UserRepository(db)
        self.shift_repo = ShiftRepository(db)
        self.sync_history_repo = SyncHistoryRepository(db)
    
    def sync_all_users(self) -> Dict[str, Any]:
        """Sync rota data for all configured users."""
        logger.info("Starting full synchronization for all users")
        
        overall_stats = {
            "users_processed": 0,
            "total_shifts_processed": 0,
            "total_events_created": 0,
            "total_events_updated": 0,
            "total_events_deleted": 0,
            "errors": [],
        }
        
        try:
            # Parse rota data once for all users
            shifts_data = self.rota_parser.parse_rota(
                self.settings.google.spreadsheet_id,
                self.settings.google.range_name
            )
            
            # Process each user
            for user_config in self.settings.users:
                try:
                    user_stats = self.sync_user(user_config, shifts_data)
                    overall_stats["users_processed"] += 1
                    overall_stats["total_shifts_processed"] += user_stats["shifts_processed"]
                    overall_stats["total_events_created"] += user_stats["events_created"]
                    overall_stats["total_events_updated"] += user_stats["events_updated"]
                    overall_stats["total_events_deleted"] += user_stats["events_deleted"]
                except Exception as e:
                    error_msg = f"Failed to sync user {user_config.user_name}: {e}"
                    logger.error(error_msg)
                    overall_stats["errors"].append(error_msg)
            
            # Record overall sync history
            self.sync_history_repo.create(
                user_id=None,
                total_shifts_processed=overall_stats["total_shifts_processed"],
                events_created=overall_stats["total_events_created"],
                events_updated=overall_stats["total_events_updated"],
                events_deleted=overall_stats["total_events_deleted"],
                status="success" if not overall_stats["errors"] else "partial",
                error_message="; ".join(overall_stats["errors"]) if overall_stats["errors"] else None,
            )
            
            logger.info(f"Synchronization completed. Processed {overall_stats['users_processed']} users")
            return overall_stats
            
        except Exception as e:
            error_msg = f"Critical error during synchronization: {e}"
            logger.error(error_msg, exc_info=True)
            overall_stats["errors"].append(error_msg)
            
            # Record failed sync
            self.sync_history_repo.create(
                user_id=None,
                total_shifts_processed=0,
                status="error",
                error_message=error_msg,
            )
            
            raise
    
    def sync_user(self, user_config: UserConfig, shifts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync rota data for a specific user."""
        logger.info(f"Syncing user: {user_config.user_name}")
        
        stats = {
            "shifts_processed": 0,
            "shifts_created": 0,
            "shifts_updated": 0,
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0,
        }
        
        try:
            # Get or create user in database
            user = self._get_or_create_user(user_config)
            
            # Setup calendar
            calendar_id = self._setup_calendar(user, user_config)
            
            # Filter shifts for this user
            user_shifts = [
                shift for shift in shifts_data 
                if shift["name"] == user_config.user_name
            ]
            
            logger.info(f"Found {len(user_shifts)} shifts for {user_config.user_name}")
            stats["shifts_processed"] = len(user_shifts)
            
            # Process shifts and sync to calendar
            for shift_data in user_shifts:
                try:
                    shift, is_new = self.shift_repo.create_or_update(user.id, shift_data)
                    
                    if is_new:
                        stats["shifts_created"] += 1
                    else:
                        stats["shifts_updated"] += 1
                    
                    # Sync to calendar
                    event_stats = self._sync_shift_to_calendar(shift, calendar_id)
                    stats["events_created"] += event_stats.get("created", 0)
                    stats["events_updated"] += event_stats.get("updated", 0)
                    stats["events_deleted"] += event_stats.get("deleted", 0)
                    
                except Exception as e:
                    logger.warning(f"Failed to process shift {shift_data}: {e}")
                    continue
            
            # Record user sync history
            self.sync_history_repo.create(
                user_id=user.id,
                total_shifts_processed=stats["shifts_processed"],
                shifts_created=stats["shifts_created"],
                shifts_updated=stats["shifts_updated"],
                events_created=stats["events_created"],
                events_updated=stats["events_updated"],
                events_deleted=stats["events_deleted"],
                status="success",
            )
            
            logger.info(f"User sync completed: {user_config.user_name}")
            return stats
            
        except Exception as e:
            # Record failed user sync
            self.sync_history_repo.create(
                user_id=user.id if 'user' in locals() else None,
                total_shifts_processed=stats["shifts_processed"],
                status="error",
                error_message=str(e),
            )
            raise
    
    def _get_or_create_user(self, user_config: UserConfig):
        """Get existing user or create new one."""
        user = self.user_repo.get_by_user_name(user_config.user_name)
        
        if not user:
            logger.info(f"Creating new user: {user_config.user_name}")
            user = self.user_repo.create(
                user_name=user_config.user_name,
                calendar_name=user_config.calendar_name,
                emails_to_share=user_config.emails_to_share,
            )
        
        return user
    
    def _setup_calendar(self, user, user_config: UserConfig) -> str:
        """Setup Google Calendar for user."""
        # Get or create calendar
        calendar_id = self.calendar_service.get_or_create_calendar(user_config.calendar_name)
        
        # Update user's calendar ID if needed
        if user.calendar_id != calendar_id:
            self.user_repo.update_calendar_id(user.id, calendar_id)
        
        # Ensure calendar is shared with configured emails
        self.calendar_service.ensure_calendar_shared(calendar_id, user_config.emails_to_share)
        
        return calendar_id
    
    def _sync_shift_to_calendar(self, shift, calendar_id: str) -> Dict[str, int]:
        """Sync a single shift to calendar."""
        stats = {"created": 0, "updated": 0, "deleted": 0}
        
        try:
            shift_date = datetime.strptime(shift.date, "%Y-%m-%d")
            existing_events = self.calendar_service.get_events_for_date(calendar_id, shift_date)
            
            # Generate event details
            event_details = self._generate_event_details(shift)
            
            # Check if we need to create/update event
            if shift.is_working or shift.shift_type in ["training"]:
                event_id = self._create_or_update_event(
                    calendar_id, shift, event_details, existing_events
                )
                if event_id:
                    if not shift.calendar_event_id:
                        stats["created"] = 1
                        self.shift_repo.update_calendar_event_id(shift.id, event_id)
                    else:
                        stats["updated"] = 1
            else:
                # Non-working day - create all-day event if not exists
                event_id = self._create_or_update_allday_event(
                    calendar_id, shift, event_details, existing_events
                )
                if event_id and not shift.calendar_event_id:
                    stats["created"] = 1
                    self.shift_repo.update_calendar_event_id(shift.id, event_id)
            
            # Clean up old events if necessary
            if len(existing_events) > 1:
                for event in existing_events[1:]:  # Keep first, delete rest
                    self.calendar_service.delete_event(calendar_id, event["id"])
                    stats["deleted"] += 1
            
        except Exception as e:
            logger.error(f"Failed to sync shift {shift.id} to calendar: {e}")
            
        return stats
    
    def _generate_event_details(self, shift) -> Dict[str, str]:
        """Generate event title and description."""
        if shift.shift_type == "regular" and shift.start_date and shift.end_date:
            start_time = datetime.strptime(shift.start_date, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(shift.end_date, "%Y-%m-%d %H:%M:%S")
            summary = f"🏥 Work ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')})"
        else:
            summary = f"{shift.shift_type.replace('_', ' ').title()}"
        
        description = f"{shift.name} - {shift.date}\\n{shift.raw_data}"
        
        return {
            "summary": summary,
            "description": description,
        }
    
    def _create_or_update_event(
        self, calendar_id: str, shift, event_details: Dict[str, str], existing_events: List
    ) -> Optional[str]:
        """Create or update a timed event."""
        if not shift.start_date or not shift.end_date:
            return None
        
        start_time = datetime.strptime(shift.start_date, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(shift.end_date, "%Y-%m-%d %H:%M:%S")
        
        # Check if existing event matches
        if existing_events:
            existing_event = existing_events[0]
            
            # Parse existing event times for comparison
            existing_start = None
            existing_end = None
            if "start" in existing_event and "dateTime" in existing_event["start"]:
                existing_start = datetime.fromisoformat(
                    existing_event["start"]["dateTime"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
            if "end" in existing_event and "dateTime" in existing_event["end"]:
                existing_end = datetime.fromisoformat(
                    existing_event["end"]["dateTime"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
            
            if (
                existing_event.get("summary") == event_details["summary"]
                and existing_event.get("description") == event_details["description"]
                and existing_start == start_time
                and existing_end == end_time
            ):
                return existing_event["id"]  # No changes needed
            
            # Update existing event
            if self.calendar_service.update_event(
                calendar_id,
                existing_event["id"],
                event_details["summary"],
                start_time,
                end_time,
                event_details["description"],
            ):
                return existing_event["id"]
        
        # Create new event
        return self.calendar_service.create_event(
            calendar_id,
            event_details["summary"],
            start_time,
            end_time,
            event_details["description"],
        )
    
    def _create_or_update_allday_event(
        self, calendar_id: str, shift, event_details: Dict[str, str], existing_events: List
    ) -> Optional[str]:
        """Create or update an all-day event."""
        shift_date = datetime.strptime(shift.date, "%Y-%m-%d")
        start_time = shift_date
        end_time = shift_date + timedelta(days=1)
        
        # Check if existing event matches
        if existing_events:
            existing_event = existing_events[0]
            
            # Parse existing event date for comparison (all-day events use date instead of dateTime)
            existing_start = None
            if "start" in existing_event and "date" in existing_event["start"]:
                existing_start = datetime.strptime(existing_event["start"]["date"], "%Y-%m-%d")
            
            if (
                existing_event.get("summary") == event_details["summary"]
                and existing_event.get("description") == event_details["description"]
                and existing_start == start_time
            ):
                return existing_event["id"]  # No changes needed
        
        # Delete existing events and create new one
        for event in existing_events:
            self.calendar_service.delete_event(calendar_id, event["id"])
        
        # Create new all-day event
        return self.calendar_service.create_event(
            calendar_id,
            event_details["summary"],
            start_time,
            end_time,
            event_details["description"],
        )
