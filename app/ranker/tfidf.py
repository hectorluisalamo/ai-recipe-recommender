from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path

import joblib
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_DIR = Path('models')

class TfidfIndex:
    def __init__(self, vectorizer: TfidfVectorizer, X, rows: List[Dict[str, Any]]):
        self.vectorizer = vectorizer
        self.X = X  # csr_matrix
        self.rows = rows
        
    @classmethod
    def load(cls, suffix: str = '') -> 'TfidfIndex':
        s = f'_{suffix}' if suffix else ''
        vectorizer: TfidfVectorizer = joblib.load(MODEL_DIR / f'vectorizer{s}.joblib')
        X = sparse.load_npz(MODEL_DIR / f'tfidf_matrix{s}.npz')
        rows: List[Dict[str, Any]] = joblib.load(MODEL_DIR / f'rows{s}.joblib')
        return cls(vectorizer, X, rows)

    def recommend(self, query: str, diet: str, must_include: List[str], k: int) -> List[Dict[str, Any]]:
        # filter by diet first by masking rows
        mask = [True] * len(self.rows)
        if diet and diet != 'none':
            mask = [r.get('diet') == diet for r in self.rows]

        # vectorize query
        q_vec = self.vectorizer.transform([query or ''])

        # compute cosine for masked rows only
        X_masked = self.X[mask]
        if X_masked.shape[0] == 0:
            return []
        sims = cosine_similarity(q_vec, X_masked).ravel()  # length = #masked rows

        # map masked indices back to original row indices
        masked_idx_to_rowidx = [i for i, m in enumerate(mask) if m]
        scored: List[Dict[str, Any]] = []
        for pos_in_mask, score in enumerate(sims):
            row_idx = masked_idx_to_rowidx[pos_in_mask]
            row = self.rows[row_idx]
            # must_include check
            if must_include:
                ing = row.get('ingredients','').lower()
                if not all(m.lower() in ing for m in must_include):
                    continue
            reasons = self._reasons_for(query, row, top_terms=3)
            scored.append({
                'id': row['id'],
                'title': row['title'],
                'reasons': reasons,
                'score': float(score),
                'url': row.get('url'),
            })

        # sort by similarity, tie-break by popularity
        scored.sort(key=lambda r: (r['score'], (r.get('popularity') or 0)), reverse=True)
        return scored[:k]

    def _reasons_for(self, query: str, row: Dict[str, Any], top_terms: int = 3) -> List[str]:
        # Show matched query tokens found in the row’s vocabulary, up to 3
        q_tokens = [t for t in (query or '').lower().split() if t]
        ing_title = f'{row.get('title','')} {row.get('ingredients','')}'.lower()
        hits = [t for t in q_tokens if t in ing_title]
        reasons = []
        if hits:
            reasons.append('matched: ' + ', '.join(sorted(set(hits))[:top_terms]))
        diet = row.get('diet')
        if diet and diet != 'none':
            reasons.append(f'diet: {diet}')
        pop = row.get('popularity') or 0
        reasons.append(f'similarity TF-IDF, popular={pop}')
        return reasons
