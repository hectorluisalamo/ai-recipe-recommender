from __future__ import annotations
import sqlite3, argparse
from pathlib import Path
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from scipy import sparse
import joblib

DB_PATH = Path('data/recipes.db')
MODEL_DIR = Path('models')

def load_rows() -> List[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('''
            SELECT id, title, ingredients, cuisine, diet, url, popularity
            FROM recipes
            ORDER BY id
        ''').fetchall()
        return [dict(r) for r in rows]

def build_corpus(rows: List[Dict], fields: str) -> List[str]:
    corpus = []
    for r in rows:
        if fields == 'title':
            text = r['title']
        elif fields == 'ingredients':
            text = r['ingredients']
        else:
            text = f'{r['title']} {r['ingredients']}'
        corpus.append(text)
    return corpus

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fields', choices=['title','ingredients','title+ingredients'], default='title+ingredients')
    p.add_argument('--ngrams', type=str, default='1,2', help='min,max e.g. 1,1 or 1,2')
    p.add_argument('--suffix', type=str, default='', help='artifact name suffix, e.g. v1 or uni')
    args = p.parse_args()

    min_n, max_n = [int(x) for x in args.ngrams.split(',')]
    suffix = (f'_{args.suffix}' if args.suffix else '')

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    if not rows:
        raise SystemExit('No recipes in DB. Run ingestion first.')
    corpus = build_corpus(rows, args.fields)

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(min_n, max_n),
        min_df=1,
        max_features=None,
    )
    X = vectorizer.fit_transform(corpus)

    joblib.dump(vectorizer, MODEL_DIR / f'vectorizer{suffix}.joblib')
    sparse.save_npz(MODEL_DIR / f'tfidf_matrix{suffix}.npz', X)
    joblib.dump(rows, MODEL_DIR / f'rows{suffix}.joblib')

    print(f'[saved] models/vectorizer{suffix}.joblib, tfidf_matrix{suffix}.npz, rows{suffix}.joblib')
    print(f'fields={args.fields} ngrams={args.ngrams} -> {X.shape[0]}x{X.shape[1]}')

if __name__ == '__main__':
    main()
