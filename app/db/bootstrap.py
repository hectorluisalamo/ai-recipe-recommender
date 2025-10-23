from __future__ import annotations
import os, sys, shutil, pathlib, urllib.parse, sqlite3

DEFAULT_PATH = '/tmp/recipes.db'  # free tier-friendly

def _path_from_db_url(db_url: str) -> str:
    if not db_url.startswith('sqlite'):
        return DEFAULT_PATH
    parsed = urllib.parse.urlparse(db_url)
    p = parsed.path
    return p if p else DEFAULT_PATH

def ensure_db():
    db_url = os.getenv('DB_URL', f'sqlite:////{DEFAULT_PATH}')
    db_path = _path_from_db_url(db_url)
    db_dir = os.path.dirname(db_path) or '/tmp'
    pathlib.Path(db_dir).mkdir(parents=True, exist_ok=True)

    if not os.path.exists(db_path):
        print(f'[bootstrap] Seeding DB to {db_path}')
        seed_src = '/app/data/recipes.db'
        if os.path.exists(seed_src):
            shutil.copy(seed_src, db_path)
        else:
            # last resort: create empty DB and let app work with it
            sqlite3.connect(db_path).close()

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute('PRAGMA journal_mode=WAL;')
        print(f'[bootstrap] DB ready at {db_path}')
    except Exception as e:
        print(f'[bootstrap] ERROR touching DB: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    ensure_db()
