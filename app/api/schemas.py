import os
from typing import List, Optional, Literal, Annotated
from pydantic import BaseModel, Field, field_validator

DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'embed')

Diet = Literal["none", "keto", "vegan", "vegetarian", "gluten_free"]
Lang = Literal["auto", "en", "es"]
ModelName = Literal["pop", "kw", "tfidf", "embed"]

ItemStr = Annotated[str, Field(min_length=1, max_length=40, strip_whitespace=True)]

class RecommendRequest(BaseModel):
    query: Annotated[str, Field(strip_whitespace=True, min_length=2, max_length=200)]
    diet: Diet = 'none'
    must_include: Annotated[List[ItemStr], Field(default_factory=list, max_length=5)] = Field(default_factory=list)
    k: int = Field(default=5, ge=1, le=10)
    language: Lang = 'auto'
    model: ModelName = DEFAULT_MODEL
    
    @field_validator('query')
    @classmethod
    def _clean_query(cls, v: str) -> str:
        v = (v or '').strip()
        if len(v) < 2:
            raise ValueError('query too short')
        if len(v) > 200:
            raise ValueError('query too long')
        return v

class RecipeOut(BaseModel):
    id: str
    title: str
    reasons: List[str]
    score: float = 0.0
    url: Optional[str] = None

class RecommendResponse(BaseModel):
    results: List[RecipeOut]
    latency_ms: int
    used_model: str