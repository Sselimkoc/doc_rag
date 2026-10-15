import logging
import threading

from sqlmodel import Session, delete, select

from app.db import engine
from app.extract import extract_image_text, extract_pdf_text
from app.models import Document, Page

logger = logging.getLogger(__name__)

# pdfium thread-safe değil; belgeler tek tek işlenir.
_lock = threading.Lock()


def process_document(document_id: int) -> None:
    """Belgenin metnini sayfa sayfa çıkarıp kaydeder, durumunu günceller."""
    with _lock, Session(engine) as session:
        document = session.get(Document, document_id)
        if document is None:
            return
        document.status = "processing"
        session.add(document)
        session.commit()
        try:
            if document.content_type == "application/pdf":
                texts = extract_pdf_text(document.path)
            else:
                texts = [extract_image_text(document.path)]
            # Yarıda kalmış önceki denemenin sayfaları silinir.
            session.exec(delete(Page).where(Page.document_id == document_id))
            session.add_all(Page(document_id=document_id, number=i + 1, text=t) for i, t in enumerate(texts))
            document.status = "ready"
        except Exception:
            logger.exception("Belge %s işlenemedi", document_id)
            session.rollback()
            document.status = "failed"
        session.add(document)
        session.commit()


def process_pending() -> None:
    """İşlenmemiş ya da işlenirken sunucu kapandığı için yarıda kalmış belgeleri işler."""
    with Session(engine) as session:
        ids = session.exec(select(Document.id).where(Document.status.in_(["uploaded", "processing"]))).all()
    for document_id in ids:
        process_document(document_id)
