"""FastAPI entrypoint: builds the app, registers middleware and routers."""
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.middleware.request_id import RequestIdMiddleware
from app.routers import auth as auth_router
from app.routers import chat as chat_router
from app.routers import feedback as feedback_router
from app.routers import me as me_router

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.include_router(auth_router.router)
app.include_router(me_router.router)
app.include_router(chat_router.router)
app.include_router(feedback_router.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe used by Docker/Kubernetes."""
    return {"status": "ok", "environment": settings.environment}


@app.get("/health/db", tags=["system"])
def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness probe: confirms the API can talk to Postgres."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}