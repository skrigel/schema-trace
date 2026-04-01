from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import ast

class MigrationFile(ABC):

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.ast_tree = None

    def load(self):
        with open(self.file_path, 'r') as f:
            self.ast_tree = ast.parse(f.read())

    @abstractmethod
    def extract_operations(self) -> List[ast.Call]: 
        pass

    @abstractmethod
    def extract_timestamp(self) -> datetime:
        pass

