from __future__ import annotations
from typing import Any, List, Dict
import os, time
from psycopg_pool import ConnectionPool
from sentence_transformers import SentenceTransformer
from functools import lru_cache
from fastapi import HTTPException
from app.db.repo import list_recipes_by_ids

MODEL_NAME = os.environ.get('EMBED_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
TOPN_PG = int(os.environ.get('EMBED_TOPN', '20'))

# --- Singletons ---
_model: SentenceTransformer | None = None
_pool: ConnectionPool | None = None
_warmed_up = False

def _pg_url() -> str:
    pg = os.getenv('PG_URL')
    if not pg:
        raise RuntimeError('PG_URL not set')
    return pg

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
        _model.max_seq_length = 128
        _model.encode(['warmup'], normalize_embeddings=True)
    return _model

def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(conninfo=_pg_url(), min_size=1, max_size=5)
    return _pool

def _vec_literal(vec: List[float]) -> str:
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

def warmup_once() -> None:
    global _warmed_up
    if _warmed_up:
        return
    try:
        m = _get_model()
        qvec = m.encode(['warmup'], normalize_embeddings=True)[0].tolist()
        lit = _vec_literal(qvec)
        pool = _get_pool()
        with pool.connection() as conn, conn.cursor() as cur:
            # make sure planner uses ANN index & analyze stats
            cur.execute('SET ivfflat.probe = 10;')
            cur.execute('ANALYZE recipes_embeddings;')
            # test query (handles empty table too)
            cur.execute('SELECT recipe_id FROM recipes_embeddings ORDER BY embedding <-> %s::vector LIMIT 1;', (lit,))
            _ = cur.fetchall()
        _warmed_up = True
    except Exception:
        return

def warmup_retry(max_wait_s: int = 10) -> None:
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        try:
            warmup_once()
            return
        except Exception:
            time.sleep(0.5)

def warmup_model_only() -> None:
    m = _get_model()
    m.encode(['warmup'], normalize_embeddings=True)
    
@lru_cache(maxsize=256)
def _encode_query(q: str):
    m = _get_model()
    return m.encode([q or ''], normalize_embeddings=True)[0].tolist()

def recommend_embed(query: str, diet: str, must_include: List[str], k: int, topn_pg: int = 50) -> List[Dict[str, Any]]:
    qvec = _encode_query(query)
    if len(qvec) != 384:
        raise HTTPException(status_code=500, detail=f'embedding dim {len(qvec)} != 384 for model {MODEL_NAME}')
    lit = _vec_literal(qvec)
    topn = topn_pg or TOPN_PG
    
    # ANN search
    ids: List[str] = []
    pool = _get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            'SELECT recipe_id FROM recipes_embeddings ORDER BY embedding <-> %s::vector LIMIT %s;',
            (lit, topn),
        )
        ids = [row[0] for row in cur.fetchall()]
        
    # hydrate & filter
    out: List[Dict[str, Any]] = []
    for r in list_recipes_by_ids(ids):
        if diet != 'none' and r.get('diet') != diet:
            continue
        if must_include:
            ing = (r.get('ingredients') or '').lower()
            if not all(m.lower() in ing for m in must_include):
                continue
        out.append({
            'id': r['id'],
            'title': r['title'],
            'reasons': ['semantic match (multilingual)', f"diet: {r.get('diet')}"],
            'score': 1.0,
            'url': r.get('url'),
        })
        if len(out) >= k:
            break
    return out