from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import HTTPException, Request, Response, status
from jose import JWTError, jwt
import bcrypt

from .config import get_settings

logger = logging.getLogger(__name__)
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
        """bcrypt를 직접 사용하여 비밀번호 검증"""
        truncated_password = self._truncate_password(plain_password)
        try:
            # bcrypt는 bytes를 요구함
            password_bytes = truncated_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as exc:
            logger.error(f"Password verification failed: {exc}")
            return False

    def hash_password(self, password: str) -> str:
        """bcrypt를 직접 사용하여 비밀번호 해싱"""
        truncated_password = self._truncate_password(password)
        try:
            # bcrypt.gensalt(rounds=10)로 salt 생성 - 보안과 성능의 균형
            # rounds=10: ~50-100ms (기본 12보다 3-4배 빠르면서도 안전)
            password_bytes = truncated_password.encode('utf-8')
            hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=10))
            return hashed.decode('utf-8')
        except Exception as exc:
            logger.error(f"Password hashing failed: {exc}")
            raise

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


# Helper functions for backward compatibility and convenience
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token with custom data payload.
    Used for state tokens in OAuth flows.
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    """
    Decode a JWT token and return the payload.
    Used for state tokens in OAuth flows.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
