from datetime import datetime
from pydantic import BaseModel, Field

### DATABASE MODELS

class SchemaEventBase(BaseModel):
    event_type: str
    field_name: str = Field(..., description="Name of the field being changed")
    risk_level: str = Field(default="low", description="Risk level: low, medium, high")
    # metadata: dict | None = Field(default=None, description="Additional event metadata as JSON")


class SchemaEventCreate(SchemaEventBase):
    model_id: int
    timestamp: datetime | None = Field(default=None, description="Event timestamp (defaults to now if not provided)")


class SchemaEventResponse(SchemaEventBase):
    id: int
    model_id: int
    timestamp: datetime

    class Config:
        from_attributes = True