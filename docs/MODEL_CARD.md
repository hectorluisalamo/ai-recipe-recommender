# Model Card — AI Recipe Recommender

**Version**: 0.2 (pop, kw, tfidf, embed)  
**Last Updated**: October 2025
**Owner**: Hector Luis Alamo
**Repository**: hectorluisalamo/ai-recipe-recommender


## Models (Implemented)
- **Popularity (pop)**: diet/must-include filters → sort by popularity.
- **Keyword (kw)**: token overlap between query and (title ∪ ingredients) + popularity epsilon.
- **TF-IDF (tfidf)**:
  - **Vectorizer**: scikit-learn TF-IDF over `title + ingredients` (ngrams configurable).
  - **Similarity**: cosine; return Top-K.
  - **Artifacts**: `models/vectorizer_v1.joblib`, `models/tfidf_v1.joblib`.
  - **Reasons**: top matched terms / highest-weighted tokens.
- **Embeddings (embed)**:
  - **Encoder**: `sentence-transformers/all-MiniLM-L6-v2` (Apache-2.0), 384-d.
  - **Index**: FAISS flat/IP (dev) or pgvector (prod). Query vector → ANN search → Top-K.
  - **Artifacts**: `models/embeddings/recipe_vectors.npy`, `ids.npy`, `faiss.index` *(or pgvector table)*.
  - **Reasons**: nearest neighbor terms / highlight ingredient/cuisine matches.

## Intended Use
✅ Primary Uses
* Suggest relevant recipes based on free-text search.
* Support bilingual users (English and Spanish).
* Compare lightweight vs deep semantic retrieval performance.

🚫 Out of Scope
* Medical or nutritional recommendations.
* Queries unrelated to food or recipes.
* High-stakes decision-making or personalization beyond keyword/semantic relevance.

## Training & Data
- **Source**: self-authored sample CSV (`data/recipes_sample.csv`) → SQLite (`data/recipes.db`).
- **Fields**: id, title, description, ingredients, cuisine, diet, time, popularity, url.
- **TF-IDF model**: trained on tokenized English/Spanish recipe text using scikit-learn (TfidfVectorizer).
- **Embeddings**: generated from [sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2] — 384-D vectors normalized and stored in Postgres via pgvector.
- **Cleaning**: lowercase, punctuation strip, normalize ingredients to `;`, small synonym map (e.g., chile→chili).

## Performance
Evaluation performed with eval/evaluate_via_api.py using gold set (eval/gold_set.jsonl)
Metrics: Precision@5, Mean Reciprocal Rank (MRR), Latency (p50/p95).

| Variant | Prec@5 | MRR | p50 ms | p95 ms | Cost/mo | Notes |
|--------:|:------:|:---:|:------:|:------:|:-------:|:------|
| Pop     | 0.12   | 0.33|  0.0   |  0.0   |   ~$0   | diet + popularity |
| KW      | 0.22   | 0.92|  0.0   |  0.0   |   ~$0   | token overlap |
| TF-IDF  | 0.20   | 0.90|  18.0  |  18.0  |   $0-10 | cosine, title+ingredients |
| Embeds  | 0.24   | 1.00|  20.0  |  32.0  |   $0-10 | MiniLM = FAISS/pgvector |

## Implementation Details

### Backend:
- **Framework**: FastAPI (Python 3.12)
- **Dependencies**: sentence-transformers, scikit-learn, httpx, psycopg[pool], pgvector
- **Data stores**:
    * SQLite for recipe metadata
    * Postgres + pgvector for embeddings

### Embed Model Parameters:
- **Dimension**: 384
- **Normalization**: L2
- **Index type**: IVF-Flat (lists=100, cosine distance)
- **ANN library**: pgvector

### Caching:
- Tiny LRU cache (256) avoids re-encoding identical queries.

## Risks & Biases
- **Language variance**: accents/Spanglish handled better by embeddings; still imperfect.
- **Cultural coverage**: small dataset skews cuisines; expand dataset with provenance.
- **Diet labeling**: classifications are simplistic and not medically verified.
- **Semantic bias**: embedding model uses multilingual data; subtle meaning differences may impact relevance in Spanglish or dialectal Spanish.

## Safety, Privacy, and Logging
- No PII stored; logs contain query text, latency, model used.
- Input limits & sanitization; lawful data sources only.

## Versioning & Reproducibility
- `requirements.txt` pinned; artifacts stored under `models/` with semantic version (e.g., `tfidf_v1`, `embed_miniLM_v1`).  
- Rebuild scripts kept in `scripts/` (index build; TF-IDF train).  
- Promotion gate: embeddings replace TF-IDF only if they outperform on Prec@5 or MRR by a meaningful margin (documented in metrics).

### Next planned updates:
- Expand gold set with 100+ bilingual queries.
- Introduce reranker model (cross-encoder variant) for qualitative comparison.
- Consolidate SQLite → Postgres migration.

## Citation/Reference
If you use or adapt this model:
@misc{alamo2025recipeai,
  author = {Hector Luis Alamo},
  title = {AI Recipe Recommender — Model Card},
  year = {2025},
  url = {https://github.com/hectoralamo/ai-recipe-recommender}
}