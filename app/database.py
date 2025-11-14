import time
from contextlib import contextmanager
from typing import Iterator
import logging

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# PostgreSQL 연결 - 프로덕션 환경 최적화
# 동시 접속자 500-1000명 대응 가능한 연결 풀 설정
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,  # 연결 유효성 자동 확인
    pool_size=20,  # 기본 연결 풀 크기 (기본값: 5)
    max_overflow=40,  # 피크 시간 추가 연결 수 (총 60개 동시 연결 가능)
    pool_timeout=30,  # 연결 대기 최대 시간 (초)
    pool_recycle=3600,  # 1시간마다 연결 재생성 (장시간 유휴 연결 방지)
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30초 쿼리 타임아웃
    } if "postgresql" in settings.database_url else {},
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
