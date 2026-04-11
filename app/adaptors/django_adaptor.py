from .base import BaseAdapter, SchemaEventData
from typing import List
from pathlib import Path
from app.parsers.django_migration import DjangoMigrationFile
from app.parsers.django_mapper import DjangoOperationMapper
from app.parsers.django_field_extractor import DjangoFieldExtractor

class DjangoAdapter(BaseAdapter):
    """Django migration adapter with AST parsing"""

    def __init__(self):
        self.field_extractor = DjangoFieldExtractor()
        self.operation_mapper = DjangoOperationMapper(self.field_extractor)

    def detect(self, path: Path) -> bool:
        """Look for migrations/*.py files"""
        path = Path(path)

        if path.is_dir():
            # Check for migrations directory
            migrations_dirs = list(path.rglob("migrations"))
            for mig_dir in migrations_dirs:
                if any(mig_dir.glob("*.py")):
                    return True

        return False

    def parse(self, path: Path) -> List[SchemaEventData]:
        """
        Parse all Django migration files and extract schema events.
        """
        path = Path(path)
        events = []

        # Check if path IS a migrations directory or contains one
        if path.name == "migrations" and path.is_dir():
            # We're in the migrations directory itself
            migration_files = sorted(path.glob("*.py"))
        else:
            # Look for migrations subdirectories
            migration_files = sorted(path.rglob("migrations/*.py"))

        for file_path in migration_files:
            # Skip __init__.py and __pycache__
            if file_path.name.startswith("__"):
                continue

            try:
                # Parse migration file
                migration = DjangoMigrationFile(file_path)
                migration.load()

                timestamp = migration.extract_timestamp()

                # Extract operations
                operations = migration.extract_operations()

                # Map each operation to events (may return multiple events per operation)
                for op_node in operations:
                    operation_events = self.operation_mapper.map_operation(op_node, timestamp)
                    events.extend(operation_events)

            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")
                continue

        events.sort(key=lambda e: e.timestamp)

        return events

    def get_framework_name(self) -> str:
        return "Django"