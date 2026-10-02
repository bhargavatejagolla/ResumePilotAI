from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, generate
from app.config import get_settings
from app.core.logging import configure_logging
from app.services.embedding_service import _load as load_embedder
from app.layers.l2_candidate import build_index

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load embedding model & ensure index is warmed at startup
    try:
        load_embedder()
    except Exception:
        pass

    try:
        build_index(force_rebuild=False)
    except Exception:
        pass
    yield


app = FastAPI(
    title="ResumePilot AI",
    version="0.1.0",
    description="AI Resume Intelligence Engine",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(generate.router, tags=["generate"])
