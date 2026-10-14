import pypdfium2 as pdfium
import pytesseract
from PIL import Image

# Metin katmanı boş sayfalar bu çözünürlükte resme çevrilip OCR'a gider.
OCR_DPI = 300


def extract_pdf_text(path: str) -> list[str]:
    """PDF'i sayfa sayfa okur; metin katmanı boş sayfalarda OCR kullanır."""
    pdf = pdfium.PdfDocument(path)
    try:
        pages = []
        for page in pdf:
            textpage = page.get_textpage()
            text = textpage.get_text_bounded()
            textpage.close()
            if not text.strip():
                text = extract_image_text(page.render(scale=OCR_DPI / 72).to_pil())
            page.close()
            pages.append(text)
        return pages
    finally:
        pdf.close()


def extract_image_text(image: str | Image.Image) -> str:
    """Resimdeki metni Tesseract ile (Türkçe + İngilizce) okur."""
    return pytesseract.image_to_string(image, lang="tur+eng")
