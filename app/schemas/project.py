from pydantic import BaseModel
from datetime import datetime

# Base schema with shared fields
class ProjectBase(BaseModel):
    name: str
    description: str | None = None

# For creating a project (request body)
class ProjectCreate(ProjectBase):
    pass

# For updating a project (request body)
class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

# For responses (includes id, timestamps, etc.)
class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Allows reading from ORM models
