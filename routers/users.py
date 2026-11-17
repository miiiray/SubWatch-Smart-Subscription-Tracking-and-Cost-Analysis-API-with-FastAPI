"""
routers/users.py — Kullanıcı endpoint'leri.
"""
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from database import SessionDep
from models import User, UserCreate

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=User, status_code=201)
def create_user(user_in: UserCreate, session: SessionDep):
    # Aynı e-posta ile ikinci kayıt olmasın
    existing = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı.")

    user = User.model_validate(user_in)
    session.add(user)
    session.commit()
    session.refresh(user)   # veritabanının verdiği id'yi al
    return user


@router.get("", response_model=list[User])
def list_users(session: SessionDep):
    return session.exec(select(User)).all()


@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    return user
