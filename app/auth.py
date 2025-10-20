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

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

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
        response.set_cookie(
            key="session",
            value=token,
            httponly=True,
            max_age=self.expire_minutes * 60,
            secure=False,
            samesite="lax",
        )

    def clear_login_cookie(self, response: Response) -> None:
        response.delete_cookie("session")

    def extract_token(self, request: Request) -> Optional[str]:
        return request.cookies.get("session")


auth_manager = AuthManager()
