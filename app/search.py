import urllib.error

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.embedding import EMBED_MODEL, embed
from app.models import Chunk, Document, Embedding, not_deleted
from app.schemas import SearchRequest, SearchResult

router = APIRouter(tags=["search"])


def search(session: Session, query: str, k: int = 8, document_ids: list[int] | None = None) -> list[tuple[Chunk, float]]:
    """Soruya en yakın k parçayı kosinüs benzerliğiyle döndürür.
    """
    statement = (
        select(Embedding.chunk_id, Embedding.vector)
        .join(Document, Document.id == Embedding.document_id)
        .where(Embedding.model == EMBED_MODEL, not_deleted())
    )
    if document_ids is not None:
        statement = statement.where(Embedding.document_id.in_(document_ids))
    rows = session.exec(statement).all()
    if not rows:
        return []
    chunk_ids = [chunk_id for chunk_id, _ in rows]
    matrix = np.frombuffer(b"".join(vector for _, vector in rows), dtype=np.float32).reshape(len(rows), -1)
    scores = matrix @ embed([query])[0]
    top = np.argsort(-scores)[:k]
    chunks = session.exec(select(Chunk).where(Chunk.id.in_([chunk_ids[i] for i in top]))).all()
    by_id = {c.id: c for c in chunks}
    return [(by_id[chunk_ids[i]], float(scores[i])) for i in top]


@router.post("/search", response_model=list[SearchResult])
def search_chunks(request: SearchRequest, session: Session = Depends(get_session)):
    try:
        results = search(session, request.query, request.k, request.document_ids)
    except urllib.error.URLError:
        raise HTTPException(503, "Embedding servisine (Ollama) ulaşılamadı.")
    return to_results(session, results)


def to_results(session: Session, results: list[tuple[Chunk, float]]) -> list[SearchResult]:
    filenames = dict(session.exec(select(Document.id, Document.filename)).all())
    return [
        SearchResult(
            chunk_id=c.id, document_id=c.document_id, filename=filenames[c.document_id],
            page=c.page, section=c.section, kind=c.kind, source=c.source, score=score, text=c.text,
        )
        for c, score in results
    ]


def with_neighbors(session: Session, sources: list[SearchResult], top: int) -> list[SearchResult]:
    """İlk `top` parçaya aynı sayfadaki önceki ve sonraki parçayı ekler.
    Cevap cümlesi bazen sayfanın gelmeyen parçasında kalıyor (TESTING Vaka 58)."""
    taken = {s.chunk_id for s in sources}
    widened = []
    for rank, source in enumerate(sources):
        if rank < top:
            chunk = session.get(Chunk, source.chunk_id)
            # Sayfa dışına taşmaz: alıntının gösterdiği sayfa doğru kalsın.
            neighbors = session.exec(
                select(Chunk).where(
                    Chunk.document_id == chunk.document_id,
                    Chunk.page == chunk.page,
                    Chunk.position.in_([chunk.position - 1, chunk.position + 1]),
                )
            ).all()
            parts = sorted([chunk] + [n for n in neighbors if n.id not in taken], key=lambda c: c.position)
            taken.update(c.id for c in parts)
            source = source.model_copy(update={"text": "\n".join(c.text for c in parts)})
        widened.append(source)
    return widened
