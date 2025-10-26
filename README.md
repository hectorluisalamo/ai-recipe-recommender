# *AI Recipe Recommender* 🍳

Top-K recipes from natural-language queries (EN/ES) with brief “reasons”. Models: **pop**, **kw**, **tfidf**, **embed**.

**Live demo:** <https://recipe-ui-4ip2.onrender.com>  
**API base:** <https://recipe-api-81x3.onrender.com>  

> Targets: Prec@5 ≥ 0.60 · p95 ≤ 300 ms (@ ~1k recipes) · ≤ $10/mo · 99% weekly uptime

## Quickstart (local)

bash
python3 -m venv .venv && source .venv/bin/activate \
pip install -r requirements.txt \
python -m uvicorn app.api.main:app --reload --port 8000 

* Health: http://127.0.0.1:8000/health
* Docs: http://127.0.0.1:8000/docs

## API (Schemas + cURL)

{ \
  "query": "quick vegan pasta with tomatoes", \
  "diet": "vegan", \
  "must_include": [], \
  "k": 5, \
  "language": "auto", \
  "model": "kw" \
}

Returns: results[{id,title,reasons[],score,url}], latency_ms, used_model.

Helpful:
* GET /health → {"status":"ok","version":"x.y.z"}
* GET /catalog/count → {"count": N}

## Architecture

```mermaid
flowchart LR
  A[Streamlit/Web] -->|JSON| B(FastAPI API)
  B --> C{Ranker}
  C -->|pop/kw/tfidf| D[(SQLite: recipes)]
  C -->|embed→ids| G[(Postgres: pgvector)]
  G -->|top ids| H[[Hydrate by ids]]
  H --> D
  C --> I[Diet & must_include filters]
  I --> J[[Top-K results]]
  B --> E[/Metrics & Logs/]
  B --> F{Lang Detect}
  F --> C
  B --> K[[/health, /feedback]]
  ```

## Models

* pop — diet filter + must-include → sort by popularity
* kw — token overlap (title + ingredients) + popularity tie-break
* tfidf — cosine over TF-IDF vectors (title+ingredients)
* embed — semantic search using embeddings (MiniLM) + ANN index (FAISS/pgvector).

## Repo layout

app/ (api/, ranker/, db/, metrics/) \
data/ (sample csv + db) \
models/ (tfidf artifacts) \
ui/ (streamlit) \
infra/ (entrypoint.sh, render.yaml) \
tests/ \
eval/

## License & Data

MIT

## Next Steps

- Expand dataset + bilingual recall.
- Embeddings + pgvector A/B vs TF-IDF.
- Caching + rate limiting.
