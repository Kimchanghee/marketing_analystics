from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request, Response, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
        return pwd_context.verify(truncated_password, hashed_password)

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
