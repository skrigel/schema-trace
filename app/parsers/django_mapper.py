import ast
from typing import Optional, Dict, Any, List
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
    ) -> List[SchemaEventData]:
        """
        Map a single Django operation to a list of SchemaEventData.

        Returns empty list if operation is not a schema change we track.
        Most operations return a single event, but CreateModel returns multiple.
        """
        op_name = self._get_operation_name(operation_node)
        if not op_name:
            return []

        # Extract common arguments
        args = self._extract_args(operation_node)

        # Map based on operation type
        if op_name == "AddField":
            event = self._map_add_field(args, timestamp)
            return [event] if event else []

        elif op_name == "RemoveField":
            event = self._map_remove_field(args, timestamp)
            return [event] if event else []

        elif op_name == "AlterField":
            event = self._map_alter_field(args, timestamp)
            return [event] if event else []

        elif op_name == "RenameField":
            event = self._map_rename_field(args, timestamp)
            return [event] if event else []

        elif op_name == "CreateModel":
            return self._extract_create_model_fields(operation_node, timestamp)

        elif op_name == "AddIndex":
            event = self._map_add_index(args, timestamp)
            return [event] if event else []

        elif op_name == "RemoveIndex":
            event = self._map_remove_index(args, timestamp)
            return [event] if event else []

        # Ignore operations we don't track
        return []

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

    def _extract_create_model_fields(self, operation_node: ast.Call, timestamp: datetime) -> List[SchemaEventData]:
        """
        Extract all fields from a CreateModel operation as separate ADD_COLUMN events.

        Example:
            migrations.CreateModel(
                name='User',
                fields=[
                    ('id', models.BigAutoField(...)),
                    ('username', models.CharField(...)),
                ]
            )
        """
        events = []
        model_name = None

        # Extract model name and fields from operation
        for keyword in operation_node.keywords:
            if keyword.arg == "name":
                model_name = self._extract_constant(keyword.value)
            elif keyword.arg == "fields" and isinstance(keyword.value, ast.List):
                if not model_name:
                    continue

                # Each field is a tuple: (field_name, field_definition)
                for field_tuple in keyword.value.elts:
                    if not isinstance(field_tuple, ast.Tuple) or len(field_tuple.elts) < 2:
                        continue

                    field_name = self._extract_constant(field_tuple.elts[0])
                    field_node = field_tuple.elts[1]

                    if not field_name:
                        continue

                    metadata = self.field_extractor.extract_field_metadata(field_node)

                    events.append(SchemaEventData(
                        model_name=model_name,
                        event_type="ADD_COLUMN",
                        field_name=field_name,
                        timestamp=timestamp,
                        risk_level="low",
                        metadata=metadata
                    ))

        return events

    def _map_add_index(self, args: Dict, timestamp: datetime) -> Optional[SchemaEventData]:
        """Map AddIndex operation"""
        # TODO: Implement index tracking
        return None

    def _map_remove_index(self, args: Dict, timestamp: datetime) -> Optional[SchemaEventData]:
        """Map RemoveIndex operation"""
        # TODO: Implement index tracking
        return None
