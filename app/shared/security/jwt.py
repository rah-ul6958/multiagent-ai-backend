from datetime import datetime, timedelta
from typing import Optional

import jwt

from app.core.config import settings
from app.core.exceptions import AuthenticationError


def create_access_token(user_id: str, role: str = "user") -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": datetime.utcnow()
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    payload = decode_token(token)
    if payload.get("type") != token_type:
        raise AuthenticationError(f"Invalid token type: expected {token_type}")
    return payload.get("sub")
