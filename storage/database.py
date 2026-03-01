from __future__ import annotations

import os
from contextlib import contextmanager
from functools import lru_cache
import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


Base = declarative_base()
logger = logging.getLogger(__name__)


def _resolve_database_url() -> str:
    raw = os.getenv("DATABASE_URL", "sqlite:///./scd.db")
    if raw.startswith("postgresql://"):
        raw = raw.replace("postgresql://", "postgresql+psycopg://", 1)

    running_in_docker = os.getenv("RUNNING_IN_DOCKER", "0") == "1" or Path("/.dockerenv").exists()

    if "@db:" in raw and not running_in_docker:
        logger.warning("DATABASE_URL points to docker host 'db' outside container; falling back to sqlite")
        return "sqlite:///./scd.db"

    return raw


@lru_cache(maxsize=1)
def _get_engine():
    database_url = _resolve_database_url()
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, pool_pre_ping=True, future=True, connect_args=connect_args)


@lru_cache(maxsize=1)
def _get_sessionmaker():
    return sessionmaker(bind=_get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope() -> Session:
    session = _get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database() -> None:
    """Ensure models are imported so Base.metadata is complete.

    Schema creation is handled by Alembic migrations (``alembic upgrade head``)
    which runs automatically via docker-entrypoint.sh.  The ``create_all``
    call is kept as a safety-net for local development / SQLite usage.
    """
    from storage import models  # noqa: F401

    engine = _get_engine()
    url = str(engine.url)
    # Only use create_all for SQLite (local dev); Alembic handles Postgres
    if url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
