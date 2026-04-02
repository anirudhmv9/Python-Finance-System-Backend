"""
SQLAlchemy engine, session factory, and declarative base.

Session lifecycle: per-request scope via FastAPI dependency `get_db`.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


_settings = get_settings()

is_sqlite = _settings.sqlalchemy_database_uri.startswith("sqlite")

engine_kwargs = {"echo": False}
if is_sqlite:
    # SQLite is file-based; required for FastAPI's threaded request handling.
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

engine = create_engine(_settings.sqlalchemy_database_uri, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session and ensure it is closed after the request.

    Usage:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
