import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import SessionDep
from models import AuthToken, User

TOKEN_DAYS = 7
ITERATIONS = 100_000

bearer = HTTPBearer(auto_error=False)


# ---------- 1) ŞİFRE ----------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, saved_digest = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return hmac.compare_digest(digest.hex(), saved_digest)


# ---------- 2) TOKEN ----------
def create_token(session, user_id: int) -> str:
    token = secrets.token_hex(32)
    auth = AuthToken(
        token=token,
        user_id=user_id,
        expires_at=datetime.now() + timedelta(days=TOKEN_DAYS),
    )
    session.add(auth)
    session.commit()
    return token


# ---------- 3) GİRİŞ YAPAN KİM? ----------
def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Giriş yapmalısın.")

    auth = session.get(AuthToken, credentials.credentials)
    if auth is None:
        raise HTTPException(status_code=401, detail="Geçersiz oturum, tekrar giriş yap.")

    if auth.expires_at < datetime.now():
        session.delete(auth)
        session.commit()
        raise HTTPException(status_code=401, detail="Oturum süresi doldu, tekrar giriş yap.")

    user = session.get(User, auth.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]