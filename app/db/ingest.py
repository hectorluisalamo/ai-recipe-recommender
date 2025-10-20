import sqlite3
import pandas as pd
import re
from pathlib import Path

DB_PATH = Path("data/recipes.db")
SCHEMA_PATH = Path("app/db/schema.sql")
CSV_PATH = Path("data/recipes_sample.csv")

# --- basic cleaners ---
PUNCT_RE = re.compile(r"[^\w\s;]")  # keep word chars, whitespace, and semicolons

def normalize_text(s: str) -> str:
    s = s or ""
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = PUNCT_RE.sub("", s)
    return s

# collapse some ingredient synonyms; expand as needed
SYNONYMS = {
    "aji amarillo": "aji amarillo",
    "aji limon": "limon aji",
    "chile": "chili",
}

def normalize_ingredients(s: str) -> str:
    # accept comma or semicolon; output semicolon-separated
    parts = re.split(r"[;,]", s.lower())
    norm = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        p = SYNONYMS.get(p, p)
        norm.append(p)
    return "; ".join(norm)

def main():
    print(f"Loading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    # standardize columns
    df["title_norm"] = df["title"].map(normalize_text)
    df["desc_norm"] = df["description"].fillna("").map(normalize_text)
    df["ingredients"] = df["ingredients"].map(normalize_ingredients)
    # ensure diet labels valid
    valid_diets = {"none","keto","vegan","vegetarian","gluten_free"}
    bad = set(df["diet"]) - valid_diets
    if bad:
        raise ValueError(f"Invalid diet labels found: {bad}")

    # create DB + schema
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        # upsert: replace on conflict by id
        df_to_load = df[[
            "id","title","description","ingredients","cuisine","diet","time_minutes","popularity","url"
        ]].copy()

        df_to_load.to_sql("recipes", conn, if_exists="append", index=False)
        # create basic indexes to speed later queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recipes_diet ON recipes(diet)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recipes_popularity ON recipes(popularity)")
        conn.commit()
    print(f"Ingested {len(df)} recipes into {DB_PATH}")

if __name__ == "__main__":
    main()
