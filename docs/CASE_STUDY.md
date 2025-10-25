# AI Recipe Recommender — Case Study

## Problem
Home cooks know diets/cuisines/ingredients but waste time keyword-hunting. Goal: return Top-K relevant recipes with short reasons, fast and cheap.

## Users
Beginners–intermediate home cooks. Bilingual queries (EN/ES/Spanglish).

## Design choices
- **Retrieval-first**, not personalized. Start with keyword baseline, add TF-IDF; embeddings later if metrics justify.
- **SQLite** for simplicity + Render Disk for persistence.
- **Prometheus** metrics at `/metrics` to measure latency & errors in prod-like conditions.
- **Streamlit** demo for fastest end-to-end loop.

## Data
- Seed CSV (10 rows) you own. Cleaning: lowercase, punctuation trim, normalize ingredient separators; diet labels validated.
- Future: larger licensed datasets.

## Metrics & Ablations
Summarize the table (Prec@5, MRR, p50/p95). On our toy set: `kw` ~= `tfidf`. Keep `kw` default until data grows.

## Ops (deploy/monitor)
- Dockerized FastAPI; deployed on Render (API + UI).
- Persistent DB at `/data/recipes.db`.
- Structured JSON logs (structlog) + Prometheus counters/histograms.
- Runbook: check `/health`, scrape `/metrics`, tail logs, rebuild TF-IDF artifacts after data changes.

## Incident & Fix (example)
- *Symptom:* 504 timeouts after deploy.  
- *Findings:* TF-IDF artifacts missing in container.  
- *Fix:* Run `fit_index.py` in CI and bake artifacts into image; add guard in startup to error clearly.

## Results
- Live demo reachable; p95 latency well below 300 ms at 1k docs (projected).
- CI runs `pytest` and lints; blue/green via Render redeploys.

## Next 3 improvements
1) Embed + pgvector A/B; promote only if +8–10 pts Prec@5.  
2) Implicit feedback capture (clicks → re-rank).  
3) Rate limiting + simple caching layer.

