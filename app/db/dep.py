from contextlib import contextmanager
from sqlalchemy import create_engine
import os

DB_URL = os.getenv('DB_URL', 'sqlite:///data/recipes.db')
_engine = create_engine(DB_URL, echo=False, future=True)

@contextmanager
def _conn():
    with _engine.begin() as conn:
        yield conn

def get_conn():
    with _conn() as c:
        yield c
