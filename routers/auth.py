from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select

from database import SessionDep
from models import AuthToken, User, UserLogin, UserPublic, UserRegister
from security import CurrentUser, bearer, create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


def to_public(user: User) -> UserPublic:
    return UserPublic(id=user.id, name=user.name, email=user.email, monthly_budget=user.monthly_budget)


@router.post("/register", response_model=UserPublic, status_code=201)
def register(data: UserRegister, session: SessionDep):
    email = data.email.strip().lower()
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı.")

    user = User(
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        monthly_budget=data.monthly_budget,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return to_public(user)


@router.post("/login")
def login(data: UserLogin, session: SessionDep):
    email = data.email.strip().lower()
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    token = create_token(session, user.id)
    return {"access_token": token, "token_type": "bearer", "user": to_public(user)}


@router.post("/logout")
def logout(
    user: CurrentUser,
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
):
    auth = session.get(AuthToken, credentials.credentials)
    if auth:
        session.delete(auth)
        session.commit()
    return {"message": "Çıkış yapıldı."}


@router.get("/me", response_model=UserPublic)
def me(user: CurrentUser):
    return to_public(user)