from datetime import datetime, timezone

from app.documents import list_documents
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
