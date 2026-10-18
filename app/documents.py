import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import distinct, func
from sqlmodel import Session, select

from app.db import DATA_DIR, get_session
from app.models import Chunk, Document, Page, not_deleted
from app.processing import process_document
from app.schemas import DocumentSummary

UPLOAD_DIR = DATA_DIR / "uploads"
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}
PENDING = ("uploaded", "processing")

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
def list_documents(
    limit: int | None = Query(None, ge=1, le=500),
    offset: int = Query(0, ge=0),
    ids: list[int] | None = Query(None),
    session: Session = Depends(get_session),
):
    # limit verilmezse tüm belgeler döner; id sırası aynı anda yüklenenlerde sayfaları sabit tutar.
    query = select(Document).where(not_deleted()).order_by(Document.created_at.desc(), Document.id.desc()).offset(offset).limit(limit)
    # Arayüz durum yenilerken yalnızca işlenmekte olan belgeleri sorar.
    if ids is not None:
        query = query.where(Document.id.in_(ids))
    documents = session.exec(query).all()
    ids = [d.id for d in documents]
    pages = dict(
        session.exec(
            select(Page.document_id, func.count()).where(Page.document_id.in_(ids)).group_by(Page.document_id)
        ).all()
    )
    ocr_pages = dict(
        session.exec(
            select(Chunk.document_id, func.count(distinct(Chunk.page)))
            .where(Chunk.source == "ocr", Chunk.document_id.in_(ids))
            .group_by(Chunk.document_id)
        ).all()
    )
    return [
        DocumentSummary(
            **d.model_dump(exclude={"path", "is_deleted"}),
            page_count=pages.get(d.id, 0),
            ocr_page_count=ocr_pages.get(d.id, 0),
        )
        for d in documents
    ]


def get_active(session: Session, document_id: int) -> Document:
    document = session.get(Document, document_id)
    if document is None or document.is_deleted:
        raise HTTPException(404, "Belge bulunamadı.")
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, session: Session = Depends(get_session)):
    document = get_active(session, document_id)
    # Arka planda işlenirken silinirse işlem yine de biter; karışıklık olmasın diye engellenir.
    if document.status in PENDING:
        raise HTTPException(409, "İşlenmekte olan belge silinemez.")
    document.is_deleted = True
    session.add(document)
    session.commit()


@router.post("/{document_id}/reprocess", status_code=202)
def reprocess_document(document_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    document = get_active(session, document_id)
    if document.status in PENDING:
        raise HTTPException(409, "Belge zaten işleniyor.")
    document.status = "uploaded"
    session.add(document)
    session.commit()
    background_tasks.add_task(process_document, document_id)


@router.get("/{document_id}/file")
def get_document_file(document_id: int, session: Session = Depends(get_session)):
    document = get_active(session, document_id)
    if not Path(document.path).exists():
        raise HTTPException(404, "Belge bulunamadı.")
    return FileResponse(
        document.path,
        media_type=document.content_type,
        filename=document.filename,
        content_disposition_type="inline",
    )


@router.get("/{document_id}/text")
def get_document_text(document_id: int, session: Session = Depends(get_session)):
    document = get_active(session, document_id)
    if document.status != "ready":
        raise HTTPException(409, f"Belgenin metni hazır değil (durum: {document.status}).")
    pages = session.exec(select(Page).where(Page.document_id == document_id).order_by(Page.number)).all()
    return [{"page": p.number, "text": p.text} for p in pages]
