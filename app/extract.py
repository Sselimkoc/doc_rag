import pypdfium2 as pdfium


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
