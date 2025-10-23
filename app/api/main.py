from __future__ import annotations
from typing import List, Optional
try:
    from typing import Literal
except Exception:
    from typing_extensions import Literal

from fastapi import FastAPI
import os
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routers.system import router as system_router
from app.api.routers.catalog import router as catalog_router
from app.api.routers.recommend import router as recommend_router

app = FastAPI(title='AI Recipe Recommender', version='0.0.3')

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

DEFAULT_ORIGINS = [
    "http://localhost", "http://127.0.0.1",
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:8501", "http://127.0.0.1:8501",  # Streamlit local
]
env_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
allowed = [o.strip() for o in env_origins.split(",") if o.strip()] or DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# attach SlowAPI global handler
app.state.limiter = getattr(recommend_router, 'limiter', None)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# include routers
app.include_router(system_router)
app.include_router(catalog_router)
app.include_router(recommend_router)
