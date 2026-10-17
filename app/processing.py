import logging
import threading

from sqlmodel import Session, delete, exists, or_, select

from app.chunking import chunk_page
from app.db import engine
from app.embedding import EMBED_MODEL, embed
from app.extract import extract_image_text, extract_pdf_text
from app.models import Chunk, Document, Embedding, Page

logger = logging.getLogger(__name__)

# pdfium thread-safe değil; belgeler tek tek işlenir.
_lock = threading.Lock()


def embed_document(session: Session, document_id: int) -> None:
    """Belgenin parçalarını vektöre çevirip kaydeder (commit etmez)."""
    session.exec(delete(Embedding).where(Embedding.document_id == document_id))
    chunks = session.exec(select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.position)).all()
    if not chunks:
        return
    vectors = embed([c.text for c in chunks])
    session.add_all(
        Embedding(chunk_id=c.id, document_id=document_id, model=EMBED_MODEL, vector=v.tobytes())
        for c, v in zip(chunks, vectors)
    )


def process_document(document_id: int) -> None:
    """Belgenin metnini sayfa sayfa çıkarıp parçalarıyla kaydeder, durumunu günceller."""
    with _lock, Session(engine) as session:
        document = session.get(Document, document_id)
        if document is None:
            return
        document.status = "processing"
        session.add(document)
        session.commit()
        try:
            if document.content_type == "application/pdf":
                pages = extract_pdf_text(document.path)
            else:
                pages = [(extract_image_text(document.path), "ocr")]
            # Yarıda kalmış önceki denemenin kayıtları silinir.
            session.exec(delete(Embedding).where(Embedding.document_id == document_id))
            session.exec(delete(Page).where(Page.document_id == document_id))
            session.exec(delete(Chunk).where(Chunk.document_id == document_id))
            session.add_all(Page(document_id=document_id, number=i + 1, text=t) for i, (t, _) in enumerate(pages))
            chunks, section = [], None
            for number, (page_text, source) in enumerate(pages, start=1):
                # Başlık sonraki sayfaya devreder.
                page_chunks, section = chunk_page(page_text, section)
                chunks += [(number, source, *c) for c in page_chunks]
            session.add_all(
                Chunk(
                    document_id=document_id, page=number, position=i,
                    text=text, kind=kind, source=source, section=section,
                )
                for i, (number, source, kind, text, section) in enumerate(chunks)
            )
            session.flush()
            embed_document(session, document_id)
            document.status = "ready"
            session.add(document)
            session.commit()
        except Exception:
            logger.exception("Belge %s işlenemedi", document_id)
            session.rollback()
            document.status = "failed"
            session.add(document)
            session.commit()


def process_pending() -> None:
    """İşlenmemiş, yarıda kalmış ya da parçalamadan önce işlenmiş belgeleri işler; vektörü eksik olanları tamamlar."""
    has_chunks = exists().where(Chunk.document_id == Document.id)
    has_embeddings = exists().where(Embedding.document_id == Document.id)
    with Session(engine) as session:
        ids = session.exec(
            select(Document.id).where(
                or_(Document.status.in_(["uploaded", "processing"]), (Document.status == "ready") & ~has_chunks)
            )
        ).all()
        to_embed = session.exec(
            select(Document.id).where((Document.status == "ready") & has_chunks & ~has_embeddings)
        ).all()
    for document_id in ids:
        process_document(document_id)
    # Metin zaten çıkarılmış; sadece vektörler hesaplanır. Ollama kapalıysa sonraki açılışta tekrar denenir.
    for document_id in to_embed:
        with _lock, Session(engine) as session:
            try:
                embed_document(session, document_id)
                session.commit()
            except Exception:
                logger.exception("Belge %s vektörleri hesaplanamadı", document_id)
