from typing import Any, Dict, Optional


def format_response(data: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"status": "success", "data": data, "metadata": metadata or {}}
