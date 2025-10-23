Title: AI Recipe Recommender

Problem
People know ingredients/diets/cuisines but waste time finding fitting recipes.

Users
Beginners–intermediate home cooks; bilingual (EN/ES/Spanglish) queries.

In-Scope (V1)
Free-text query; diet filter; Top-K results; brief “reasons”; EN/ES detection.

Out-of-Scope (V1)
User profiles, nutrition macros, shopping lists, scraping protected sites, paid APIs.

Success Metrics
- Accuracy: Prec@5 ≥ 0.60; MRR tracked.
- Latency: p50 ≤ 100 ms, p95 ≤ 300 ms at ~1k recipes.
- Cost: ≤ $10/mo infra.
- Uptime: ≥ 99% weekly.

Constraints
Solo dev; zero-ops infra; lawful, permissively licensed data; no PII.

APIs (sketch)
GET /health -> {status, version}
POST /recommend -> {results: [{id,title,reasons[],score,url}], latency_ms, used_model}
POST /feedback -> {ok}
POST /catalog/ingest (admin) -> upsert recipes

Risks & Mitigations
- Data quality/licensing -> use permissive datasets; keep provenance notes.
- Bilingual edge cases -> normalize, detect lang; test EN/ES queries in gold set.
- Latency spikes -> precompute TF-IDF; warm load; simple caching later.
- Scope creep -> DOD + metrics gate; roadmap V2 for embeddings.

Milestones
M1 Baselines + eval; M2 API + demo; M3 Deploy + CI + metrics; M4 Case study.

Definition of Done
Deployed API + Streamlit demo; metrics table; tests/CI green; case study + mini model card.
