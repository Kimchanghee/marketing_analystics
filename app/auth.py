from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import HTTPException, Request, Response, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

logger = logging.getLogger(__name__)

# bcrypt 초기화 시 발생할 수 있는 에러 무시
try:
    import bcrypt
    # bcrypt 버전 확인 및 미리 로드
    logger.info(f"bcrypt loaded successfully")
except Exception as e:
    logger.warning(f"bcrypt import warning: {e}")

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,
)
settings = get_settings()


class AuthManager:
    def __init__(self) -> None:
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.expire_minutes = settings.access_token_expire_minutes

    def _truncate_password(self, password: str) -> str:
        """
        bcrypt는 72바이트까지만 처리할 수 있습니다.
        긴 비밀번호를 72바이트로 자릅니다.
        """
        password_bytes = password.encode('utf-8')
        if len(password_bytes) <= 72:
            return password
        # 72바이트로 자르되, UTF-8 문자가 깨지지 않도록 처리
        return password_bytes[:72].decode('utf-8', errors='ignore')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        truncated_password = self._truncate_password(plain_password)
        try:
            return pwd_context.verify(truncated_password, hashed_password)
        except (ValueError, Exception) as exc:
            # passlib may raise for legacy hashes or edge cases – treat as failure rather than 500
            logger.warning(f"Password verification error: {exc}")
            if "password cannot be longer than 72 bytes" in str(exc):
                # best-effort retry with hard truncation for legacy data
                hard_truncated = truncated_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
                try:
                    return pwd_context.verify(hard_truncated, hashed_password)
                except Exception as retry_exc:
                    logger.error(f"Password verification retry failed: {retry_exc}")
                    return False
            # bcrypt backend 초기화 에러인 경우, 직접 bcrypt로 검증 시도
            try:
                import bcrypt as bcrypt_lib
                return bcrypt_lib.checkpw(truncated_password.encode('utf-8'), hashed_password.encode('utf-8'))
            except Exception as bcrypt_exc:
                logger.error(f"Direct bcrypt verification failed: {bcrypt_exc}")
                return False

    def hash_password(self, password: str) -> str:
        truncated_password = self._truncate_password(password)
        return pwd_context.hash(truncated_password)

    def create_access_token(self, subject: str, expires_delta: Optional[timedelta] = None) -> str:
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.expire_minutes))
        to_encode = {"sub": subject, "exp": expire}
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
        subject: Optional[str] = payload.get("sub")
        if subject is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return subject

    def set_login_cookie(self, response: Response, token: str) -> None:
        # Cloud Run uses HTTPS, so secure should be True in production
        is_production = settings.is_production
        response.set_cookie(
            key="session",
            value=token,
            httponly=True,
            max_age=self.expire_minutes * 60,
            secure=is_production,  # True for HTTPS (production), False for local development
            samesite="lax",
        )

    def clear_login_cookie(self, response: Response) -> None:
        response.delete_cookie("session")

    def extract_token(self, request: Request) -> Optional[str]:
        return request.cookies.get("session")


auth_manager = AuthManager()
