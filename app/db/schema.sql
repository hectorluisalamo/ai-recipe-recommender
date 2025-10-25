CREATE TABLE IF NOT EXISTS recipes (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  ingredients TEXT NOT NULL,   -- semicolon-separated
  cuisine TEXT,
  diet TEXT,
  time_minutes INTEGER,
  popularity INTEGER,
  url TEXT
);

CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recipe_id TEXT,
  query TEXT,
  is_relevant INTEGER CHECK (is_relevant IN (0,1)),
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
