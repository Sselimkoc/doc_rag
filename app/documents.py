import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app.db import DATA_DIR, get_session
from app.extract import extract_pdf_text
from app.models import Document

UPLOAD_DIR = DATA_DIR / "uploads"
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=Document)
async def upload_document(file: UploadFile, session: Session = Depends(get_session)):
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
    return document


@router.get("", response_model=list[Document])
def list_documents(session: Session = Depends(get_session)):
    return session.exec(select(Document).order_by(Document.created_at.desc())).all()


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
    if document is None or not Path(document.path).exists():
        raise HTTPException(404, "Belge bulunamadı.")
    if document.content_type != "application/pdf":
        raise HTTPException(415, "Şimdilik sadece PDF metni çıkarılabiliyor.")
    pages = extract_pdf_text(document.path)
    return [{"page": i + 1, "text": text} for i, text in enumerate(pages)]
