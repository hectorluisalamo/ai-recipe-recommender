from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, conint, constr

from app.db.repo import get_recipe_count, list_recipes
from app.ranker.baselines import recommend_popularity, recommend_keyword

# ---- App ----
app = FastAPI(
    title="AI Recipe Recommender",
    version="0.0.2",
    description="Top-K recipe recommendations (EN/ES) with brief reasons.",
)

# CORS (dev-friendly: allow localhost origins; tighten later in deploy)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---
Diet = Literal["none", "keto", "vegan", "vegetarian", "gluten_free"]
Lang = Literal["auto", "en", "es"]
ModelName = Literal["pop","kw"]

class RecommendRequest(BaseModel):
    query: constr(strip_whitespace=True, min_length=2)
    diet: Diet = "none"
    must_include: List[str] = Field(default_factory=list)
    k: conint(ge=1, le=10) = 5
    language: Lang = "auto"
    model: ModelName = "pop"

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

class HealthOut(BaseModel):
    status: Literal["ok"]
    version: str

# ---- Endpoints ----
@app.get("/", include_in_schema=False)
def root():
    return {"message": "See the interactive docs at /docs"}

@app.get("/health", response_model=HealthOut, tags=["system"])
def health() -> HealthOut:
    return HealthOut(status="ok", version=app.version)

@app.get("/catalog/count", tags=["catalog"])
def catalog_count() -> dict:
    return {"count": get_recipe_count()}

@app.get("/catalog/sample", tags=["catalog"])
def catalog_sample(diet: Diet = "none", limit: int = 5) -> dict:
    return {"items": list_recipes(diet=diet, limit=limit)}

@app.post("/recommend", response_model=RecommendResponse, tags=["recommend"])
def recommend(req: RecommendRequest) -> RecommendResponse:
    t0 = time.perf_counter()

    # ---- ROUTING BY MODEL ----
    if req.model == "kw":
        results_raw = recommend_keyword(req.query, req.diet, req.must_include, req.k)
        used = "kw_baseline_v1"
    else:
        results_raw = recommend_popularity(req.query, req.diet, req.must_include, req.k)
        used = "pop_baseline_v1"

    latency_ms = int((time.perf_counter() - t0) * 1000)
    results = [RecipeOut(**r) for r in results_raw]
    return RecommendResponse(results=results, latency_ms=latency_ms, used_model=used)