from sqlalchemy.orm import Session
from . import models
from typing import Optional


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, email: str, hashed_password: str, role: str = "user") -> models.User:
    db_user = models.User(username=username, email=email, hashed_password=hashed_password, role=role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
