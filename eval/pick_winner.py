from eval.evaluate_models import run_eval
BASELINES = {
  'pop': run_eval('pop'),
  'kw': run_eval('kw'),
}
candidates = [('tfidf','v1'),('tfidf','uni')]
def better_than_baselines(p, r):
    p_pop, r_pop = BASELINES['pop'][0], BASELINES['pop'][1]
    p_kw,  r_kw  = BASELINES['kw'][0],  BASELINES['kw'][1]
    return ((p - p_pop >= 0.10 and p - p_kw >= 0.10) or
            (r - r_pop >= 0.10 and r - r_kw >= 0.10))
winners = []
for m,sfx in candidates:
    p,r,p50,p95 = run_eval(m, sfx)
    ok = better_than_baselines(p,r) and p95 <= 300
    winners.append((f'{m}:{sfx}', p, r, p95, ok))
winners.sort(key=lambda x: (x[1], x[2], -x[3]), reverse=True)
for tag,p,r,p95,ok in winners:
    print(f'{tag} | Prec@5={p:.2f} | MRR={r:.2f} | p95={p95:.1f} ms | {'PASS' if ok else 'FAIL'}')
print(f'Winner: {winners[0][0]} (top by Prec@5 then MRR; must PASS gate)')
