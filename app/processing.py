import logging
import threading

from sqlmodel import Session, delete, exists, or_, select

from app.chunking import chunk_page
from app.db import engine
from app.extract import extract_image_text, extract_pdf_text
from app.models import Chunk, Document, Page

logger = logging.getLogger(__name__)

# pdfium thread-safe değil; belgeler tek tek işlenir.
_lock = threading.Lock()


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
            document.status = "ready"
        except Exception:
            logger.exception("Belge %s işlenemedi", document_id)
            session.rollback()
            document.status = "failed"
        session.add(document)
        session.commit()


def process_pending() -> None:
    """İşlenmemiş, yarıda kalmış ya da parçalamadan önce işlenmiş belgeleri işler."""
    has_chunks = exists().where(Chunk.document_id == Document.id)
    with Session(engine) as session:
        ids = session.exec(
            select(Document.id).where(
                or_(Document.status.in_(["uploaded", "processing"]), (Document.status == "ready") & ~has_chunks)
            )
        ).all()
    for document_id in ids:
        process_document(document_id)
