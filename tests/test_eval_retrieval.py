from eval.retrieval import evidence_ranks
from app.models import Chunk

FILENAMES = {1: "kanun.pdf", 2: "diger.pdf"}
EVIDENCE = [{"document": "kanun.pdf", "page": 10, "text": "en çok iki ay olabilir"}]


def chunk(document_id, page, text):
    return Chunk(document_id=document_id, page=page, position=0, text=text, kind="text", source="text")


def test_other_chunk_of_same_page_counts_only_at_page_level():
    results = [
        (chunk(2, 10, "başka belge"), 0.9),
        (chunk(1, 10, "Deneme süresi dört aya kadar uzatılabilir."), 0.8),
        (chunk(1, 10, "Bunun süresi en çok\niki ay olabilir."), 0.7),
    ]
    assert evidence_ranks(results, EVIDENCE, FILENAMES) == (2, 3)


def test_evidence_text_on_another_page_does_not_count():
    results = [(chunk(1, 11, "en çok iki ay olabilir"), 0.9)]
    assert evidence_ranks(results, EVIDENCE, FILENAMES) == (None, None)
