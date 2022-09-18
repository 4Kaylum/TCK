from typing import Any
import json
from datetime import datetime
import uuid


__all__ = (
    'HTTPEncoder',
)


class HTTPEncoder(json.JSONEncoder):

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, uuid.UUID):
            return str(o)
        return super().default(o)
