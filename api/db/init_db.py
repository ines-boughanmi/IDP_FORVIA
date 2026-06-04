import os

from .session import engine, Base
from ..auth.password import hash_password


def init_db(seed_admin_password: str = None, seed_user_password: str = None):
    # create tables
    Base.metadata.create_all(bind=engine)

    # seed or refresh initial users so the known credentials stay valid
    from .session import SessionLocal
    from .crud import get_user_by_username, create_user

    db = SessionLocal()
    try:
        admin_pwd = seed_admin_password or os.environ.get("P2P_ADMIN_PWD", "adminpass")
        admin = get_user_by_username(db, "admin")
        if not admin:
            create_user(db, "admin", "admin@example.com", hash_password(admin_pwd), role="admin")
        else:
            admin.email = "admin@example.com"
            admin.role = "admin"
            admin.hashed_password = hash_password(admin_pwd)
            db.commit()

        user_pwd = seed_user_password or os.environ.get("P2P_USER_PWD", "userpass")
        alice = get_user_by_username(db, "alice")
        if not alice:
            create_user(db, "alice", "alice@example.com", hash_password(user_pwd), role="user")
        else:
            alice.email = "alice@example.com"
            alice.role = "user"
            alice.hashed_password = hash_password(user_pwd)
            db.commit()
    finally:
        db.close()
