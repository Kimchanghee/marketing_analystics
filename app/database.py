import time
from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

settings = get_settings()
# PostgreSQL 연결 (SQLite check_same_thread 옵션 제거)
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10} if "postgresql" in settings.database_url else {},
)


def init_db(max_retries: int = 3, retry_delay: int = 2) -> None:
    """Initialize database with retry logic for Cloud Run deployments"""
    for attempt in range(max_retries):
        try:
            SQLModel.metadata.create_all(engine)
            print(f"Database initialized successfully on attempt {attempt + 1}")
            return
        except Exception as e:
            print(f"Database initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Database initialization failed.")
                raise


def get_session() -> Iterator[Session]:
    """FastAPI Depends용 세션 제너레이터"""
    with Session(engine) as session:
        yield session


@contextmanager
def session_context() -> Iterator[Session]:
    """일반 코드에서 with 블록용 컨텍스트 매니저"""
    with Session(engine) as session:
        yield session
