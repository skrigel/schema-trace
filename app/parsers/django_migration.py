import ast
import re
from pathlib import Path
from datetime import datetime
from typing import List

class DjangoMigrationFile:
    """Parses a single Django migration file"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.ast_tree = None
        self.operations = []

    def load(self) -> None:
        """Load and parse file into AST"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.ast_tree = ast.parse(content)
        except Exception as e:
            raise ValueError(f"Failed to parse {self.file_path}: {e}")

    def extract_operations(self) -> List[ast.Call]:
        """
        Extract operations list from Migration class.
        
        Example input:
            class Migration(migrations.Migration):
                operations = [...]
        """
        if not self.ast_tree:
            self.load()

        operations = []

        if not self.ast_tree:
            return operations

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.ClassDef) and node.name == "Migration":
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "operations":
                                if isinstance(item.value, ast.List):
                                    operations += item.value.elts

        return operations

    def extract_timestamp(self) -> datetime:
        """
        Extract timestamp from filename.
        
        Django formats:
        - 0001_initial.py → use file mtime
        - 0002_auto_20240112_1030.py → 2024-01-12 10:30
        - 0003_add_email_field_20240115.py → 2024-01-15 00:00
        """
        filename = self.file_path.stem
        match = re.search(r'_(?:auto_)?(\d{8})_?(\d{4})?', filename)
        if match:
            date_str = match.group(1)  # YYYYMMDD
            time_str = match.group(2) or "0000"  # HHMM or default
            try:
                return datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M")
            except ValueError:
                pass

        match = re.search(r'_(\d{8})', filename)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y%m%d")
            except ValueError:
                pass

        # Fallback, use file modification time
        return datetime.fromtimestamp(self.file_path.stat().st_mtime)