import ast
from typing import Optional, Dict, Any
from datetime import datetime
from app.adaptors.base import SchemaEventData

class DjangoOperationMapper:
    """Maps Django migration operations to SchemaEventData"""

    def __init__(self, field_extractor):
        self.field_extractor = field_extractor

    def map_operation(
        self, 
        operation_node: ast.Call, 
        timestamp: datetime
    ) -> Optional[SchemaEventData]:
        """
        Map a single Django operation to SchemaEventData.
        
        Returns None if operation is not a schema change we track.
        """
        op_name = self._get_operation_name(operation_node)
        if not op_name:
            return None

        # Extract common arguments
        args = self._extract_args(operation_node)

        # Map based on operation type
        if op_name == "AddField":
            return self._map_add_field(args, timestamp)

        elif op_name == "RemoveField":
            return self._map_remove_field(args, timestamp)

        elif op_name == "AlterField":
            return self._map_alter_field(args, timestamp)

        elif op_name == "RenameField":
            return self._map_rename_field(args, timestamp)

        elif op_name == "CreateModel":
            return self._map_create_model(args, timestamp)

        elif op_name == "AddIndex":
            return self._map_add_index(args, timestamp)

        elif op_name == "RemoveIndex":
            return self._map_remove_index(args, timestamp)

        # Ignore operations we don't track
        return None

    def _get_operation_name(self, node: ast.Call) -> Optional[str]:
        """Extract operation name (e.g., 'AddField' from migrations.AddField)"""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _extract_args(self, node: ast.Call) -> Dict[str, Any]:
        """
        Extract arguments from operation call.
        
        Django uses both positional and keyword args:
            migrations.AddField(
                model_name='User',          # can be positional or keyword
                name='email',               # can be positional or keyword
                field=models.EmailField()   # usually positional
            )
        """
        args = {}

        for keyword in node.keywords:
            if keyword.arg == "model_name":
                args['model_name'] = self._extract_constant(keyword.value)
            elif keyword.arg == "name":
                args['field_name'] = self._extract_constant(keyword.value)
            elif keyword.arg == "field":
                args['field'] = keyword.value
            elif keyword.arg == "old_name":
                args['old_name'] = self._extract_constant(keyword.value)
            elif keyword.arg == "new_name":
                args['new_name'] = self._extract_constant(keyword.value)

        return args

    def _extract_constant(self, node: ast.AST) -> Any:
        """Extract constant value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        return None

    def _map_add_field(self, args: Dict, timestamp: datetime) -> Optional[SchemaEventData]:
        """Map AddField operation"""
        model_name = args.get('model_name')
        field_name = args.get('field_name')
        field_node = args.get('field')

        if not model_name or not field_name:
            return None

        metadata = self.field_extractor.extract_field_metadata(field_node)

        return SchemaEventData(
            model_name=model_name,
            event_type="ADD_COLUMN",
            field_name=field_name,
            timestamp=timestamp,
            risk_level="low",
            metadata=metadata
        )

    def _map_remove_field(self, args: Dict, timestamp: datetime) -> Optional[SchemaEventData]:
        model_name = args.get('model_name')
        field_name = args.get('field_name')

        if not model_name or not field_name:
            return None

        return SchemaEventData(
            model_name=model_name,
            event_type="REMOVE_COLUMN",
            field_name=field_name,
            timestamp=timestamp,
            risk_level="high",  # Removing fields is dangerous!
            metadata={}
        )

    def _map_alter_field(self, args: Dict, timestamp: datetime) -> Optional[SchemaEventData]:
        model_name = args.get('model_name')
        field_name = args.get('field_name')
        field_node = args.get('field')

        if not model_name or not field_name:
            return None

        metadata = self.field_extractor.extract_field_metadata(field_node)
        metadata['operation'] = 'alter'

        return SchemaEventData(
            model_name=model_name,
            event_type="CHANGE_TYPE",
            field_name=field_name,
            timestamp=timestamp,
            risk_level="medium",
            metadata=metadata
        )

    def _map_rename_field(self, args: Dict, timestamp: datetime) -> Optional[SchemaEventData]:
        model_name = args.get('model_name')
        old_name = args.get('old_name')
        new_name = args.get('new_name')

        if not model_name or not old_name or not new_name:
            return None

        return SchemaEventData(
            model_name=model_name,
            event_type="RENAME_COLUMN",
            field_name=old_name,  # Use old name as field_name
            timestamp=timestamp,
            risk_level="high",
            metadata={'new_name': new_name}
        )

    def _map_create_model(self, args: Dict, timestamp: datetime) -> Optional[SchemaEventData]:
        """
        Map CreateModel operation.
        
        Note: This creates multiple events - one for the model creation,
        then one for each field. For now, we'll skip this or handle specially.
        """
        # TODO: Decide how to handle CreateModel
        # Option 1: Skip it (fields will be added via AddField in later migrations)
        # Option 2: Create ADD_COLUMN events for each field
        return None

    def _map_add_index(self, args: Dict, timestamp: datetime) -> Optional[SchemaEventData]:
        """Map AddIndex operation"""
        # TODO: Implement index tracking
        return None

    def _map_remove_index(self, args: Dict, timestamp: datetime) -> Optional[SchemaEventData]:
        """Map RemoveIndex operation"""
        # TODO: Implement index tracking
        return None
