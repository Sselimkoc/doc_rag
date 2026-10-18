import urllib.error

import numpy as np
import pytest
from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, select

from app import db, embedding, processing
from app.documents import list_documents
from app.models import Chunk, Document, Embedding, Page

PAGE = "# 1. Kapsam\n" + " ".join(f"Cümle {i} biraz uzunca bir metin içerir." for i in range(60))


@pytest.fixture
def fresh_db():
    """Geçici DOC_RAG_DATA altındaki veritabanı, her testte boş."""
    SQLModel.metadata.drop_all(db.engine)
    db.init_db()
    yield db.engine


@pytest.fixture
def fake_models(monkeypatch):
    monkeypatch.setattr(processing, "extract_pdf_text", lambda path: [(PAGE, "text"), ("İkinci sayfa metni.", "text")])
    monkeypatch.setattr(processing, "extract_image_text", lambda path: "Taranmış sayfa metni.")
    monkeypatch.setattr(processing, "embed", lambda texts: np.ones((len(texts), 4), dtype=np.float32) / 2)


def add_document(engine, content_type="application/pdf", status="uploaded"):
    with Session(engine) as session:
        document = Document(filename="belge", content_type=content_type, size=1, path="belge", status=status)
        session.add(document)
        session.commit()
        return document.id


def counts(engine, document_id):
    with Session(engine) as session:
        status = session.get(Document, document_id).status
        return status, *(len(session.exec(select(m).where(m.document_id == document_id)).all()) for m in (Page, Chunk, Embedding))


def test_pdf_is_extracted_chunked_and_embedded(fresh_db, fake_models):
    doc = add_document(fresh_db)
    processing.process_document(doc)
    status, pages, chunks, vectors = counts(fresh_db, doc)
    assert (status, pages) == ("ready", 2) and chunks > 1 and vectors == chunks
    with Session(fresh_db) as session:
        first = session.exec(select(Chunk).where(Chunk.document_id == doc).order_by(Chunk.position)).first()
    assert first.section == "1. Kapsam" and first.source == "text"


def test_image_goes_through_ocr(fresh_db, fake_models):
    doc = add_document(fresh_db, content_type="image/png")
    processing.process_document(doc)
    with Session(fresh_db) as session:
        chunk = session.exec(select(Chunk).where(Chunk.document_id == doc)).one()
    assert (chunk.text, chunk.source) == ("Taranmış sayfa metni.", "ocr")


def test_failure_marks_failed_and_keeps_previous_chunks(fresh_db, fake_models, monkeypatch):
    # Vaka 38/41: belge "işleniyor"da kalmamalı, eski parçalar silinmemeli.
    doc = add_document(fresh_db)
    processing.process_document(doc)
    before = counts(fresh_db, doc)

    def ollama_down(texts):
        raise urllib.error.URLError("bağlantı yok")

    monkeypatch.setattr(processing, "embed", ollama_down)
    processing.process_document(doc)
    assert counts(fresh_db, doc) == ("failed", *before[1:])


def test_pending_documents_are_processed_and_missing_vectors_filled(fresh_db, fake_models):
    pending = add_document(fresh_db)
    stuck = add_document(fresh_db, status="processing")
    ready = add_document(fresh_db)
    processing.process_document(ready)
    with Session(fresh_db) as session:
        for e in session.exec(select(Embedding).where(Embedding.document_id == ready)).all():
            session.delete(e)
        session.commit()

    processing.process_pending()
    for doc in (pending, stuck, ready):
        status, _, chunks, vectors = counts(fresh_db, doc)
        assert status == "ready" and vectors == chunks > 0


def test_missing_column_is_added_to_existing_table(fresh_db):
    # Vaka 37: eski veritabanında chunk.section yoktu.
    with fresh_db.begin() as conn:
        conn.execute(text('ALTER TABLE chunk DROP COLUMN "section"'))
    db.add_missing_columns()
    assert "section" in {c["name"] for c in inspect(fresh_db).get_columns("chunk")}


def test_documents_from_before_soft_delete_are_still_listed(fresh_db):
    # Sonradan eklenen is_deleted sütunu eski satırlarda NULL kalır.
    doc = add_document(fresh_db)
    with fresh_db.begin() as conn:
        conn.execute(text('ALTER TABLE document DROP COLUMN "is_deleted"'))
    db.add_missing_columns()
    with Session(fresh_db) as session:
        assert session.get(Document, doc).is_deleted is None
        assert [d.id for d in list_documents(limit=None, offset=0, ids=None, session=session)] == [doc]


def test_embed_batches_requests_and_normalizes(monkeypatch):
    calls = []

    def fake_post(path, body, timeout=300):
        calls.append(len(body["input"]))
        return {"embeddings": [[3.0, 4.0] if t else [0.0, 0.0] for t in body["input"]]}

    monkeypatch.setattr(embedding, "post", fake_post)
    vectors = embedding.embed(["metin"] * 69 + [""])
    assert calls == [32, 32, 6] and vectors.dtype == np.float32
    assert np.allclose(vectors[0], [0.6, 0.8]) and np.allclose(vectors[-1], [0, 0])
