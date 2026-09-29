"""Attachment text extraction."""
import io

from docx import Document
from pypdf import PdfWriter

from app.attachments import extract_text


def test_docx():
    d = Document()
    d.add_paragraph("Vertrag Klausel 3")
    b = io.BytesIO()
    d.save(b)
    text, _ = extract_text(b.getvalue(), "vertrag.docx", "")
    assert "Klausel 3" in text


def test_pdf_without_text_is_flagged_as_scan():
    w = PdfWriter()
    w.add_blank_page(200, 200)
    b = io.BytesIO()
    w.write(b)
    text, hint = extract_text(b.getvalue(), "scan.pdf", "application/pdf")
    assert text is not None and "Scan" in hint


def test_unknown_format_is_refused():
    text, hint = extract_text(b"MZ", "tool.exe", "application/octet-stream")
    assert text is None and hint
