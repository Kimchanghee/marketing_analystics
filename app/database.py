from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

settings = get_settings()
# PostgreSQL 연결 (SQLite check_same_thread 옵션 제거)
engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI Depends용 세션 제너레이터"""
    with Session(engine) as session:
        yield session


@contextmanager
def session_context() -> Iterator[Session]:
    """일반 코드에서 with 블록용 컨텍스트 매니저"""
    with Session(engine) as session:
        yield session
