from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import SchemaEvent, Model
from app.schemas.events import SchemaEventCreate, SchemaEventResponse
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/events", tags=["events"])


class BulkEventCreate(BaseModel):
    """Schema for bulk event creation"""
    events: List[SchemaEventCreate]


class BulkEventResponse(BaseModel):
    """Response for bulk event creation"""
    created_count: int
    events: List[SchemaEventResponse]


@router.post("/bulk", response_model=BulkEventResponse, status_code=201)
def create_events_bulk(payload: BulkEventCreate, db: Session = Depends(get_db)):
    """
    Bulk create schema events (used by CLI scan command)

    This is the primary endpoint for the CLI to upload parsed migration data.
    Accepts a list of events and creates them all in a single transaction.
    """
    created_events = []

    for event_data in payload.events:
        model = db.query(Model).filter(Model.id == event_data.model_id).first()
        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Model with id {event_data.model_id} not found"
            )

        db_event = SchemaEvent(**event_data.model_dump())
        db.add(db_event)
        created_events.append(db_event)

    db.commit()

    # Refresh all events to get generated IDs and timestamps
    for event in created_events:
        db.refresh(event)

    return BulkEventResponse(
        created_count=len(created_events),
        events=created_events
    )


@router.post("/", response_model=SchemaEventResponse, status_code=201)
def create_event(event: SchemaEventCreate, db: Session = Depends(get_db)):
    """Create a single schema event"""
    # Validate model exists
    model = db.query(Model).filter(Model.id == event.model_id).first()
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model with id {event.model_id} not found"
        )

    db_event = SchemaEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.get("/model/{model_id}", response_model=List[SchemaEventResponse])
def list_model_events(model_id: int, db: Session = Depends(get_db)):
    """
    Get all events for a specific model, ordered chronologically.

    This allows viewing the complete history of schema changes for a model.
    """
    # Validate model exists
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model with id {model_id} not found"
        )

    events = db.query(SchemaEvent)\
        .filter(SchemaEvent.model_id == model_id)\
        .order_by(SchemaEvent.timestamp)\
        .all()

    return events


@router.get("/{event_id}", response_model=SchemaEventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a single event by ID"""
    event = db.query(SchemaEvent).filter(SchemaEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Event with id {event_id} not found"
        )
    return event
