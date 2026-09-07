from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.api import router
from app.routers.extras import router as extras_router
from app.seed.bootstrap import init_db_and_seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db_and_seed()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
app.include_router(extras_router, prefix="/api")


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/docs", "api": "/api/health"}
