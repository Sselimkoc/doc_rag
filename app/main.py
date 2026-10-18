import logging
import threading
import urllib.error
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.answer import router as answer_router
from app.db import init_db
from app.documents import router as documents_router
from app.embedding import embed
from app.ollama import load_llm
from app.processing import process_pending
from app.search import router as search_router

logger = logging.getLogger(__name__)


def warm_up():
    # İlk soru model yüklenmesini (~13 s) beklemesin.
    # Sıra önemli: LLM sonra yüklenirse Ollama bge-m3'ü bellekten atıyor.
    try:
        load_llm()
        embed(["ısınma"])
    except (urllib.error.URLError, TimeoutError) as error:
        logger.warning("Modeller önceden yüklenemedi: %s", error)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Açılışı bekletmemek için arka planda.
    threading.Thread(target=process_pending, daemon=True).start()
    threading.Thread(target=warm_up, daemon=True).start()
    yield


app = FastAPI(title="doc_rag", lifespan=lifespan)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(answer_router)


@app.get("/health")
def health():
    return {"status": "ok"}
