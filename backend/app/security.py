"""
Phone + OTP -> JWT.

OTP delivery is mocked (fixed dev code, returned in the response so the
frontend can autofill it and logged server-side) — wire a real SMS
provider (MSG91, Twilio Verify) before taking real customer traffic.
Set JWT_SECRET as a real secret in Render's environment variables;
the default here is for local dev only.
"""
import os
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# IS_LOCAL is True only on your own laptop. Render sets the RENDER env var, so a deployed app is never "local".
IS_LOCAL = os.getenv("ENV", "dev").lower() == "dev" and not os.getenv("RENDER")


def _secret(name: str, dev_value: str, what: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    if IS_LOCAL:
        return dev_value
    print(f"[WARN] {name} is not set. Using a random temporary value ({what}). Set {name} in the Render dashboard.")
    return secrets.token_urlsafe(48)


JWT_SECRET = _secret("JWT_SECRET", "dev-secret-change-me-in-render-env-vars", "logins reset on every restart")
ADMIN_KEY = _secret("ADMIN_KEY", "dev-admin-key", "admin endpoints stay locked until you set it")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/verify-otp", auto_error=False)


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def require_role(*roles: str):
    def dependency(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted for this role")
        return user

    return dependency


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """Ops-only endpoints (create/verify providers). Send header X-Admin-Key."""
    if not x_admin_key or not secrets.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin key required")
