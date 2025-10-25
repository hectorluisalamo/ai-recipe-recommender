import asyncio, time
import structlog

from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from app.api.schemas import RecommendRequest, RecommendResponse, RecipeOut, ModelName
    
from app.metrics.prom import REQUESTS, ERRORS, LATENCY
from app.ranker.tfidf import TfidfIndex
from app.ranker.baselines import recommend_popularity, recommend_keyword
from app.ranker.embeddings import recommend_embed

log = structlog.get_logger()
router = APIRouter(prefix='/recommend', tags=['recommend'])

async def _recommend_core(req: RecommendRequest, request:Request) -> RecommendResponse:
    t0 = time.perf_counter()
    REQUESTS.labels(endpoint='recommend', model=req.model, diet=req.diet).inc()

    async def _run():
        req_id = getattr(getattr(request, 'state', object()), 'request_id', 'n/a')
        if req.model == 'embed':
            try:
                results_raw = recommend_embed(req.query, req.diet, req.must_include, req.k)
                used = 'embed_miniLM_multilingual_v1'
            except Exception as e:
                # soft-fail to keyword baseline
                ERRORS.labels(type='embed_fallback').inc()
                log.error("embed_failed_fallback_kw", request_id=req_id, error=str(e))
                results_raw = recommend_keyword(req.query, req.diet, req.must_include, req.k)
                used = "embed_fallback_kw"
        elif req.model == 'tfidf':
            global _TFIDF_INDEX
            try:
                _TFIDF_INDEX
            except NameError:
                _TFIDF_INDEX = TfidfIndex.load()
            results_raw = _TFIDF_INDEX.recommend(req.query, req.diet, req.must_include, req.k)
            used = 'tfidf_v1'
        elif req.model == 'kw':
            results_raw = recommend_keyword(req.query, req.diet, req.must_include, req.k)
            used = 'kw_baseline_v1'
        else:
            results_raw = recommend_popularity(req.query, req.diet, req.must_include, req.k)
            used = 'pop_baseline_v1'
        return used, results_raw

    try:
        used, results_raw = await asyncio.wait_for(_run(), timeout=5.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail={'error': 'timeout', 'details': 'ranker timed out'})
    except ValidationError as ve:
        ERRORS.labels(type='invalid_input').inc()
        raise HTTPException(status_code=400, detail={'error': 'invalid_input', 'details': str(ve)})
    except HTTPException:
        raise
    except Exception as e:
        ERRORS.labels(type='internal').inc()
        log.error('recommend_error', error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail={'error': 'internal_error', 'details': 'unexpected error'})

    latency_ms = int((time.perf_counter() - t0) * 1000)
    LATENCY.labels(endpoint='recommend', model=req.model).observe(latency_ms / 1000.0)
    
    results = [RecipeOut(**r) for r in results_raw]
    return RecommendResponse(results=results, latency_ms=latency_ms, used_model=used)

@router.post('', response_model=RecommendResponse)
async def recommend(req: RecommendRequest, request: Request) -> RecommendResponse:
    return await _recommend_core(req, request)