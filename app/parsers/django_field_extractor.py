import ast
from typing import Dict, Any, Optional

class DjangoFieldExtractor:
    """Extracts metadata from Django field definitions"""

    def extract_field_metadata(self, field_node: Optional[ast.AST]) -> Dict[str, Any]:
        """
        Extract field type and constraints from Django field definition.
        
        Example:
            models.EmailField(max_length=120, unique=True, null=False)
            
            Returns:
            {
                'field_type': 'EmailField',
                'max_length': 120,
                'unique': True,
                'nullable': False
            }
        """
        if not field_node or not isinstance(field_node, ast.Call):
            return {}

        metadata = {}

        # Extract field type (CharField, EmailField, etc.)
        if isinstance(field_node.func, ast.Attribute):
            metadata['field_type'] = field_node.func.attr

        # Extract keyword arguments
        for keyword in field_node.keywords:
            if not keyword.arg:
                continue

            value = self._extract_value(keyword.value)

            # Map Django field kwargs to our schema
            if keyword.arg == "null":
                metadata['nullable'] = value
            elif keyword.arg == "max_length":
                metadata['max_length'] = value
            elif keyword.arg == "unique":
                metadata['unique'] = value
            elif keyword.arg == "default":
                metadata['default'] = value
            elif keyword.arg == "blank":
                metadata['blank'] = value
            elif keyword.arg == "db_index":
                metadata['indexed'] = value
            elif keyword.arg == "primary_key":
                metadata['primary_key'] = value
            elif keyword.arg == "auto_now":
                metadata['auto_now'] = value
            elif keyword.arg == "auto_now_add":
                metadata['auto_now_add'] = value

        return metadata

    def _extract_value(self, node: ast.AST) -> Any:
        """Extract value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            # Handle True, False, None
            if node.id == "True":
                return True
            elif node.id == "False":
                return False
            elif node.id == "None":
                return None
        elif isinstance(node, ast.List):
            return [self._extract_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._extract_value(elt) for elt in node.elts)

        return None