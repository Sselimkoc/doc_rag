import pdfplumber
import pypdfium2 as pdfium
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


def extract_pdf_text(path: str) -> list[tuple[str, str]]:
    """PDF'i sayfa sayfa okur; metin katmanı boş ya da çok kısa sayfalarda OCR kullanır.

    (metin, kaynak) listesi döndürür; kaynak "text" (metin katmanı) ya da "ocr".
    """
    pdf = pdfium.PdfDocument(path)
    plumber = pdfplumber.open(path)
    try:
        pages = []
        for page, plumber_page in zip(pdf, plumber.pages):
            textpage = page.get_textpage()
            text = textpage.get_text_bounded()
            if len("".join(text.split())) < MIN_TEXT_CHARS: # Metin yoksa OCR'a geç
                pages.append((extract_image_text(page.render(scale=OCR_DPI / 72).to_pil()), "ocr"))
            else:
                pages.append((extract_text_page(plumber_page, page, textpage), "text"))
            textpage.close()
            page.close()
        return pages
    finally:
        plumber.close()
        pdf.close()


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
