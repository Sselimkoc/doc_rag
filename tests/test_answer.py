from pathlib import Path

import pytest

from app import answer
from app.answer import answer_question, build_prompt, clean_answer, normalize
from app.config import DATA_DIR
from app.schemas import SearchResult


def source(text, score=0.7, page=1, chunk_id=None):
    return SearchResult(chunk_id=chunk_id or page, document_id=1, filename="doc.pdf", page=page, section=None,
                        kind="text", source="text", score=score, text=text)


@pytest.fixture
def pipeline(monkeypatch):
    """Arama ve modeli taklit eder; model çağrıları calls listesine yazılır."""
    calls = []

    def setup(sources, reply):
        monkeypatch.setattr(answer, "search", lambda *args, **kwargs: [])
        monkeypatch.setattr(answer, "to_results", lambda session, results: sources)
        monkeypatch.setattr(answer, "with_neighbors", lambda session, results, top: results)
        monkeypatch.setattr(answer, "chat_json", lambda system, user, schema: calls.append(user) or reply)
        return calls

    return setup


def test_tests_do_not_use_real_data_dir():
    assert DATA_DIR != Path("data")


# normalize

def test_normalize_unifies_case_quotes_dashes_and_whitespace():
    assert normalize("  “Haftada”\n en   ÇOK – 45 ’saat’ ") == "\"haftada\" en çok - 45 'saat'"


def test_normalize_drops_pdf_control_characters():
    # paperqa_pasa.pdf: "test\x02ing"; eskiden alıntı doğrulamayı bozuyordu.
    assert normalize("train\x02ing") == "training"


def test_normalize_applies_nfkc():
    assert normalize("ﬁle") == "file"


def test_normalize_matches_dotted_capital_i():
    # jet-02: alıntı "İlk başarılı uygulama…", kaynakta "Fakat ilk başarılı uygulama…".
    assert normalize("İlk İngilizler") == "ilk ingilizler"
    assert normalize("İlk başarılı") in normalize("Fakat ilk başarılı uygulama")


# clean_answer: değerlendirmede görülen gerçek model çıktıları

@pytest.mark.parametrize("raw, cleaned", [
    ("ACME'de hafta sonu fazla mesai yüzde 100 zamlı ödenir. (Source: [1], '4. Fazla Mesai' bölümünde "
     "'Hafta sonu yapılan mesai yüzde 100 zamlı ödenir' ifadesi.)",
     "ACME'de hafta sonu fazla mesai yüzde 100 zamlı ödenir."),
    ("Gecikme halinde aylık yüzde 5 faiz uygulanır. (15 Haziran 2026 - FT-2026-00187 - [1])",
     "Gecikme halinde aylık yüzde 5 faiz uygulanır."),
    ("Most tactical military aircraft are powered by low-bypass turbofan engines.[1][3][5]",
     "Most tactical military aircraft are powered by low-bypass turbofan engines."),
    ("Belirtir. (Source: [6] \"Table 2 (see Sec. 3).\") (Source: [4] \"CSF Tiers…\")", "Belirtir."),
    ("Cevap. (Kaynak 2: 'y (z)')", "Cevap."),
])
def test_clean_answer_removes_source_references(raw, cleaned):
    assert clean_answer(raw) == cleaned


@pytest.mark.parametrize("text", [
    "Partial (Tier 1), Risk Informed (Tier 2), Repeatable (Tier 3), Adaptive (Tier 4).",
    "Toplam 14.400 TL (KDV dahil).",
    "Tier sırası (IDENTIFY, PROTECT, DETECT).",
    "Değer [1] ve [2] arasında.",
    "eksik parantez)",
])
def test_clean_answer_keeps_regular_text(text):
    assert clean_answer(text) == text


# answer_question

def test_low_top_score_refuses_without_calling_model(pipeline):
    calls = pipeline([source("Türkiye'nin başkenti", score=0.39)], {})
    r = answer_question(None, "Türkiye'nin başkenti neresidir?")
    assert (r.answered, r.refusal, calls) == (False, "no_sources", [])


def test_no_sources_refuses(pipeline):
    calls = pipeline([], {})
    r = answer_question(None, "soru")
    assert (r.answered, r.refusal, calls) == (False, "no_sources", [])


@pytest.mark.parametrize("reply", [
    {"answerable": False, "answer": "", "citations": []},
    {"answerable": True, "answer": "  ", "citations": [{"source": 1, "quote": "x"}]},
    {},  # num_predict sınırına çarpan cevap (Vaka 44)
])
def test_model_refusal_or_empty_answer_is_not_in_sources(pipeline, reply):
    pipeline([source("Deneme süresi en çok iki ay olabilir.")], reply)
    r = answer_question(None, "soru")
    assert (r.answered, r.refusal) == (False, "not_in_sources")


def test_verified_quote_is_accepted_despite_case_quotes_and_whitespace(pipeline):
    pipeline([source("bunun süresi en çok\niki ay olabilir. Ancak “toplu” iş", page=10)],
             {"answerable": True, "answer": "En çok iki ay.", "citations": [
                 {"source": 1, "quote": "Bunun süresi en çok iki ay olabilir. Ancak \"toplu\""}]})
    r = answer_question(None, "Deneme süresi?")
    assert r.answered and r.refusal is None and r.unverified_quotes == 0
    assert [(c.filename, c.page) for c in r.citations] == [("doc.pdf", 10)]


def test_fabricated_quote_is_refused_as_unverified(pipeline):
    pipeline([source("Haftada en çok kırkbeş saattir.")],
             {"answerable": True, "answer": "37,5 saat", "citations": [{"source": 1, "quote": "otuz yedi buçuk saattir"}]})
    r = answer_question(None, "Haftalık çalışma süresi?")
    assert (r.answered, r.refusal, r.unverified_quotes) == (False, "unverified", 1)


def test_answer_without_citations_is_refused(pipeline):
    # Prompt 3'te görülen durum: doğru cevap ama boş alıntı listesi (Vaka 46).
    pipeline([source("Selimiye Camii")], {"answerable": True, "answer": "Selimiye Camii", "citations": []})
    r = answer_question(None, "soru")
    assert (r.answered, r.refusal, r.unverified_quotes) == (False, "unverified", 0)


def test_unverified_quotes_are_dropped_but_answer_kept(pipeline):
    pipeline([source("Garanti süresi asgari iki yıldır.")],
             {"answerable": True, "answer": "İki yıl.", "citations": [
                 {"source": 1, "quote": "asgari iki yıldır"}, {"source": 1, "quote": "uydurma alıntı"}]})
    r = answer_question(None, "soru")
    assert r.answered and len(r.citations) == 1 and r.unverified_quotes == 1


@pytest.mark.parametrize("index", [0, 3, -1, "1", None])
def test_invalid_source_number_is_unverified(pipeline, index):
    pipeline([source("metin a"), source("metin b", page=2)],
             {"answerable": True, "answer": "a", "citations": [{"source": index, "quote": "metin a"}]})
    assert answer_question(None, "soru").refusal == "unverified"


def test_quote_must_come_from_the_cited_source(pipeline):
    pipeline([source("birinci kaynak"), source("ikinci kaynak", page=2)],
             {"answerable": True, "answer": "x", "citations": [{"source": 1, "quote": "ikinci kaynak"}]})
    assert answer_question(None, "soru").refusal == "unverified"


def test_answer_text_is_cleaned(pipeline):
    pipeline([source("yüzde 100 zamlı ödenir")],
             {"answerable": True, "answer": "Yüzde 100. (Source: [1])", "citations": [{"source": 1, "quote": "yüzde 100 zamlı"}]})
    assert answer_question(None, "soru").answer == "Yüzde 100."


def test_prompt_numbers_sources_with_filename_and_page():
    prompt = build_prompt("Soru?", [source("birinci", page=3), source("ikinci", page=7)])
    assert "Question: Soru?" in prompt
    assert "[1] (doc.pdf, page 3)\nbirinci" in prompt and "[2] (doc.pdf, page 7)\nikinci" in prompt
