import pdfplumber
import pypdfium2 as pdfium
import pytesseract
from PIL import Image

# Taranmış sayılan sayfalar bu çözünürlükte resme çevrilip OCR'a gider.
OCR_DPI = 300
# Metin katmanında bundan az karakter (boşluksuz) varsa sayfa taranmış sayılır;
# taranmış sayfadaki sayfa numarası, damga gibi küçük metinler OCR'ı engellemesin.
MIN_TEXT_CHARS = 50


def extract_pdf_text(path: str) -> list[str]:
    """PDF'i sayfa sayfa okur; metin katmanı boş ya da çok kısa sayfalarda OCR kullanır."""
    pdf = pdfium.PdfDocument(path)
    plumber = pdfplumber.open(path)
    try:
        pages = []
        for page, plumber_page in zip(pdf, plumber.pages):
            textpage = page.get_textpage()
            text = textpage.get_text_bounded()
            textpage.close()
            if len("".join(text.split())) < MIN_TEXT_CHARS: # Metin yoksa OCR'a geç
                text = extract_image_text(page.render(scale=OCR_DPI / 72).to_pil())
            else:
                text = extract_page_with_tables(plumber_page)
            page.close()
            pages.append(text)
        return pages
    finally:
        plumber.close()
        pdf.close()


def extract_page_with_tables(page: pdfplumber.page.Page) -> str:
    """Tablo dışı metni okur, tabloları sayfadaki yerlerine Markdown olarak koyar."""
    tables = sorted(page.find_tables(), key=lambda t: (t.bbox[1], t.bbox[0]))
    if not tables:
        return page.extract_text()

    def outside_tables(obj) -> bool:
        cx, cy = (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2
        return not any(x0 <= cx <= x1 and top <= cy <= bottom for x0, top, x1, bottom in (t.bbox for t in tables))

    rest = page.filter(outside_tables)
    parts = []
    x0, top, x1, bottom = page.bbox
    for table in tables:
        # Tablonun üstündeki ve yanındaki metin tablodan önce gelir.
        if table.bbox[3] > top:
            parts.append(rest.crop((x0, top, x1, table.bbox[3])).extract_text())
        parts.append(table_to_markdown(table.extract()))
        top = max(top, table.bbox[3])
    if bottom > top:
        parts.append(rest.crop((x0, top, x1, bottom)).extract_text())
    return "\n\n".join(p for p in parts if p.strip())


def table_to_markdown(rows: list[list[str | None]]) -> str:
    """Tamamen boş sütunları atıp tabloyu Markdown'a çevirir."""
    cells = [[(c or "").replace("\n", " ").replace("|", "\\|").strip() for c in row] for row in rows]
    keep = [i for i in range(len(cells[0])) if any(row[i] for row in cells)]
    cells = [[row[i] for i in keep] for row in cells]
    lines = ["| " + " | ".join(cells[0]) + " |", "|" + " --- |" * len(keep)]
    lines += ["| " + " | ".join(row) + " |" for row in cells[1:]]
    return "\n".join(lines)


def extract_image_text(image: str | Image.Image) -> str:
    """Resimdeki metni Tesseract ile (Türkçe + İngilizce) okur."""
    return pytesseract.image_to_string(image, lang="tur+eng")
