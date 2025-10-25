# Model Card — AI Recipe Recommender

**Intended Use:** top-K recipe retrieval for general cooking queries in EN/ES.  
**Not for:** medical/nutrition advice, allergen guarantees, scraping protected content.

**Data provenance:** small seed CSV; future datasets must be legally licensed.

**Known biases/limits:** cuisine coverage skewed by seed data; limited multilingual coverage; ingredient synonyms may miss matches.

**Evaluation:** offline gold set (10 queries). Metrics: Prec@5, MRR, p latency. Promote new models only if they beat baselines by +10 Prec@5 or +0.1 MRR.

**Safety:** no PII, input length caps, structured errors, 2s timeout.
