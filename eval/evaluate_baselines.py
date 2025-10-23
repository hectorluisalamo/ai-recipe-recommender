from __future__ import annotations

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json, time
from pathlib import Path
from typing import List

from app.ranker.baselines import recommend_popularity, recommend_keyword

GOLD_PATH = Path('eval/gold_set.jsonl')

def prec_at_k(pred_ids: List[str], rel_ids: List[str], k: int=5) -> float:
    hits = sum(1 for x in pred_ids[:k] if x in rel_ids)
    return hits / float(k)

def mrr(pred_ids: List[str], rel_ids: List[str]) -> float:
    for i, pid in enumerate(pred_ids, start=1):
        if pid in rel_ids:
            return 1.0 / i
    return 0.0

def run_eval(model: str):
    precs, mrrs, latencies = [], [], []
    with open(GOLD_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            row = json.loads(line)
            q = row['query']
            rel = row['relevant_ids']
            t0 = time.perf_counter()
            if model == 'pop':
                preds = recommend_popularity(q, diet='none', must_include=[], k=5)
            else:
                preds = recommend_keyword(q, diet='none', must_include=[], k=5)
            lat_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat_ms)
            pred_ids = [p['id'] for p in preds]
            precs.append(prec_at_k(pred_ids, rel, k=5))
            mrrs.append(mrr(pred_ids, rel))
    p_at5 = sum(precs) / len(precs)
    mrr_avg = sum(mrrs) / len(mrrs)
    p50 = sorted(latencies)[len(latencies)//2]
    p95 = sorted(latencies)[max(0, int(len(latencies)*0.95)-1)]
    return p_at5, mrr_avg, p50, p95

def main():
    for m in ['pop','kw']:
        p, r, p50, p95 = run_eval(m)
        print(f'{m:>3} | Prec@5={p:.2f} | MRR={r:.2f} | p50={p50:.1f} ms | p95={p95:.1f} ms')

if __name__ == '__main__':
    main()
