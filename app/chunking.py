import re

# Karakter; embedding modeli seçilince token'la ölçülüp ayarlanacak.
# Ölçüm: metin katmanında paragraf ayrımı yok, en uzun cümle ~1000 karakter.
TARGET_CHARS = 1100
MAX_CHARS = 1800
# Sayfa sonunda bundan kısa kalan parça öncekiyle birleştirilir.
MIN_CHARS = 200

# Bu kelimelerden sonraki nokta cümle sonu sayılmaz.
ABBREVIATIONS = {
    "vb", "vs", "vd", "bkz", "örn", "sn", "dr", "prof", "doç", "yrd", "öğr", "gör", "arş", "av",
    "no", "md", "s", "st", "mr", "mrs", "ms", "e.g", "i.e", "etc", "fig",
}
LIST_ITEM = re.compile(r"^\s*([•\-–*]|\d+[.)]|[a-zçğıöşü][.)])\s")
SENTENCE_END = re.compile(r"(?<=[.!?…])\s+(?=[\"“(\dA-ZÇĞİÖŞÜ])")


def chunk_page(text: str, section: str | None = None) -> tuple[list[tuple[str, str, str | None]], str | None]:
    """Sayfa metnini (tür, metin, bölüm) parçalarına böler; tür "text" ya da "table".

    Bölüm, parçanın başladığı yerdeki son başlık. Sonraki sayfaya devretmek için son bölüm de döner.
    """
    chunks = []
    caption = None
    for is_table, lines in split_tables(text):
        if is_table:
            # Tablodan önce kalan küçük metin (ör. "EK-1: ...") ayrı parça olmaz, tabloya başlık olur.
            if chunks and chunks[-1][0] == "text" and len(chunks[-1][1]) < MIN_CHARS:
                caption = chunks.pop()[1]
            chunks += [("table", c, section) for c in chunk_table(lines, caption)]
            caption = None
        else:
            units = split_units(lines, section)
            texts = pack(units)
            # Tablodan sonra kalan küçük metin (ör. sayfa numarası) önceki parçaya eklenir.
            if texts and chunks and len(texts[0][0]) < MIN_CHARS and len(chunks[-1][1]) + 1 + len(texts[0][0]) <= MAX_CHARS:
                kind, previous, previous_section = chunks.pop()
                chunks.append((kind, previous + "\n" + texts.pop(0)[0], previous_section))
            chunks += [("text", c, s) for c, s in texts]
            if units:
                section = units[-1][2]
            # Tablodan hemen önceki cümle tablonun başlığı olabilir.
            caption = units[-1][0] if units and len(units[-1][0]) <= 300 else None
    return chunks, section


def split_tables(text: str) -> list[tuple[bool, list[str]]]:
    """Metni ardışık tablo satırları ve düz metin olarak gruplar."""
    groups = []
    for line in text.splitlines():
        is_table = line.lstrip().startswith("|")
        if groups and groups[-1][0] == is_table:
            groups[-1][1].append(line)
        else:
            groups.append((is_table, [line]))
    return groups


def split_units(lines: list[str], section: str | None) -> list[tuple[str, bool, str | None]]:
    """Satırları cümlelere böler; (cümle, paragraf başı mı, bölüm) listesi döndürür.

    Boş satır ya da madde işaretiyle başlayan satır yeni paragraf başlatır;
    tamamı büyük harfli satır başlıktır, ardışık başlık satırları tek başlık sayılır.
    """
    paragraphs, current = [], []  # (metin, başlık mı)
    for line in lines:
        line = line.strip()
        # En az 5 harf: OCR'ın "KE" gibi kısa çöp okumaları başlık sayılmasın.
        is_heading = line.isupper() and len(line) <= 100 and sum(c.isalpha() for c in line) >= 5
        if not line or LIST_ITEM.match(line) or is_heading:
            if current:
                paragraphs.append((" ".join(current), False))
                current = []
            if is_heading and paragraphs and paragraphs[-1][1]:
                paragraphs[-1] = (f"{paragraphs[-1][0]} {line}", True)
            elif is_heading:
                paragraphs.append((line, True))
            elif line:
                current = [line]
        else:
            current.append(line)
    if current:
        paragraphs.append((" ".join(current), False))

    units = []
    for paragraph, is_heading in paragraphs:
        if is_heading:
            section = paragraph
        for i, sentence in enumerate(split_sentences(" ".join(paragraph.split()))):
            units += [(piece, i == 0 and j == 0, section) for j, piece in enumerate(split_long(sentence))]
    return units


def split_sentences(text: str) -> list[str]:
    sentences = []
    start = 0
    for m in SENTENCE_END.finditer(text):
        last_word = text[start:m.start()].rsplit(maxsplit=1)[-1].rstrip(".").lower()
        # Kısaltma ya da baş harf ("A.") ise cümle bitmemiştir.
        if last_word in ABBREVIATIONS or len(last_word) == 1:
            continue
        sentences.append(text[start:m.start()])
        start = m.end()
    sentences.append(text[start:])
    return [s for s in sentences if s]


def split_long(sentence: str) -> list[str]:
    """Sınırı aşan cümleyi kelime sınırından böler (ölçülen belgelerde olmadı)."""
    pieces, current = [], ""
    for word in sentence.split(" "):
        if current and len(current) + 1 + len(word) > MAX_CHARS:
            pieces.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    return pieces + [current] if current else pieces


def pack(units: list[tuple[str, bool, str | None]]) -> list[tuple[str, str | None]]:
    """Cümleleri hedef boyuta kadar birleştirir; komşu parçalar bir cümle örtüşür. (metin, bölüm) döndürür."""
    chunks, current, overlapped = [], [], False  # chunks: (cümleler, örtüşmeyle mi başlıyor)
    for unit in units:
        if current and len(join(current + [unit])) > TARGET_CHARS:
            chunks.append((current, overlapped))
            # Tek cümlelik parçanın tekrarı bütün parçayı tekrarlamak olur.
            overlapped = len(current) > 1 and len(join([current[-1], unit])) <= MAX_CHARS
            current = [current[-1]] if overlapped else []
        current.append(unit)
    if current:
        new = current[1:] if overlapped else current
        if chunks and len(join(current)) < MIN_CHARS and len(join(chunks[-1][0] + new)) <= MAX_CHARS:
            chunks[-1][0].extend(new)
        else:
            chunks.append((current, overlapped))
    # Bölüm, örtüşen cümleden sonraki ilk cümleninki; o bölümsüzse parçadaki ilk başlık.
    return [
        (join(us), next((u[2] for u in us[1 if started_with_overlap else 0:] if u[2]), None))
        for us, started_with_overlap in chunks
    ]


def join(units: list[tuple[str, bool, str | None]]) -> str:
    """Cümleleri birleştirir; paragraf başları yeni satırda."""
    return "".join(("\n" if new_par else " ") + s if k else s for k, (s, new_par, _) in enumerate(units))


def chunk_table(lines: list[str], caption: str | None) -> list[str]:
    """Tabloyu sığdığı sürece tek parça tutar; büyükse satır sınırından böler, her parçada başlık tekrarlanır."""
    prefix = f"{caption}\n" if caption else ""
    header, rows = lines[:2], lines[2:]
    whole = prefix + "\n".join(lines)
    if len(whole) <= MAX_CHARS:
        return [whole]
    chunks, current = [], []
    for row in rows:
        if current and len(prefix + "\n".join(header + current + [row])) > MAX_CHARS:
            chunks.append(prefix + "\n".join(header + current))
            current = []
        current.append(row)
    if current:
        chunks.append(prefix + "\n".join(header + current))
    return chunks
