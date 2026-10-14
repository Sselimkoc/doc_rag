from fastapi import FastAPI

app = FastAPI(title="doc_rag")


@app.get("/health")
def health():
    return {"status": "ok"}
