import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import __version__
from .config import settings
from .db import get_db
from .routers import tickets

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger("resolvedesk")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema is owned by Alembic (see the Dockerfile entrypoint). Nothing to create here.
    logger.info("ResolveDesk API %s starting in %s mode", __version__, settings.environment)
    yield
    logger.info("ResolveDesk API shutting down")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="IT helpdesk ticketing API - DevOps capstone project.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/health", "/ready"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(tickets.router)


@app.get("/", tags=["meta"])
def root():
    return {
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health():
    """Liveness probe: the process is up and can serve HTTP."""
    return {"status": "UP"}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)):
    """Readiness probe: the database is reachable, so traffic can be routed here."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("Readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "READY", "database": "ok"}
