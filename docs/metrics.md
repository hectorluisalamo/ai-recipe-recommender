# Evaluation Results

API: http://127.0.0.1:8000 · k=5 · gold=10 queries

| Variant | Prec@5 | MRR | p50 ms | p95 ms | Cost/mo | Notes |
|--------:|:------:|:---:|:------:|:------:|:-------:|:------|
| Pop     | 0.12   | 0.33|  0.0   |  0.0   |   ~$0   | diet + popularity |
| KW      | 0.22   | 0.92|  0.0   |  0.0   |   ~$0   | token overlap |
| TF-IDF  | 0.20   | 0.90|  18.0  |  18.0  |   $0-10 | cosine, title+ingredients |
| Embeds  | 0.24   | 1.00|  20.0  |  32.0  |   $0-10 | MiniLM = FAISS/pgvector |

Dataset: 10 recipes (toy) for dev; expand to ~1k before final report

Gold set: eval/gold_set.jsonl (EN/ES)

Artifacts:
* TF-IDF: models/vectorizer_v1.joblib, models/tfidf_v1.joblib
* Embeddings: models/embeddings/recipe_vectors.npy, models/embeddings/ids.npy, models/embeddings/faiss.index (or pgvector table)