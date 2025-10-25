import sqlite3
import pandas as pd
import re
from pathlib import Path

DB_PATH = Path("data/recipes.db")
CSV_PATH = Path("data/recipes_sample.csv")

PUNCT_RE = re.compile(r"[^\w\s;]")
VALID_DIETS = {"none","keto","vegan","vegetarian","gluten_free"}
DIET_MAP = {
    "gluten-free": "gluten_free",
    "gluten free": "gluten_free",
    "gf": "gluten_free",
    "veg": "vegetarian",
    "vegetarian": "vegetarian",
    "vegan": "vegan",
    "keto": "keto",
    "none": "none",
    "omnivore": "none",
    "paleo": "none",
    "regular": "none",
}

def normalize_text(s: str) -> str:
    s = s or ""
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = PUNCT_RE.sub("", s)
    return s

def normalize_ingredients(s: str) -> str:
    parts = re.split(r"[;,]", (s or "").lower())
    norm = []
    for p in parts:
        p = p.strip()
        if not p: continue
        p = p.replace("aji limon", "limon aji").replace("chile", "chili")
        norm.append(p)
    return "; ".join(norm)

def normalize_diet(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "none"
    s = str(x).strip().lower().replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    s = DIET_MAP.get(s, s).replace(" ", "_")
    return s if s in VALID_DIETS else "none"

def main():
    print(f"Loading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    # normalize fields
    df["title"] = df["title"].map(normalize_text)
    df["description"] = df["description"].fillna("").map(normalize_text)
    df["ingredients"] = df["ingredients"].map(normalize_ingredients)
    df["diet"] = df["diet"].apply(normalize_diet).astype(str).str.strip()
    df["cuisine"] = df["cuisine"].fillna("").astype(str)
    df["time_minutes"] = df["time_minutes"].fillna(0).astype(int)
    df["popularity"] = df["popularity"].fillna(0).astype(int)
    df["url"] = df["url"].fillna("").astype(str)

    print("[ingest] Diet distribution:", df["diet"].value_counts().to_dict())

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        rows = []
        for _, r in df.iterrows():
            diet = r["diet"]
            if diet not in VALID_DIETS:
                diet = "none"
            rows.append((
                str(r["id"]),
                str(r["title"]),
                str(r["description"]),
                str(r["ingredients"]),
                str(r["cuisine"]),
                diet,
                int(r["time_minutes"]),
                int(r["popularity"]),
                str(r["url"]),
            ))
        cur.executemany("""
            INSERT INTO recipes (id, title, description, ingredients, cuisine, diet, time_minutes, popularity, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        # indexes (idempotent)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_diet ON recipes(diet)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_popularity ON recipes(popularity)")
        conn.commit()
    print(f"Ingested {len(rows)} recipes into {DB_PATH}")

if __name__ == "__main__":
    main()
