from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from routers import auth, insights, subscriptions
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

# Tarayıcı site dosyalarını hafızada tutmasın: kod değişince hep en yeni hali gelsin
@app.middleware("http")
async def no_cache_for_site(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path in ("/", "/app") or path.startswith("/static"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/app", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")
