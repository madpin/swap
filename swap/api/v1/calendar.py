# swap/api/v1/calendar.py
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from swap.core.database import get_db
from swap.models.calendar import Calendar, Event

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/", response_model=Calendar, status_code=201)
def create_calendar(calendar: Calendar, session: Session = Depends(get_db)):
    session.add(calendar)
    session.commit()
    session.refresh(calendar)
    return calendar


@router.get("/", response_model=List[Calendar])
def read_calendars(session: Session = Depends(get_db)):
    calendars = session.exec(select(Calendar)).all()
    return calendars


@router.get("/{calendar_id}", response_model=Calendar)
def read_calendar(calendar_id: int, session: Session = Depends(get_db)):
    calendar = session.get(Calendar, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return calendar


@router.put("/{calendar_id}", response_model=Calendar)
def update_calendar(
    calendar_id: int, calendar: Calendar, session: Session = Depends(get_db)
):
    db_calendar = session.get(Calendar, calendar_id)
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    for key, value in calendar.model_dump(exclude_unset=True).items():
        setattr(db_calendar, key, value)
    session.add(db_calendar)
    session.commit()
    session.refresh(db_calendar)
    return db_calendar


@router.delete("/{calendar_id}", status_code=204)
def delete_calendar(calendar_id: int, session: Session = Depends(get_db)):
    calendar = session.get(Calendar, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    session.delete(calendar)
    session.commit()
    return


@router.post("/{calendar_id}/events", response_model=Event, status_code=201)
def create_event(calendar_id: int, event: Event, session: Session = Depends(get_db)):
    calendar = session.get(Calendar, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    event.calendar_id = calendar_id
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.get("/{calendar_id}/events", response_model=List[Event])
def read_events(calendar_id: int, session: Session = Depends(get_db)):
    calendar = session.get(Calendar, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    events = session.exec(select(Event).where(Event.calendar_id == calendar_id)).all()
    return events


@router.get("/{calendar_id}/events/{event_id}", response_model=Event)
def read_event(calendar_id: int, event_id: int, session: Session = Depends(get_db)):
    calendar = session.get(Calendar, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    event = session.get(Event, event_id)
    if not event or event.calendar_id != calendar_id:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{calendar_id}/events/{event_id}", response_model=Event)
def update_event(
    calendar_id: int, event_id: int, event: Event, session: Session = Depends(get_db)
):
    db_event = session.get(Event, event_id)
    if not db_event or db_event.calendar_id != calendar_id:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event.model_dump(exclude_unset=True).items():
        setattr(db_event, key, value)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


@router.delete("/{calendar_id}/events/{event_id}", status_code=204)
def delete_event(calendar_id: int, event_id: int, session: Session = Depends(get_db)):
    event = session.get(Event, event_id)
    if not event or event.calendar_id != calendar_id:
        raise HTTPException(status_code=404, detail="Event not found")
    session.delete(event)
    session.commit()
    return
