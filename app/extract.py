import ctypes
import re
from collections import Counter

import pdfplumber
import pypdfium2 as pdfium
import pypdfium2.raw as raw
import pytesseract
from PIL import Image

# Taranmış sayılan sayfalar bu çözünürlükte resme çevrilip OCR'a gider.
OCR_DPI = 300
# Metin katmanında bundan az karakter (boşluksuz) varsa sayfa taranmış sayılır;
# taranmış sayfadaki sayfa numarası, damga gibi küçük metinler OCR'ı engellemesin.
MIN_TEXT_CHARS = 50
# Gömülü resimlerde bu güvenin altındaki kelimeler atılır (logo, çizgi gibi çöp okumalar).
MIN_IMAGE_WORD_CONF = 60
# Kısa kenarı bundan küçük gömülü resimde okunabilir yazı olamaz; OCR'a gönderilmez.
MIN_IMAGE_PX = 20
# Art arda başlık satırları toplamda bundan uzunsa kalın yazılmış paragraftır.
MAX_HEADING_CHARS = 150
BULLET = re.compile(r"^[•\-–*▪●◦■]")
CAPTION = re.compile(r"^(fig\.?|figure|table|şekil|tablo|resim)\s*\d", re.IGNORECASE)
SECTION_NUMBER = re.compile(r"^(\d{1,3}|[a-z])(\.\d{1,3})*\.?$")


def extract_pdf_text(path: str) -> list[tuple[str, str]]:
    """PDF'i sayfa sayfa okur; metin katmanı boş ya da çok kısa sayfalarda OCR kullanır.

    (metin, kaynak) listesi döndürür; kaynak "text" (metin katmanı) ya da "ocr".
    """
    pdf = pdfium.PdfDocument(path)
    plumber = pdfplumber.open(path)
    try:
        bookmarks = read_bookmarks(pdf)
        pages, styles, sizes = [], {}, Counter()
        for i, (page, plumber_page) in enumerate(zip(pdf, plumber.pages)):
            textpage = page.get_textpage()
            text = textpage.get_text_bounded()
            if len("".join(text.split())) < MIN_TEXT_CHARS: # Metin yoksa OCR'a geç
                pages.append((extract_image_text(page.render(scale=OCR_DPI / 72).to_pil()), "ocr"))
            else:
                pages.append((extract_text_page(plumber_page, page, textpage), "text"))
                if not bookmarks:
                    styles[i] = line_styles(textpage, sizes)
            textpage.close()
            page.close()
        # Başlıklar "# " ile işaretlenir; yer imi varsa onlar, yoksa yazı tipi kuralları.
        body_size = sizes.most_common(1)[0][0] if sizes else 0
        for i, (text, source) in enumerate(pages):
            if bookmarks:
                pages[i] = (mark_bookmarks(text, bookmarks.get(i, [])) if source == "text" else text, source)
            elif i in styles:
                pages[i] = (mark_font_headings(text, styles[i], body_size), source)
        return pages
    finally:
        plumber.close()
        pdf.close()


def read_bookmarks(pdf: pdfium.PdfDocument) -> dict[int, list[str]]:
    """Yer imi başlıklarını sayfa numarasına göre döndürür."""
    bookmarks = {}
    for bookmark in pdf.get_toc():
        dest = bookmark.get_dest()
        title = " ".join(bookmark.get_title().split())
        if dest is not None and title:
            bookmarks.setdefault(dest.get_index(), []).append(title)
    return bookmarks


def mark_bookmarks(text: str, titles: list[str]) -> str:
    """Yer imi başlığının sayfadaki satırlarını işaretler; bulunamazsa sayfa başına ekler.

    Satır başında bölüm numarası olabilir (yer imi "Introduction", sayfada "1 Introduction").
    """
    lines = text.splitlines()
    key = lambda s: "".join(s.split()).lower()
    missing, start = [], 0
    for title in titles:
        target = key(title)
        # Önce birebir eşleşme; yoksa numaralı (ayrı satırdaki sayfa numarası önek sanılmasın).
        found = find_lines(lines, start, lambda s: s == target) or find_lines(
            lines, start, lambda s: s.endswith(target) and SECTION_NUMBER.match(s[: -len(target)]) is not None)
        if found:
            for k in range(found[0], found[1] + 1):
                lines[k] = "# " + lines[k].strip()
            start = found[1] + 1
        else:
            missing.append("# " + title)
    return "\n".join(missing + lines)


def find_lines(lines: list[str], start: int, matches) -> tuple[int, int] | None:
    """Birleşik hali eşleşen ilk satır aralığı; başlık en çok 3 satıra bölünmüş olabilir."""
    for i in range(start, len(lines)):
        joined = ""
        for j in range(i, min(i + 3, len(lines))):
            joined += "".join(lines[j].split()).lower()
            if joined and matches(joined):
                return i, j
    return None


def line_styles(textpage: pdfium.PdfTextPage, sizes: Counter) -> dict[str, tuple[float, float]]:
    """Satır metni -> (ortalama yazı boyutu, kalın karakter oranı); boyutları belge sayacına ekler."""
    styles, start = {}, 0
    n = textpage.count_chars()
    for i in range(n + 1):
        if i < n and chr(raw.FPDFText_GetUnicode(textpage.raw, i)) not in "\r\n":
            continue
        line_sizes, bold = [], 0
        for k in range(start, i):
            if raw.FPDFText_IsGenerated(textpage.raw, k) == 1 or chr(raw.FPDFText_GetUnicode(textpage.raw, k)).isspace():
                continue
            line_sizes.append(round(raw.FPDFText_GetFontSize(textpage.raw, k) * 2) / 2)
            bold += is_bold(textpage, k)
        if line_sizes:
            sizes.update(line_sizes)
            styles[textpage.get_text_range(start, i - start).strip()] = (sum(line_sizes) / len(line_sizes), bold / len(line_sizes))
        start = i + 1
    return styles


def is_bold(textpage: pdfium.PdfTextPage, i: int) -> bool:
    if raw.FPDFText_GetFontWeight(textpage.raw, i) >= 600:
        return True
    name = ctypes.create_string_buffer(256)
    raw.FPDFText_GetFontInfo(textpage.raw, i, name, 256, None)
    return b"bold" in name.value.lower()


def mark_font_headings(text: str, styles: dict[str, tuple[float, float]], body_size: float) -> str:
    """Tamamı kalın ya da gövdeden büyük, kısa, cümle gibi bitmeyen satırları başlık olarak işaretler."""
    lines = text.splitlines()
    marked = [is_font_heading(line.strip(), styles, body_size) for line in lines]
    # Art arda işaretli satırlar tek başlık sayılır; çok uzunsa (kalın paragraf) başlık değildir.
    i = 0
    while i < len(lines):
        if not marked[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(lines) and (marked[j + 1] or not lines[j + 1].strip()):
            j += 1
        group = [k for k in range(i, j + 1) if marked[k]]
        if sum(len(lines[k].strip()) for k in group) > MAX_HEADING_CHARS:
            for k in group:
                marked[k] = False
        i = j + 1
    return "\n".join("# " + line.strip() if m else line for line, m in zip(lines, marked))


def is_font_heading(line: str, styles: dict[str, tuple[float, float]], body_size: float) -> bool:
    if line not in styles or line.startswith("|") or len(line) > 100:
        return False
    size, bold = styles[line]
    letters = sum(c.isalpha() for c in line)
    return (
        (bold >= 0.95 or size >= body_size * 1.15)
        and not line.rstrip(")").endswith((".", ",", ";"))
        and "=" not in line and not line.startswith("(")
        and not BULLET.match(line)
        and not CAPTION.match(line)
        and letters >= 4 and letters >= len("".join(line.split())) / 2  # formül, sayı satırı değil
    )


def extract_text_page(page: pdfplumber.page.Page, pdfium_page: pdfium.PdfPage, textpage: pdfium.PdfTextPage) -> str:
    """Metin katmanlı sayfayı okur; tabloları Markdown, gömülü resimlerdeki yazıyı OCR ile yerlerine koyar.

    Düz metin pypdfium2'den, PDF'teki sırasıyla gelir: pdfplumber dar harf aralığında kelimeleri
    birleştiriyor, iki sütunlu sayfada satırları karıştırıyor. pdfplumber sadece tablo bulmak için.
    """
    blocks = [(t.bbox, table_to_markdown(extract_table_cells(t, textpage, page.height))) for t in page.find_tables()]
    blocks += extract_embedded_images(page, pdfium_page)
    if not blocks:
        return textpage.get_text_bounded()

    def block_at(i: int) -> int | None:
        left, bottom, right, top = textpage.get_charbox(i)
        cx, cy = (left + right) / 2, page.height - (bottom + top) / 2
        return next((k for k, ((x0, t, x1, b), _) in enumerate(blocks) if x0 <= cx <= x1 and t <= cy <= b), None)

    n = textpage.count_chars()
    owners = [block_at(i) for i in range(n)]
    # Tablo, ilk karakterinin yerine; karakteri olmayan blok (resim) altından başlayan ilk metnin önüne konur.
    anchors = {}
    for k, ((_, top, _, bottom), _) in enumerate(blocks):
        anchor = next((i for i, owner in enumerate(owners) if owner == k), None)
        if anchor is None:
            anchor = next((i for i in range(n) if owners[i] is None and page.height - textpage.get_charbox(i)[3] >= bottom), n)
        anchors.setdefault(anchor, []).append(k)

    parts, start = [], None
    for i in range(n + 1):
        if i in anchors or i == n or owners[i] is not None:
            if start is not None:
                parts.append(textpage.get_text_range(start, i - start))
                start = None
            parts += [blocks[k][1] for k in anchors.get(i, [])]
            if i < n and owners[i] is None:
                start = i
        elif start is None:
            start = i
    return "\n\n".join(p.strip() for p in parts if p.strip())


def extract_embedded_images(page: pdfplumber.page.Page, pdfium_page: pdfium.PdfPage) -> list[tuple[tuple, str]]:
    """Sayfadaki gömülü resimleri OCR ile okur; (konum, metin) listesi döndürür."""
    scale = OCR_DPI / 72
    px0, ptop, px1, pbottom = page.bbox
    rendered = None
    results = []
    for im in page.images:
        if min(im["srcsize"]) < MIN_IMAGE_PX:
            continue
        bbox = (max(im["x0"], px0), max(im["top"], ptop), min(im["x1"], px1), min(im["bottom"], pbottom))
        if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            continue
        # Üstünde metin katmanı olan resim (ör. aranabilir tarama) zaten okunuyor.
        if len("".join(page.within_bbox(bbox).extract_text().split())) >= MIN_TEXT_CHARS:
            continue
        if rendered is None:
            rendered = pdfium_page.render(scale=scale).to_pil()
        x0, top, x1, bottom = bbox
        crop = rendered.crop(((x0 - px0) * scale, (top - ptop) * scale, (x1 - px0) * scale, (bottom - ptop) * scale))
        text = extract_confident_text(crop)
        if text:
            results.append((bbox, text))
    return results


def extract_confident_text(image: Image.Image) -> str:
    """Resmi OCR ile okur, güveni düşük kelimeleri atar; satırlar korunur."""
    data = pytesseract.image_to_data(image, lang="tur+eng", output_type=pytesseract.Output.DICT)
    lines = {}
    for word, conf, *line in zip(data["text"], data["conf"], data["block_num"], data["par_num"], data["line_num"]):
        if word.strip() and float(conf) >= MIN_IMAGE_WORD_CONF:
            lines.setdefault(tuple(line), []).append(word)
    return "\n".join(" ".join(words) for words in lines.values())


def extract_table_cells(table, textpage: pdfium.PdfTextPage, height: float) -> list[list[str | None]]:
    """Hücre sınırları pdfplumber'dan, hücre metni pypdfium2'den (kelime boşlukları doğru)."""
    return [
        [None if cell is None else textpage.get_text_bounded(cell[0], height - cell[3], cell[2], height - cell[1])
         for cell in row.cells]
        for row in table.rows
    ]


def table_to_markdown(rows: list[list[str | None]]) -> str:
    """Tamamen boş sütunları atıp tabloyu Markdown'a çevirir."""
    cells = [[" ".join((c or "").split()).replace("|", "\\|") for c in row] for row in rows]
    keep = [i for i in range(len(cells[0])) if any(row[i] for row in cells)]
    cells = [[row[i] for i in keep] for row in cells]
    lines = ["| " + " | ".join(cells[0]) + " |", "|" + " --- |" * len(keep)]
    lines += ["| " + " | ".join(row) + " |" for row in cells[1:]]
    return "\n".join(lines)


def extract_image_text(image: str | Image.Image) -> str:
    """Resimdeki metni Tesseract ile (Türkçe + İngilizce) okur."""
    return pytesseract.image_to_string(image, lang="tur+eng")
