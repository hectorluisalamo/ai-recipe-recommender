# *AI Recipe Recommender* 🍳

Bilingual (EN/ES) recipe search with diet filters. Ships a FastAPI service with Prometheus metrics and a Streamlit demo UI.

**Live demo:** <https://recipe-ui-4ip2.onrender.com>  
**API base:** <https://recipe-api-81x3.onrender.com>  

## Quickstart (local)

bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# seed data + model
python app/db/ingest.py
python app/ranker/fit_index.py --fields title+ingredients --ngrams 1,2 --suffix v1
# run API
python -m uvicorn app.api.main:app --reload --port 8000
# run UI
streamlit run ui/app.py

## API (Schemas + cURL)

{
  "query": "quick vegan pasta with tomatoes",
  "diet": "vegan",
  "must_include": [],
  "k": 5,
  "language": "auto",
  "model": "kw"
}

curl -sX POST <https://recipe-api-81x3.onrender.com>/recommend \
 -H 'Content-Type: application/json' \
 -d '{"query":"quick vegan pasta with tomatoes","diet":"vegan","k":5,"model":"kw"}'

Health: GET /health → {"status":"ok","version":"x.y.z"}
Metrics: GET /metrics (Prometheus exposition)

## Metrics (sample)

Variant     Prec@5	    MRR	    p50ms  p95ms	Notes
pop	        0.12	    0.33	0.1	    0.1     popularity baseline
kw	        0.20	    0.90    0.1	    0.1     default model
tfidf:v1	0.20	    0.90	0.3     0.3     cosine sim
tfidf:uni	0.20	    0.90	0.2	    0.3	    ablation

Cost (est.): <$10/mo on free tiers; p95 <= 300 ms (1k recipes)

## Architecture

flowchart LR
  A[Streamlit UI] -->|JSON| B(FastAPI Service)
  B --> C{{Ranker\nkw | tfidf}}
  B --> D[(SQLite on Disk)]
  C --> D
  B --> E[/Prometheus /metrics/]
  B --> F{Validation\nPydantic}

## Repo layout

app/ (api/, ranker/, db/, metrics/)
data/ (sample csv + db)
models/ (tfidf artifacts)
ui/ (streamlit)
infra/ (entrypoint.sh, render.yaml)
tests/
eval/

## License & Data

## Next Steps

- Expand dataset + bilingual recall.
- Embeddings + pgvector A/B vs TF-IDF.
- Caching + rate limiting.