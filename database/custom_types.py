from sqlalchemy.types import TypeDecorator, Text
import json

class JSONText(TypeDecorator):
    impl = Text
    cache_ok = True  # Optional but recommended for SQLAlchemy 1.4+

    def process_bind_param(self, value, dialect):
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        if not value:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None