from datetime import datetime
from pydantic import BaseModel


class FieldBase(BaseModel):
    name: str
    field_type: str
    nullable: bool = True
    unique: bool = False
    default_value: str | None = None


class FieldCreate(FieldBase):
    model_id: int


class FieldResponse(FieldBase):
    model_id: int
    added_at: datetime
    removed_at: datetime | None = None

    class Config:
        from_attributes = True


class FieldResponseActive(FieldBase):
    """Response schema for active fields only (removed_at is None)"""
    added_at: datetime

    class Config:
        from_attributes = True