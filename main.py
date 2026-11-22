from contextlib import asynccontextmanager
from pathlib import Path
from routers import auth, subscriptions
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import create_db_and_tables


STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="SubWatch API",
    description="Smart Subscription Tracking and Cost Analysis API",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(subscriptions.router)   
app.include_router(insights.router)        

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "login.html")