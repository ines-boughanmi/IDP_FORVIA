from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from . import models


# ── Users ──────────────────────────────────────────────────────────────────────

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(
    db: Session, username: str, email: str, hashed_password: str, role: str = "user"
) -> models.User:
    db_user = models.User(
        username=username, email=email, hashed_password=hashed_password, role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ── Conversations ─────────────────────────────────────────────────────────────

def create_conversation(db: Session, user_id: int, title: str) -> models.Conversation:
    conv = models.Conversation(user_id=user_id, title=title[:200])
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversations(db: Session, user_id: int) -> List[models.Conversation]:
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == user_id)
        .order_by(models.Conversation.updated_at.desc())
        .all()
    )


def get_conversation(
    db: Session, conv_id: int, user_id: int
) -> Optional[models.Conversation]:
    return (
        db.query(models.Conversation)
        .filter(
            models.Conversation.id == conv_id,
            models.Conversation.user_id == user_id,
        )
        .first()
    )


def touch_conversation(db: Session, conv: models.Conversation):
    conv.updated_at = datetime.utcnow()
    db.commit()


def delete_conversation(db: Session, conv_id: int, user_id: int) -> bool:
    conv = get_conversation(db, conv_id, user_id)
    if not conv:
        return False
    db.delete(conv)
    db.commit()
    return True


def delete_all_conversations(db: Session, user_id: int) -> int:
    rows = (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == user_id)
        .all()
    )
    count = len(rows)
    for c in rows:
        db.delete(c)
    db.commit()
    return count


# ── Messages ──────────────────────────────────────────────────────────────────

def add_message(
    db: Session,
    conv_id: int,
    role: str,
    content: str,
    sources: Optional[List[str]] = None,
    confidence: Optional[float] = None,
) -> models.ConversationMessage:
    msg = models.ConversationMessage(
        conversation_id=conv_id,
        role=role,
        content=content,
        sources=json.dumps(sources or []),
        confidence=confidence,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
