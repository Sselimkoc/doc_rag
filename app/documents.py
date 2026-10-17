import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import distinct, func
from sqlmodel import Session, select

from app.db import DATA_DIR, get_session
from app.models import Chunk, Document, Page
from app.processing import process_document
from app.schemas import DocumentSummary

UPLOAD_DIR = DATA_DIR / "uploads"
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=Document)
async def upload_document(
    file: UploadFile, background_tasks: BackgroundTasks, session: Session = Depends(get_session)
):
    suffix = ALLOWED_TYPES.get(file.content_type)
    if suffix is None:
        raise HTTPException(415, "Sadece PDF, JPG ve PNG desteklenir.")

    content = await file.read()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(content)

    document = Document(
        filename=file.filename,
        content_type=file.content_type,
        size=len(content),
        path=str(path),
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    background_tasks.add_task(process_document, document.id)
    return document


@router.get("", response_model=list[DocumentSummary])
def list_documents(session: Session = Depends(get_session)):
    documents = session.exec(select(Document).order_by(Document.created_at.desc())).all()
    pages = dict(session.exec(select(Page.document_id, func.count()).group_by(Page.document_id)).all())
    ocr_pages = dict(
        session.exec(
            select(Chunk.document_id, func.count(distinct(Chunk.page)))
            .where(Chunk.source == "ocr")
            .group_by(Chunk.document_id)
        ).all()
    )
    return [
        DocumentSummary(
            **d.model_dump(exclude={"path"}),
            page_count=pages.get(d.id, 0),
            ocr_page_count=ocr_pages.get(d.id, 0),
        )
        for d in documents
    ]


@router.get("/{document_id}/file")
def get_document_file(document_id: int, session: Session = Depends(get_session)):
    document = session.get(Document, document_id)
    if document is None or not Path(document.path).exists():
        raise HTTPException(404, "Belge bulunamadı.")
    return FileResponse(
        document.path,
        media_type=document.content_type,
        filename=document.filename,
        content_disposition_type="inline",
    )


@router.get("/{document_id}/text")
def get_document_text(document_id: int, session: Session = Depends(get_session)):
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(404, "Belge bulunamadı.")
    if document.status != "ready":
        raise HTTPException(409, f"Belgenin metni hazır değil (durum: {document.status}).")
    pages = session.exec(select(Page).where(Page.document_id == document_id).order_by(Page.number)).all()
    return [{"page": p.number, "text": p.text} for p in pages]
