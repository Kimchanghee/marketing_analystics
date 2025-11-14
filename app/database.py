import time
from contextlib import contextmanager
from typing import Iterator
import logging

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# PostgreSQL 연결 (SQLite check_same_thread 옵션 제거)
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10} if "postgresql" in settings.database_url else {},
)

# Track if database has been initialized
_db_initialized = False


class DatabaseInitializationError(Exception):
    """Raised when database cannot be initialized."""
    pass


def init_db(max_retries: int = 2, retry_delay: int = 1) -> None:
    """Initialize database with retry logic for Cloud Run deployments

    Raises:
        DatabaseInitializationError: If database initialization fails after all retries
    """
    global _db_initialized

    if _db_initialized:
        return

    for attempt in range(max_retries):
        try:
            logger.info(f"Database initialization attempt {attempt + 1}/{max_retries}")
            SQLModel.metadata.create_all(engine)
            logger.info(f"Database initialized successfully on attempt {attempt + 1}")
            _db_initialized = True
            return
        except Exception as e:
            logger.error(f"Database initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} second(s)...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Database initialization failed.")
                raise DatabaseInitializationError(
                    f"Failed to initialize database after {max_retries} attempts: {e}"
                ) from e


def get_session() -> Iterator[Session]:
    """FastAPI Depends용 세션 제너레이터 - lazy initialization

    Raises:
        DatabaseInitializationError: If database initialization fails
    """
    # Initialize database on first access (fail-fast)
    if not _db_initialized:
        init_db()

    with Session(engine) as session:
        yield session


@contextmanager
def session_context() -> Iterator[Session]:
    """일반 코드에서 with 블록용 컨텍스트 매니저 - lazy initialization

    Raises:
        DatabaseInitializationError: If database initialization fails
    """
    # Initialize database on first access (fail-fast)
    if not _db_initialized:
        init_db()

    with Session(engine) as session:
        yield session
