# AI Recipe Recommender

**Goal:** Top-K recipes from natural-language queries (EN/ES), with brief reasons.

## Metrics Targets
- Prec@5 ≥ 0.60; MRR tracked
- p95 ≤ 300 ms (@ ~1k recipes)
- Cost ≤ $10/mo; Uptime ≥ 99% weekly

Run locally:
```bash
pip install -r requirements.txt
uvicorn app.api.main:app --reload
