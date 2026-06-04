from fastapi import Header, HTTPException
from typing import Optional
import os

# Simple auth: support static API key or Bearer token check.
# If PyJWT is available, token validation can be added later.

API_KEY = os.environ.get("P2P_API_KEY", "")
SIMPLE_TOKEN = os.environ.get("P2P_API_TOKEN", "testtoken")


def require_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Require an API key header `x-api-key` if configured."""
    if not API_KEY:
        # API key not configured -> allow
        return True
    if x_api_key == API_KEY:
        return True
    raise HTTPException(status_code=401, detail="Invalid API Key")


def require_bearer_token(authorization: Optional[str] = Header(None)) -> bool:
    """Simple Bearer token check. Do not rely on this for strong security.

    Accepts Authorization: Bearer <SIMPLE_TOKEN>
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = parts[1]
    if token != SIMPLE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return True
