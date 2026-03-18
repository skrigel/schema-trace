from datetime import datetime
from pydantic import BaseModel, Field


class SchemaEventBase(BaseModel):
    event_type: str
    field_name: str = Field(..., description="Name of the field being changed")
    risk_level: str = Field(default="low", description="Risk level: low, medium, high")
    metadata: dict | None = Field(default=None, description="Additional event metadata as JSON")


class SchemaEventCreate(SchemaEventBase):
    model_id: int


class SchemaEventResponse(SchemaEventBase):
    id: int
    model_id: int
    timestamp: datetime

    class Config:
        from_attributes = True