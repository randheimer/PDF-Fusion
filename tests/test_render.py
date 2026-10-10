"""Tests for rendering PDF pages to images."""

import pymupdf
import pytest

from pdf_fusion.core.render import HAS_PYMUPDF, render_pdf_page


@pytest.mark.skipif(not HAS_PYMUPDF, reason="PyMuPDF is not installed")
def test_renders_the_first_page_at_the_given_scale(tmp_path):
    path = tmp_path / "page.pdf"
    doc = pymupdf.open()
    doc.new_page(width=200, height=100)
    doc.save(path)
    doc.close()

    img = render_pdf_page(str(path), scale=2.0)

    assert img.size == (400, 200)


def test_missing_file_gives_none(tmp_path):
    assert render_pdf_page(str(tmp_path / "missing.pdf")) is None
