"""
main.py — Uygulamanın giriş noktası.
Çalıştırmak için:  fastapi dev main.py
  Web sitesi  → http://127.0.0.1:8000
  API dokümanı → http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import create_db_and_tables
from routers import insights, subscriptions, users

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()   # uygulama açılırken tablolar yoksa oluştur
    yield


app = FastAPI(
    title="SubWatch API",
    description="Smart Subscription Tracking and Cost Analysis API",
    version="1.0.0",
    lifespan=lifespan,
)

# Router'ları uygulamaya bağla
app.include_router(users.router)
app.include_router(subscriptions.router)
app.include_router(insights.router)

# Web sitesi dosyaları (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")
