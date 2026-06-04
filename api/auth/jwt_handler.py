import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt

JWT_SECRET = os.environ.get("P2P_JWT_SECRET", "change-this-secret-key-that-is-long-enough")
JWT_ALGORITHM = "HS256"


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        exp = now + expires_delta
    else:
        exp = now + timedelta(minutes=60)
    to_encode.update({"exp": exp, "iat": now})
    token = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except Exception:
        raise
