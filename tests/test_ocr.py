import shutil

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.config import TESSERACT_CMD
from app.extract import extract_image_text

pytestmark = pytest.mark.skipif(not (TESSERACT_CMD or shutil.which("tesseract")), reason="Tesseract yok")

ROWS = [("Fatura No:", "FT-2026-00187"), ("Tarih:", "15 Haziran 2026"), ("Ara Toplam:", "12.000 TL"),
        ("Genel Toplam:", "14.400 TL"), ("Vade Tarihi:", "30 Haziran 2026")]


def test_label_value_rows_are_read_line_by_line():
    # tr_fatura.png: varsayılan düzende etiketler ve değerler ayrı bloklar olarak okunuyordu,
    # "Genel Toplam: 14.400 TL" alıntısı doğrulanamıyordu.
    font = ImageFont.load_default(size=32)
    image = Image.new("RGB", (900, 70 + 60 * len(ROWS)), "white")
    draw = ImageDraw.Draw(image)
    for i, (label, value) in enumerate(ROWS):
        draw.text((30, 40 + 60 * i), label, fill="black", font=font)
        draw.text((480, 40 + 60 * i), value, fill="black", font=font)
    lines = [line.strip() for line in extract_image_text(image).splitlines()]
    assert "Genel Toplam: 14.400 TL" in lines and "Fatura No: FT-2026-00187" in lines
