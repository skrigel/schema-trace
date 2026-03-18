# app/schemas/model.py
from datetime import datetime
from pydantic import BaseModel
from app.schemas.fields import FieldResponseActive


class ModelBase(BaseModel):
    name: str
    description: str | None = None


class ModelCreate(ModelBase):
    project_id: int


class ModelUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ModelResponse(ModelBase):
    id: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ModelResponseWithFields(ModelResponse):
    """Response that includes the model's current active fields"""
    fields: list[FieldResponseActive] = []

    # class Config:
    #     from_attributes = True