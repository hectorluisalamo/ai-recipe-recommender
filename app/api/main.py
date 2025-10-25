from __future__ import annotations
import os, time, uuid
from dotenv import load_dotenv
load_dotenv()

PG_URL = os.getenv('PG_URL')

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
ENABLE_EMBEDDINGS = os.getenv("ENABLE_EMBEDDINGS", "0") == "1"
if ENABLE_EMBEDDINGS:
    from app.ranker.embeddings import warmup_retry
else:
    warmup_model_only = warmup_retry = None
from fastapi.middleware.cors import CORSMiddleware
import structlog
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routers.system import router as system_router
from app.api.routers.catalog import router as catalog_router
from app.api.routers.recommend import router as recommend_router

# logging
structlog.configure(
    processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(20),
)
log = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        import asyncio
        asyncio.get_event_loop().run_in_executor(None, warmup_retry, 10)
    except Exception:
        pass
    yield

app = FastAPI(
    title='AI Recipe Recommender',
    version='0.0.6',
    description='Top-K recipe recommendations (EN/ES) with brief reasons.',
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint='/metrics')

DEFAULT_ORIGINS = [
    'http://localhost', 'http://127.0.0.1',
    'http://localhost:3000', 'http://127.0.0.1:3000',
    'http://localhost:8501', 'http://127.0.0.1:8501',  # Streamlit local
]
env_origins = os.getenv('CORS_ALLOW_ORIGINS', '')
allowed = [o.strip() for o in env_origins.split(',') if o.strip()] or DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.middleware("http")
async def reqctx(request: Request, call_next):
    rid = str(uuid.uuid4())[:8]
    request.state.request_id = rid
    t0 = time.perf_counter()
    try:
        resp = await call_next(request)
        status = resp.status_code
        return resp
    finally:
        ms = int((time.perf_counter() - t0) * 1000)
        log.info("request_done", request_id=rid, path=request.url.path, method=request.method, status=status if "status" in locals() else "?", latency_ms=ms)


# include routers
app.include_router(system_router)
app.include_router(catalog_router)
app.include_router(recommend_router)
