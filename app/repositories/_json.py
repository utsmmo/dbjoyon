import json
from typing import Any


def to_jsonb_param(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)
