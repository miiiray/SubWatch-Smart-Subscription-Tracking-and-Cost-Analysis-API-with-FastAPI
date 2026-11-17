"""
database.py — SQLite bağlantısı.

  engine  → veritabanı dosyasına (subwatch.db) giden bağlantı
  session → her istekte açılan, işi bitince kapanan "çalışma oturumu"
"""
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///subwatch.db"

# check_same_thread=False → FastAPI aynı bağlantıyı farklı thread'lerde kullanabilsin
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """models.py'deki table=True sınıflarının hepsini tablo olarak oluşturur."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Her istek için bir session açar, istek bitince otomatik kapatır."""
    with Session(engine) as session:
        yield session


# Endpoint'lerde "session: SessionDep" yazınca FastAPI session'ı kendisi verir
SessionDep = Annotated[Session, Depends(get_session)]
