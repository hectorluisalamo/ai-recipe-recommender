from __future__ import annotations
import os, sqlite3, math 
from typing import List, Dict
import psycopg
import numpy as np
from sentence_transformers import SentenceTransformer
from pgvector.psycopg import register_vector

SQLITE = 'data/recipes.db'
PG = os.environ.get('PG_URL')
MODEL_NAME = os.environ.get('EMBED_MODEL', 'sentence-transformers/paraphrase-multlingual-MiniLM-L12-v2')

def load_rows():
    with sqlite3.connect(SQLITE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('Select id, title, ingredients FROM recipes ORDER BY id').fetchall()
        return [dict(r) for r in rows]
    
def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i+n]
        
def main():
    assert PG, 'Set PG_URL'
    rows = load_rows()
    if not rows:
        raise SystemExit('No rows found in the SQLite DB.')
    print(f'Loaded {len(rows)} recipes')
    
    model = SentenceTransformer(MODEL_NAME)
    print(f'Loaded model: {MODEL_NAME}')
    
    with psycopg.connect(PG) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for batch in chunks(rows, 64):
                texts = [f"{r['title']} {r['ingredients']}" for r in batch]
                embs = model.encode(texts, normalize_embeddings=True) # cosine-ready
                for r, e in zip(batch, embs):
                    vec = np.array(e, dtype=np.float32).tolist()
                    cur.execute(
                        'INSERT INTO recipes_embeddings (recipe_id, embedding) VALUES (%s, %s) '
                        'ON CONFLICT (recipe_id) DO UPDATE SET embedding = EXCLUDED.embedding',
                        (r['id'], vec)
                    )
                conn.commit()
                print(f'Upserted {len(batch)} embeddings')
    print('Done.')

if __name__ == '__main__':
    main()