import os, pathlib, sqlite3
from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Literal

import psycopg

from app.metrics.prom import render_prometheus

router = APIRouter(prefix='', tags=['system'])

class HealthOut(BaseModel):
    status: Literal['ok']
    version: str

@router.get('/', include_in_schema=False)
def root():
    return {'message': 'See the interactive docs at /docs'}

@router.get('/debug')
def debug():
    report = {'sqlite': {}, 'pgvector': {}, 'tfidf': {}}
    
    # SQLite info
    db_path = os.getenv('DB_PATH', 'data/recipes.db')
    p = pathlib.Path(db_path)
    report['sqlite']['path'] = str(p)
    report['sqlite']['exists'] = p.exists()
    try:
        with sqlite3.connect(db_path) as conn:
            row = conn.execute('SELECT COUNT(*) FROM recipes').fetchone()
            report['sqlite']['recipes_count'] = int(row[0])
    except Exception as e:
        report['sqlite']['error'] = str(e)
        
    # TF_IDF info
    mdir = pathlib.Path('models')
    report['tfidf']['vectorizer'] = (mdir / 'vectorizer.joblib').exists()
    report['tfidf']['matrix'] = (mdir / 'tfidf_matrix.npz').exists()
    report['tfidf']['rows'] = (mdir / 'rows.joblib').exists()
    
    # pgvector info
    pg_url = os.getenv('PG_URL', '')
    report['pgvector']['PG_URL_set'] = bool(pg_url)
    if pg_url:
        try:
            with psycopg.connect(pg_url) as conn, conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.recipes_embeddings')")
                report['pgvector']['table_exists'] = bool(cur.fetchone()[0])
                cur.execute('SELECT COUNT(*) FROM recipes_embeddings')
                report['pgvector']['embeddings_count'] = int(cur.fetchone()[0])
        except Exception as e:
            report['pgvector']['error'] = str(e)
    return {'ok': True, 'report': report}

@router.get('/health', response_model=HealthOut)
def health():
    from app.api.main import app
    return HealthOut(status='ok', version=app.version)

@router.get('/metrics', include_in_schema=False)
def metrics():
    body, ctype = render_prometheus()
    return Response(content=body, media_type=ctype)
