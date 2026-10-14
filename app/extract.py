import pypdfium2 as pdfium
import pytesseract


def extract_pdf_text(path: str) -> list[str]:
    """PDF metin katmanını sayfa sayfa döndürür."""
    pdf = pdfium.PdfDocument(path)
    try:
        pages = []
        for page in pdf:
            textpage = page.get_textpage()
            pages.append(textpage.get_text_bounded())
            textpage.close()
            page.close()
        return pages
    finally:
        pdf.close()


def extract_image_text(path: str) -> str:
    """Resimdeki metni Tesseract ile (Türkçe + İngilizce) okur."""
    return pytesseract.image_to_string(path, lang="tur+eng")
