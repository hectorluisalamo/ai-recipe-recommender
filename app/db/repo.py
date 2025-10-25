from __future__ import annotations
import os
from typing import Iterable, Optional, Dict, Any, List
from sqlalchemy import create_engine, text

DB_URL = os.getenv('DB_URL', 'sqlite:///data/recipes.db')

# Note: echo=False to avoid noisy logs. Future: pool_pre_ping for other DBs.
_engine = create_engine(DB_URL, echo=False, future=True)

def get_recipe_count() -> int:
    with _engine.begin() as conn:
        (count,) = conn.execute(text('SELECT COUNT(*) FROM recipes')).one()
        return int(count)

def list_recipes(diet: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    query = 'SELECT id, title, ingredients, cuisine, diet, time_minutes, popularity, url FROM recipes'
    params = {}
    if diet and diet != 'none':
        query += ' WHERE diet = :diet'
        params['diet'] = diet
    query += ' ORDER BY popularity DESC LIMIT :limit'
    params['limit'] = limit
    with _engine.begin() as conn:
        rows = conn.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]
    
def list_recipes_by_ids(ids: List[str]) -> List[Dict[str, Any]]:
    if not ids:
        return []
    # preserve order using CASE
    placeholders = ', '.join([f':id{i}' for i,_ in enumerate(ids)])
    ordering = ' '.join([f'WHEN :id{i} THEN {i}' for i,_ in enumerate(ids)])
    params = {f'id{i}': v for i,v in enumerate(ids)}
    query = f'''
      SELECT id, title, ingredients, cuisine, diet, time_minutes, popularity, url
      FROM recipes
      WHERE id IN ({placeholders})
      ORDER BY CASE id {ordering} END
    '''
    with _engine.begin() as conn:
        rows = conn.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]
