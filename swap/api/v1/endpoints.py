from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from swap.db_init import create_tables
from swap.utils.logger import logger
from swap.scheduler.tasks import send_notification
from swap.core.rota_operations import get_rota
from swap.models.notification import NotificationRequest
from swap.models.calendar import Calendar, UserCalendar
from swap.core.database import get_db

from swap.api.v1.scheduler_api import router as scheduler_router
from swap.services.rota_parser import RotaParser
from swap.api.v1.calendar import router as calendar_router
from swap.core.raw2rota import rota_spread_to_raw_db

# Create the main router
router = APIRouter()

# Include the scheduler router
router.include_router(scheduler_router)

# Include the calendar router
router.include_router(calendar_router)


@router.post("/schedule-notification")
async def schedule_notification_endpoint(request: NotificationRequest):
    try:
        await send_notification(request.message, None, request.cron_expression)
        return {"status": "Notification scheduled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/db_init")
async def db_init():
    """
    This endpoint is used to initialize the database
    """
    create_tables()
    return {"status": "Database initialized successfully"}


@router.get("/rota")
async def get_rota_endpoint():
    """This endpoint is used to parse the rota spreadsheet and return the parsed data"""
    return await get_rota()


@router.get("/raw2rota")
async def raw_to_rota_endpoint():
    """
    This endpoint is used to parse the rota spreadsheet and store the data in the database
    """
    result = rota_spread_to_raw_db()
    return result


@router.post("/calendar-mapping")
async def create_calendar_mapping(
    user_name: str,
    calendar_id: int,
    session: Session = Depends(get_db)
):
    """Map a user (by name) to their Google Calendar"""
    # Check if calendar exists
    calendar = session.get(Calendar, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    # Check if mapping already exists
    existing = session.query(UserCalendar).filter(
        UserCalendar.user_name == user_name,
        UserCalendar.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"User {user_name} already mapped to calendar {existing.calendar_id}"
        )
    
    # Create new mapping
    user_calendar = UserCalendar(
        user_name=user_name,
        calendar_id=calendar_id
    )
    session.add(user_calendar)
    session.commit()
    session.refresh(user_calendar)
    
    return user_calendar


@router.get("/calendar-mapping")
async def list_calendar_mappings(session: Session = Depends(get_db)):
    """List all active user-calendar mappings"""
    mappings = session.query(UserCalendar).filter(UserCalendar.is_active == True).all()
    return mappings


@router.delete("/calendar-mapping/{mapping_id}")
async def delete_calendar_mapping(mapping_id: int, session: Session = Depends(get_db)):
    """Delete (deactivate) a user-calendar mapping"""
    mapping = session.get(UserCalendar, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    mapping.is_active = False
    mapping.updated_at = datetime.utcnow()
    session.commit()
    
    return {"status": "success"}
