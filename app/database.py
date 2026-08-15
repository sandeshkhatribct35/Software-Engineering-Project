"""Database engine, session factory and the request-scoped session dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models.base import Base

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.echo_sql,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for the lifetime of one request.

    FastAPI injects this into every router that needs persistence; the session
    is always closed, including when the request handler raises.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create any missing tables from the ORM metadata.

    The project deliberately has no migration tool (GUIDE §11.4): the schema is
    the single source of truth and is created at application startup.
    """
    import app.models  # noqa: F401  # registers every mapped class on Base.metadata

    Base.metadata.create_all(bind=engine)
