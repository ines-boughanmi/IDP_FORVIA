from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
import os

from .schemas import User
from .password import hash_password, verify_password
from .jwt_handler import create_access_token, decode_access_token

from ..db.session import SessionLocal
from ..db import crud

security = HTTPBearer()


def create_user(username: str, email: str, password: str, role: str = "user") -> User:
    db = SessionLocal()
    try:
        existing = crud.get_user_by_username(db, username)
        if existing:
            raise ValueError("User already exists")
        hashed = hash_password(password)
        db_user = crud.create_user(db, username=username, email=email, hashed_password=hashed, role=role)
        return User(id=db_user.id, username=db_user.username, email=db_user.email, role=db_user.role)
    finally:
        db.close()


def get_user_by_username(username: str) -> Optional[User]:
    db = SessionLocal()
    try:
        db_user = crud.get_user_by_username(db, username)
        if not db_user:
            return None
        return User(id=db_user.id, username=db_user.username, email=db_user.email, role=db_user.role)
    finally:
        db.close()


def authenticate_user(username: str, password: str) -> Optional[User]:
    db = SessionLocal()
    try:
        db_user = crud.get_user_by_username(db, username)
        if not db_user:
            return None
        if not verify_password(password, db_user.hashed_password):
            return None
        return User(id=db_user.id, username=db_user.username, email=db_user.email, role=db_user.role)
    finally:
        db.close()


def generate_token_for_user(user: User, expires_minutes: int = 60) -> str:
    data = {"user_id": user.id, "username": user.username, "role": user.role}
    token = create_access_token(data, expires_delta=timedelta(minutes=expires_minutes))
    return token


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    db = SessionLocal()
    try:
        db_user = crud.get_user_by_username(db, username)
        if not db_user:
            raise HTTPException(status_code=401, detail="User not found")
        return User(id=db_user.id, username=db_user.username, email=db_user.email, role=db_user.role)
    finally:
        db.close()
