from __future__ import annotations
import json, time
from pathlib import Path
from typing import List, Optional, Tuple

from app.ranker.baselines import recommend_popularity, recommend_keyword
from app.ranker.tfidf import TfidfIndex

GOLD_PATH = Path('eval/gold_set.jsonl')

def prec_at_k(pred_ids: List[str], rel_ids: List[str], k: int=5) -> float:
    hits = sum(1 for x in pred_ids[:k] if x in rel_ids)
    return hits / float(k)

def mrr(pred_ids: List[str], rel_ids: List[str]) -> float:
    for i, pid in enumerate(pred_ids, start=1):
        if pid in rel_ids:
            return 1.0 / i
    return 0.0

def run_eval(model: str, tfidf_suffix: Optional[str]=None) -> Tuple[float,float,float,float]:
    precs, mrrs, latencies = [], [], []
    tfidf = TfidfIndex.load(tfidf_suffix) if model == 'tfidf' else None
    with open(GOLD_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            row = json.loads(line)
            q = row['query']; rel = row['relevant_ids']
            t0 = time.perf_counter()
            if model == 'pop':
                preds = recommend_popularity(q, diet='none', must_include=[], k=5)
            elif model == 'kw':
                preds = recommend_keyword(q, diet='none', must_include=[], k=5)
            else:
                preds = tfidf.recommend(q, diet='none', must_include=[], k=5)
            lat_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat_ms)
            pred_ids = [p['id'] for p in preds]
            precs.append(prec_at_k(pred_ids, rel))
            mrrs.append(mrr(pred_ids, rel))
    p_at5 = sum(precs)/len(precs)
    mrr_avg = sum(mrrs)/len(mrrs)
    p50 = sorted(latencies)[len(latencies)//2]
    p95 = sorted(latencies)[max(0, int(len(latencies)*0.95)-1)]
    return p_at5, mrr_avg, p50, p95

def main():
    rows = []
    for name in [('pop', None), ('kw', None), ('tfidf','v1'), ('tfidf','uni')]:
        m, sfx = name
        p, r, p50, p95 = run_eval(m, sfx)
        tag = m if sfx is None else f'{m}:{sfx}'
        rows.append((tag, p, r, p50, p95))
    print('| Variant | Prec@5 | MRR  | p50 ms | p95 ms |')
    print('|---------|--------|------|--------|--------|')
    for tag, p, r, p50, p95 in rows:
        print(f'| {tag:<8} | {p:.2f}  | {r:.2f} | {p50:.1f} | {p95:.1f} |')

if __name__ == '__main__':
    main()
