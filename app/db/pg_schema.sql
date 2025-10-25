CREATE EXTENSION IF NOT EXISTS vector;

-- embedding dimension for MiniLM-L12-v2 (384)
CREATE TABLE IF NOT EXISTS recipes_embeddings (
    recipe_id TEXT PRIMARY KEY,
    embedding VECTOR(384)
);

-- IVF index for cosine distance
CREATE INDEX IF NOT EXISTS idx_recipes_embeddings_cosine
ON recipes_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);