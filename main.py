from fastapi import FastAPI
app = FastAPI(title="AI Recipe Recommender", version="0.0.1")
@app.get("/health")
def health():
    return {"status": "ok", "version": "0.0.1"}
