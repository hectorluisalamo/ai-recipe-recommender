from typing import List, Literal, Optional, Annotated
import asyncio, time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, StringConstraints, ValidationError
    
from app.metrics.prom import REQUESTS, ERRORS, LATENCY
from app.ranker.tfidf import TfidfIndex
from app.ranker.baselines import recommend_popularity, recommend_keyword

router = APIRouter(prefix='/recommend', tags=['recommend'])

Diet = Literal['none','keto','vegan','vegetarian','gluten_free']
Lang = Literal['auto','en','es']
ModelName = Literal['pop','kw','tfidf']

class RecommendRequest(BaseModel):
    query: Annotated[str, Field(strip_whitespace=True, min_length=2, max_length=200)]
    diet: Diet = 'none'
    must_include: List[Annotated[str, Field(strip_whitespace=True, min_length=1, max_length=40)]] = Field(default_factory=list, max_length=5)
    k: int = Field(default=5, ge=1, le=10)
    language: Lang = 'auto'
    model: ModelName = 'kw'

class RecipeOut(BaseModel):
    id: str
    title: str
    reasons: List[str]
    score: float
    url: Optional[str] = None

class RecommendResponse(BaseModel):
    results: List[RecipeOut]
    latency_ms: int
    used_model: str

async def _recommend_core(req: RecommendRequest) -> RecommendResponse:
    t0 = time.perf_counter()
    REQUESTS.labels(endpoint='recommend', model=req.model, diet=req.diet).inc()

    async def _run():
        if req.model == 'tfidf':
            global _TFIDF_INDEX
            try:
                _TFIDF_INDEX
            except NameError:
                _TFIDF_INDEX = TfidfIndex.load('v1')
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
        used, results_raw = await asyncio.wait_for(_run(), timeout=2.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail='ranker timed out')
    except ValidationError as e:
        ERRORS.labels(type='invalid_input').inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        ERRORS.labels(type='internal').inc()
        raise HTTPException(status_code=500, detail='internal server error')

    latency_ms = int((time.perf_counter() - t0) * 1000)
    LATENCY.labels(endpoint='recommend', model=req.model).observe(latency_ms / 1000.0)
    
    results = [RecipeOut(**r) for r in results_raw]
    return RecommendResponse(results=results, latency_ms=latency_ms, used_model=used)

@router.post('')
async def recommend(req: RecommendRequest, request: Request) -> RecommendResponse:
    return await _recommend_core(req)