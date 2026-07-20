from datetime import date, datetime
import re

class TypeSystem:
    """Static type checker and inference engine for Dapine."""
    
    TYPES = ['int', 'float', 'string', 'bool', 'date', 'datetime', 'list', 'dict', 'any', 'null']
    
    @staticmethod
    def infer(value):
        """Infer the type of a value."""
        if value is None: return 'null'
        if isinstance(value, bool): return 'bool'
        if isinstance(value, int): return 'int'
        if isinstance(value, float): return 'float'
        if isinstance(value, datetime): return 'datetime'
        if isinstance(value, date): return 'date'
        if isinstance(value, str): return 'string'
        if isinstance(value, list): return 'list'
        if isinstance(value, dict): return 'dict'
        return 'any'
    
    @staticmethod
    def infer_column(rows, col_name):
        """Infer the type of a column from sample rows."""
        types_seen = set()
        for row in rows[:100]:
            val = row.get(col_name)
            types_seen.add(TypeSystem.infer(val))
        
        if len(types_seen) == 1: return list(types_seen)[0]
        if 'null' in types_seen: types_seen.discard('null')
        if len(types_seen) == 1: return list(types_seen)[0]
        return 'any'
    
    @staticmethod
    def infer_schema(rows):
        """Infer schema from rows."""
        if not rows: return {}
        schema = {}
        all_keys = set()
        for row in rows: all_keys.update(row.keys())
        for key in all_keys:
            schema[key] = TypeSystem.infer_column(rows, key)
        return schema
    
    @staticmethod
    def check(value, expected_type):
        """Check if value matches expected type."""
        actual = TypeSystem.infer(value)
        if expected_type == 'any': return True
        if expected_type == 'null': return value is None
        if actual == 'null': return True
        if expected_type == actual: return True
        if expected_type == 'float' and actual == 'int': return True
        if expected_type == 'string': return True  # Anything can be string
        return False
    
    @staticmethod
    def cast(value, target_type):
        """Cast value to target type."""
        if value is None: return None
        try:
            if target_type == 'int': return int(float(value))
            if target_type == 'float': return float(value)
            if target_type == 'string': return str(value)
            if target_type == 'bool': return bool(value)
            if target_type == 'date':
                if isinstance(value, date): return value
                return date.fromisoformat(str(value))
            if target_type == 'datetime':
                if isinstance(value, datetime): return value
                return datetime.fromisoformat(str(value))
        except:
            pass
        return value
    
    @staticmethod
    def validate_schema(df, expected_schema):
        """Validate DataFrame schema."""
        errors = []
        for col, expected_type in expected_schema.items():
            if col not in df.schema:
                errors.append(f"Missing column: '{col}'")
            else:
                for i, row in enumerate(df.rows[:10]):
                    val = row.get(col)
                    if not TypeSystem.check(val, expected_type):
                        errors.append(f"Row {i}, col '{col}': expected {expected_type}, got {TypeSystem.infer(val)}")
        return errors
    
    @staticmethod
    def is_numeric(typ):
        return typ in ('int', 'float')
    
    @staticmethod
    def is_comparable(typ1, typ2):
        if typ1 == typ2: return True
        if TypeSystem.is_numeric(typ1) and TypeSystem.is_numeric(typ2): return True
        return False