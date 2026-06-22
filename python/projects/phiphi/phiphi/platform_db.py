"""Database."""

import contextlib
import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from phiphi import config

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base model."""


engine = create_engine(str(config.settings.SQLALCHEMY_DATABASE_URI))


def get_session() -> Generator[Session, None, None]:
    """Get the session."""
    with Session(engine) as session:
        yield session


@contextlib.contextmanager
def get_session_context() -> Generator[Session, None, None]:
    """Get the context session.

    This can't be used in a fastapi.Depends as fast api automatically adds the context manager to
    functions with a `yield`. As it says in the tip here:
    https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/#using-context-managers-in-dependencies-with-yield
    "But you don't have to use the [contextmanager] decorators for FastAPI dependencies (and you
    shouldn't)."

    Discussion here:
    https://github.com/tiangolo/fastapi/discussions/8955

    Can be used:
    with get_session_context() as session:
        ...

    Yields:
        Generator[Session, None, None]: The session.
    """
    with Session(engine) as session:
        yield session
