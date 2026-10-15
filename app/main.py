import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.documents import router as documents_router
from app.processing import process_pending


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Açılışı bekletmemek için arka planda.
    threading.Thread(target=process_pending, daemon=True).start()
    yield


app = FastAPI(title="doc_rag", lifespan=lifespan)
app.include_router(documents_router)


@app.get("/health")
def health():
    return {"status": "ok"}
