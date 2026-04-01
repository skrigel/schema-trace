from datetime import datetime
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base
from enum import Enum
## DATABASE MODELS
 

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=False, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    full_name = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class EventType(Enum):
    ADD_COLUMN = "ADD_COLUMN"
    REMOVE_COLUMN = "REMOVE_COLUMN"
    CHANGE_TYPE = "CHANGE_TYPE"
    CHANGE_NULLABLE = "CHANGE_NULLABLE"
    ADD_INDEX = "ADD_INDEX"
    REMOVE_INDEX = "REMOVE_INDEX"
    RENAME_COLUMN = "RENAME_COLUMN"



class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    models = relationship("Model", back_populates="project", cascade="all, delete-orphan")


class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    project = relationship("Project", back_populates="models")
    events = relationship("SchemaEvent", back_populates="model", order_by="SchemaEvent.timestamp", cascade="all, delete-orphan")
    fields = relationship("Field", back_populates="model", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('project_id', 'name', name='uq_project_model'),
      )

    

class Field(Base):
    __tablename__ = "fields"
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)

    field_type = Column(String(100), nullable=False)  # e.g., varchar(120), integer, etc.
    nullable = Column(Boolean, nullable=False, default=True)
    unique = Column(Boolean, nullable=False, default=False)
    default_value = Column(String(255), nullable=True)

    added_at = Column(DateTime, default=datetime.now, nullable=False)
    removed_at = Column(DateTime, nullable=True)

    model = relationship("Model", back_populates="fields")

    __table_args__ = (
        UniqueConstraint('model_id', 'name', name='uq_model_field'),
        Index('idx_model_field', 'model_id', 'name'),
    )


class SchemaEvent(Base):
    __tablename__ = "schema_events"
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)

    # Event details
    event_type = Column(SQLEnum(EventType), nullable=False)  # e.g., ADD_COLUMN, REMOVE_COLUMN, CHANGE_TYPE
    field_name = Column(String(100), nullable=False)  # Name of the field being changed
    timestamp = Column(DateTime, default=datetime.now, nullable=False)

    # Additional data
    risk_level = Column(String(50), nullable=False, default="low")  # low, medium, high
    # metadata = Column(JSON, nullable=True)  # Additional event metadata as JSON

    # Relationships
    model = relationship("Model", back_populates="events")


# TODO: SchemaHistory - keeps track of all schema changes (relation to SchemaUpdateEvents), including the timestamp, user who made the change, and a description of the change.
# TODO: SchemaUpdateEvent - added new fields/removed fields/changed field types, etc.

# TODO: define different types of updates