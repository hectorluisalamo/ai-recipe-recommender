from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Literal

from app.metrics.prom import render_prometheus

router = APIRouter(prefix='', tags=['system'])

class HealthOut(BaseModel):
    status: Literal['ok']
    version: str

@router.get('/', include_in_schema=False)
def root():
    return {'message': 'See the interactive docs at /docs'}

@router.get('/health', response_model=HealthOut)
def health():
    from app.api.main import app
    return HealthOut(status='ok', version=app.version)

@router.get('/metrics', include_in_schema=False)
def metrics():
    body, ctype = render_prometheus()
    return Response(content=body, media_type=ctype)
