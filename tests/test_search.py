import numpy as np
import pytest

from app import search as search_module
from app.embedding import EMBED_MODEL
from app.models import Chunk, Document, Embedding
from app.search import search, to_results


def unit(*values):
    v = np.array(values, dtype=np.float32)
    return v / np.linalg.norm(v)


@pytest.fixture
def indexed(session, monkeypatch):
    """İki belge, üç parça; soru vektörü (1, 0)."""
    for doc_id, name in [(1, "a.pdf"), (2, "b.pdf")]:
        session.add(Document(id=doc_id, filename=name, content_type="application/pdf", size=1, path=name, status="ready"))
    rows = [(1, 1, (1, 0)), (2, 1, (1, 1)), (3, 2, (0, 1))]
    for chunk_id, doc_id, vector in rows:
        session.add(Chunk(id=chunk_id, document_id=doc_id, page=chunk_id, position=0, text=f"parça {chunk_id}", kind="text", source="text"))
        session.add(Embedding(chunk_id=chunk_id, document_id=doc_id, model=EMBED_MODEL, vector=unit(*vector).tobytes()))
    session.commit()
    monkeypatch.setattr(search_module, "embed", lambda texts: np.stack([unit(1, 0)]))
    return session


def test_search_ranks_by_cosine_similarity(indexed):
    results = search(indexed, "soru", k=3)
    assert [c.id for c, _ in results] == [1, 2, 3]
    assert [round(s, 3) for _, s in results] == [1.0, 0.707, 0.0]


def test_search_returns_at_most_k(indexed):
    assert len(search(indexed, "soru", k=2)) == 2


def test_search_filters_by_document(indexed):
    assert [c.id for c, _ in search(indexed, "soru", k=3, document_ids=[2])] == [3]


def test_search_ignores_vectors_of_other_models(indexed):
    indexed.add(Chunk(id=4, document_id=1, page=4, position=0, text="eski", kind="text", source="text"))
    indexed.add(Embedding(chunk_id=4, document_id=1, model="eski-model", vector=unit(1, 0).tobytes()))
    indexed.commit()
    assert 4 not in [c.id for c, _ in search(indexed, "soru", k=10)]


def test_search_without_vectors_returns_empty(session, monkeypatch):
    monkeypatch.setattr(search_module, "embed", lambda texts: pytest.fail("embedding çağrılmamalı"))
    assert search(session, "soru") == []


def test_to_results_adds_filenames(indexed):
    results = to_results(indexed, search(indexed, "soru", k=3))
    assert [(r.filename, r.page) for r in results] == [("a.pdf", 1), ("a.pdf", 2), ("b.pdf", 3)]
