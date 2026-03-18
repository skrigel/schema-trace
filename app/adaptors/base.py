from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel


class SchemaEventData(BaseModel):
    """
    Canonical schema event format that adapters return.

    This matches our SchemaEventCreate schema but without model_id
    (model_id is determined by the CLI based on model name mapping).

    Attributes:
        model_name: Name of the database model (e.g., "User", "Post")
        event_type: Type of schema change (ADD_COLUMN, REMOVE_COLUMN, etc.)
        field_name: Name of the field being modified
        timestamp: When the change occurred
        risk_level: Risk assessment (low, medium, high)
        metadata: Additional event-specific data as JSON
    """
    model_name: str
    event_type: str
    field_name: str
    timestamp: datetime
    risk_level: str = "low"
    metadata: Dict[str, Any] = {}


class BaseAdapter(ABC):
    """
    Base adapter interface for parsing migration files from different frameworks.

    Each framework (Django, Alembic, Rails, etc.) implements this interface
    to extract schema events in a canonical format.

    This design allows SchemaTrace to support multiple ORMs/frameworks without
    coupling the core logic to any specific migration format.
    """

    @abstractmethod
    def detect(self, path: Path) -> bool:
        """
        Detect if the given path contains migrations for this framework.

        Args:
            path: Directory path to check for migrations

        Returns:
            True if this adapter can parse the migrations in this path

        Example:
            Django: Look for "migrations/*.py" files
            Alembic: Look for "alembic/versions/*.py" files
        """
        pass

    @abstractmethod
    def parse(self, path: Path) -> List[SchemaEventData]:
        """
        Parse all migration files in the given path and extract schema events.

        Args:
            path: Directory containing migration files

        Returns:
            List of schema events in chronological order

        Implementation notes:
            - Should return events sorted by timestamp
            - Should handle malformed migrations gracefully (log warnings, skip)
            - Should never execute migration code (security)
            - Should extract as much metadata as possible from field definitions
        """
        pass

    def get_framework_name(self) -> str:
        """
        Return the name of this framework for display purposes.

        Returns:
            Human-readable framework name (e.g., "Django", "Alembic")
        """
        return self.__class__.__name__.replace("Adapter", "")
