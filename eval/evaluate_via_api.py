from __future__ import annotations
import argparse, json, statistics, time
from pathlib import Path
from typing import List, Dict
import httpx

GOLD = Path('eval/gold_set.jsonl')

def prec_at_k(pred_ids: List[str], rel_ids: List[str], k:int=5)->float:
    return sum(1 for x in pred_ids[:k] if x in rel_ids)/float(k)

def mrr(pred_ids: List[str], rel_ids: List[str])->float:
    for i, pid in enumerate(pred_ids, 1):
        if pid in rel_ids: return 1.0/i
    return 0.0

def p50(vals: List[float])->float:
    return statistics.median(sorted(vals)) if vals else 0.0

def p95(vals: List[float])->float:
    if not vals: return 0.0
    vals = sorted(vals)
    idx = max(0, int(0.95*len(vals)) - 1)
    return vals[idx]

def eval_model(api:str, model:str, k:int=5):
    gold =[json.loads(l) for l in GOLD.read_text(encoding='utf-8').splitlines() if l.strip()]
    precs, mrrs, model_lat_ms, rtt_ms = [], [], [], []
    
    with httpx.Client(base_url=api, timeout=10.0) as client:
        #warm-up one request
        try:
            client.post('/recomend', json={"query":"warmup", "diet":"none", "k":k, "language":"auto", "model":model})
        except Exception:
            pass
        
        for row in gold:
            q = row['query']; rel = row['relevant_ids']
            t0 = time.perf_counter()
            resp = client.post('/recommend', json={
                "query": q,
                "diet": "none",
                "must_include": [],
                "k": k,
                "language": "auto",
                "model": model
            })
            rtt_ms.append((time.perf_counter() - t0) * 1000.0)
            
            if resp.status_code != 200:
                return {"status":"error","model":model,"code":resp.status_code,"detail":resp.text}
            
            data = resp.json()
            ids = [r['id'] for r in data.get('results', [])]
            precs.append(prec_at_k(ids, rel, k))
            mrrs.append(mrr(ids, rel))
            
            # model latency reported by API
            lm = float(data.get('latency_ms', 0))
            if lm > 0:
                model_lat_ms.append(lm)
    
    return {
        "status":"ok",
        "model":model,
        "prec5": sum(precs)/len(precs) if precs else 0.0,
        "mrr": sum(mrrs)/len(mrrs) if mrrs else 0.0,
        "p50_ms": p50(model_lat_ms),
        "p95_ms": p95(model_lat_ms),
        "rtt_p50_ms": p50(rtt_ms),
        "rtt_p95_ms": p95(rtt_ms),
        "n": len(precs),
    }
    
def fmt_row(name, r, notes):
    if r.get('status') != 'ok':
        return f"| {name:<7} | ERR | ERR | - | - | ~$0 | {r.get('code', '?')} {r.get('detail', '')[:40]} |"
    return (f"| {name:<7} | {r['prec5']:.2f} | {r['mrr']:.2f} | {r['p50_ms']:.1f} | {r['p95_ms']:.1f} | {'~$0' if name in ('Pop', 'KW') else '$0-10'} | {notes} |")

def main():
    ap =argparse.ArgumentParser()
    ap.add_argument('--api', default='http://127.0.0.1:8000')
    ap.add_argument('--models', nargs='+', default=['pop','kw','tfidf','embed'])
    ap.add_argument('--k', type=int, default=5)
    args = ap.parse_args()
    
    name_map = {'pop':'Pop','kw':'KW','tfidf':"TF-IDF",'embed':'Embeds'}
    notes_map = {
        'pop': 'diet + popularity',
        'kw': 'token overlap',
        'tfidf': 'cosine, title+ingredients',
        'embed': 'MiniLM = FAISS/pgvector'
    }
    
    results = []
    for m in args.models:
        r = eval_model(args.api, m, k=args.k)
        results.append((name_map.get(m,m), r, notes_map.get(m,'')))
    
    print('# Evaluation Results\n')
    print(f"API: {args.api} · k={args.k} · gold={sum(1 for _ in open(GOLD, 'r', encoding='utf-8'))} queries\n")
    print('| Variant | Prec@5 | MRR | p50 ms | p95 ms | Cost/mo | Notes |')
    print('|--------:|:------:|:---:|:------:|:------:|:-------:|:------|')
    for name, r, note in results:
        print(fmt_row(name, r, note))
        
    # also show end-to-end RTT med/p95 for debugging
    print('\n(Above p50/p95 are model latency for API response. RTT med/p95 printed per model for reference.)')
    for name, r, _ in results:
        if r.get('status') == 'ok':
            print(f"{name:>7} RTT p50={r['rtt_p50_ms']:.1f} ms · p95={r['rtt_p95_ms']:.1f} ms")
            
if __name__ == '__main__':
    main()
