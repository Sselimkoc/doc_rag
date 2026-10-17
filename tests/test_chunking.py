from app.chunking import MAX_CHARS, chunk_page, split_long, split_sentences


def sentences(n, words=12):
    return " ".join(f"Cümle {i} " + "kelime " * words + "biter." for i in range(n))


def test_split_sentences_skips_abbreviations_and_initials():
    text = "Bkz. Madde 5 uygulanır. A. Yılmaz örn. Ankara'da çalışır. İkinci cümle burada."
    assert split_sentences(text) == ["Bkz. Madde 5 uygulanır.", "A. Yılmaz örn. Ankara'da çalışır.", "İkinci cümle burada."]


def test_split_long_breaks_at_word_boundaries():
    pieces = split_long(" ".join(["kelime"] * 1000))
    assert len(pieces) > 1 and all(len(p) <= MAX_CHARS for p in pieces)
    assert " ".join(pieces).split() == ["kelime"] * 1000


def test_long_text_is_split_within_limit_with_one_sentence_overlap():
    chunks, _ = chunk_page(sentences(40))
    assert len(chunks) > 1
    assert all(kind == "text" and len(text) <= MAX_CHARS for kind, text, _ in chunks)
    for (_, first, _), (_, second, _) in zip(chunks, chunks[1:]):
        last_sentence = first.rsplit("Cümle ", 1)[1]
        assert second.startswith("Cümle " + last_sentence)


def test_heading_becomes_section_and_carries_to_next_page():
    chunks, section = chunk_page("# 2. Yıllık İzin\n" + sentences(3))
    assert chunks[0][2] == "2. Yıllık İzin" and section == "2. Yıllık İzin"
    next_chunks, _ = chunk_page(sentences(2), section)
    assert next_chunks[0][2] == "2. Yıllık İzin"


def test_small_table_is_one_chunk_with_preceding_caption():
    table = "| Malzeme | Adet |\n| --- | --- |\n| Kutu | 18 |"
    chunks, _ = chunk_page("Tablo 1: Kabul edilen malzemeler\n" + table)
    assert chunks == [("table", "Tablo 1: Kabul edilen malzemeler\n" + table, None)]


def test_large_table_repeats_header_in_every_chunk():
    header = ["| Kod | Açıklama |", "| --- | --- |"]
    rows = [f"| A{i:03d} | {'açıklama ' * 10}|" for i in range(60)]
    chunks, _ = chunk_page("\n".join(header + rows))
    assert len(chunks) > 1
    for kind, text, _ in chunks:
        assert kind == "table" and len(text) <= MAX_CHARS and text.splitlines()[:2] == header
    body = [line for _, text, _ in chunks for line in text.splitlines()[2:]]
    assert body == rows
