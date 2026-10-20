"""Database engine, session factory, and base model."""

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from hotel_booking.config import get_settings


class Base(DeclarativeBase):
    """Base declarative class for all ORM models."""

    pass


def create_db_engine(db_url: str | None = None) -> Any:
    """Create and configure SQLAlchemy engine."""
    url = db_url or get_settings().database_url
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args)


engine = create_db_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing database session to endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_to_use: Any = None) -> None:
    """Initialize database tables."""
    target_engine = engine_to_use or engine
    Base.metadata.create_all(bind=target_engine)
