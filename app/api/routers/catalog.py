from fastapi import APIRouter
from typing import Optional
from app.db.repo import get_recipe_count, list_recipes

router = APIRouter(prefix='/catalog', tags=['catalog'])

@router.get('/count')
def catalog_count():
    return {'count': get_recipe_count()}

@router.get('/sample')
def catalog_sample(diet: Optional[str] = 'none', limit: int = 5):
    return {'items': list_recipes(diet=diet, limit=limit)}
