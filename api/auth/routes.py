from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from datetime import timedelta

from .schemas import LoginRequest, RegisterRequest, User
from .dependencies import authenticate_user, generate_token_for_user, create_user, get_current_user
from ..core.response import format_response

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        return JSONResponse(status_code=401, content={"status": "error", "message": "Invalid credentials", "code": "invalid_credentials"})
    token = generate_token_for_user(user, expires_minutes=60)
    return format_response({"access_token": token, "token_type": "bearer"}, metadata={"expires_in": 3600})


@router.post("/register")
def register(payload: RegisterRequest):
    try:
        new_user = create_user(payload.username, payload.email, payload.password)
        return format_response({"user": new_user.dict()}, metadata={"message": "user_created"})
    except ValueError as e:
        message = str(e)
        if message == "User already exists":
            code = "user_exists"
        elif message == "password too long":
            code = "password_too_long"
        else:
            code = "invalid_registration"
        return JSONResponse(status_code=400, content={"status": "error", "message": message, "code": code})


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return format_response({"user": current_user.dict()})
