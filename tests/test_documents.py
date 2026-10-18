import asyncio
import io
from datetime import datetime, timezone

import pytest
from fastapi import BackgroundTasks, HTTPException, UploadFile
from starlette.datastructures import Headers

from app import documents

from app.documents import delete_document, upload_document, get_document_text, list_documents, reprocess_document
from app.models import Chunk, Document, Page

SAME_TIME = datetime(2026, 10, 17, tzinfo=timezone.utc)


def add_documents(session, n):
    for i in range(n):
        session.add(Document(filename=f"belge{i}", content_type="application/pdf", size=1, path="x",
                             created_at=SAME_TIME))
    session.commit()


def names(documents):
    return [d.filename for d in documents]


def test_list_without_limit_returns_all_newest_first(session):
    add_documents(session, 3)
    assert names(list_documents(limit=None, offset=0, ids=None, session=session)) == ["belge2", "belge1", "belge0"]


def test_pages_cover_every_document_once_even_with_equal_timestamps(session):
    add_documents(session, 7)
    pages = [names(list_documents(limit=3, offset=o, ids=None, session=session)) for o in (0, 3, 6, 9)]
    assert [len(p) for p in pages] == [3, 3, 1, 0]
    assert sum(pages, []) == names(list_documents(limit=None, offset=0, ids=None, session=session))


def test_page_and_ocr_counts_are_per_document(session):
    add_documents(session, 2)
    session.add_all([Page(document_id=1, number=1, text="a"), Page(document_id=1, number=2, text="b"),
                     Chunk(document_id=1, page=2, position=0, text="b", kind="text", source="ocr")])
    session.commit()
    first, second = list_documents(limit=1, offset=1, ids=None, session=session) + list_documents(limit=1, offset=0, ids=None, session=session)
    assert (first.page_count, first.ocr_page_count) == (2, 1)
    assert (second.page_count, second.ocr_page_count) == (0, 0)


def test_ids_returns_only_requested_documents(session):
    add_documents(session, 5)
    assert names(list_documents(limit=None, offset=0, ids=[2, 4, 99], session=session)) == ["belge3", "belge1"]
    assert list_documents(limit=None, offset=0, ids=[], session=session) == []


def all_names(session):
    return names(list_documents(limit=None, offset=0, ids=None, session=session))


def status_code(call):
    with pytest.raises(HTTPException) as e:
        call()
    return e.value.status_code


def test_deleted_document_stays_in_db_but_is_hidden(session):
    add_documents(session, 2)
    session.get(Document, 1).status = "ready"
    session.commit()
    delete_document(1, session=session)
    assert all_names(session) == ["belge1"]
    assert session.get(Document, 1).is_deleted
    assert status_code(lambda: get_document_text(1, session=session)) == 404
    assert status_code(lambda: delete_document(1, session=session)) == 404


def test_document_being_processed_cannot_be_deleted_or_reprocessed(session):
    add_documents(session, 1)
    session.get(Document, 1).status = "processing"
    session.commit()
    assert status_code(lambda: delete_document(1, session=session)) == 409
    assert status_code(lambda: reprocess_document(1, BackgroundTasks(), session=session)) == 409


def test_reprocess_queues_document_again(session):
    add_documents(session, 1)
    session.get(Document, 1).status = "failed"
    session.commit()
    tasks = BackgroundTasks()
    reprocess_document(1, tasks, session=session)
    assert session.get(Document, 1).status == "uploaded" and len(tasks.tasks) == 1



def upload(session, content, content_type="application/pdf"):
    file = UploadFile(io.BytesIO(content), filename="belge", headers=Headers({"content-type": content_type}))
    return asyncio.run(upload_document(file, BackgroundTasks(), session=session))


def test_upload_rejects_content_that_does_not_match_its_type(session):
    # .pdf adı verilmiş başka bir dosya işlenmeden reddedilir.
    assert status_code(lambda: upload(session, b"MZ, Windows program")) == 415
    assert status_code(lambda: upload(session, b"%PDF-1.7 ...", "image/png")) == 415
    assert upload(session, b"%PDF-1.7 ...").status == "uploaded"


def test_upload_rejects_files_over_the_size_limit(session, monkeypatch):
    monkeypatch.setattr(documents, "MAX_UPLOAD_MB", 1)
    assert status_code(lambda: upload(session, b"%PDF-" + b"0" * (1024 * 1024))) == 413
    assert upload(session, b"%PDF-" + b"0" * 1000).status == "uploaded"
