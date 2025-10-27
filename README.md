# *AI Recipe Recommender* 🥑

Top-K recipes from natural-language queries (EN/ES) with brief “reasons”. Models: **pop**, **kw**, **tfidf**, **embed**.

**Live demo**: <https://recipe-ui-4ip2.onrender.com>  
**API base**: <https://recipe-api-81x3.onrender.com>  

> Targets: Precision@5 ≥ 0.60 · p95 ≤ 300 ms (@ ~1k recipes) · ≤ $10/mo · 99% weekly uptime

See also:
- [`model_card.md`](./model_card.md) — architecture, metrics, and limitations
- [`case_study.md`](./case_study.md) — design rationale and takeaways

## Quickstart (local)

```bash
python3 -m venv .venv && source .venv/bin/activate \
pip install -r requirements.txt \
python -m uvicorn app.api.main:app --reload --port 8000
```

**Requirements**: Python ≥3.10 · Docker (optional) · pip · virtualenv

* **Health**: http://127.0.0.1:8000/health
* **Docs**: http://127.0.0.1:8000/docs

## Docker

**<ins>Build image</ins>**
docker build -t recipe-api .

**<ins>Run API container</ins>**
docker run --rm -p 8000:8000 -e DB_URL=sqlite:////app/data/recipes.db recipe-api

**<ins>Run Streamlit UI</ins>**
docker run --rm -p 8501:8501 -e API_URL=http://localhost:8000 recipe-ui


## Environment Variables

| **Variable** | **Default** | **Description** |
|-----------|----------|-------------|
| `APP_ENV` | `dev` | Environment mode |
| `DB_URL` | `sqlite:////data/recipes.db` | SQLite or Postgres connection |
| `PG_URL` | — | Optional pgvector database URL |
| `EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model used for semantic search |

## API (Schemas + cURL)

{ \
  "query": "quick vegan pasta with tomatoes", \
  "diet": "vegan", \
  "must_include": [], \
  "k": 5, \
  "language": "auto", \
  "model": "kw" \
}

**Returns**: results[{id,title,reasons[],score,url}], latency_ms, used_model.

<ins>Helpful</ins>:
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

## Evaluation

Run local benchmarks against the API using the included gold set:

```bash
python eval/evaluate_via_api.py --api http://127.0.0.1:8000 --models pop kw tfidf embed --k 5
```

## Models

* **pop**: diet filter + must-include → sort by popularity
* **kw**: token overlap (title + ingredients) + popularity tie-break
* **tfidf**: cosine over TF-IDF vectors (title+ingredients)
* **embed**: semantic search using embeddings (MiniLM) + ANN index (FAISS/pgvector).

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

## Contributing

Pull requests and discussions are welcome.

Created and maintained by **Hector Luis Alamo**.  

📫 [LinkedIn](https://www.linkedin.com/in/hector-luis-alamo-90432941/) ·
