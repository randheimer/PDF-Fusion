"""Tests for the GUI-independent merge logic."""

from pathlib import Path

import pymupdf
import pytest
from PIL import Image
from PyPDF2 import PdfReader

from pdf_fusion.core.merge import MergeError, merge_to_pdf


def make_pdf(path: Path, texts: list[str]) -> str:
    """Writes a PDF with one page per text and returns its path."""
    doc = pymupdf.open()
    for text in texts:
        doc.new_page().insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return str(path)


def make_image(path: Path, mode: str) -> str:
    """Writes a small image in the given mode and returns its path."""
    Image.new(mode, (60, 40)).save(path)
    return str(path)


def page_texts(path: Path) -> list[str]:
    """Returns the extracted text of every page, stripped."""
    return [page.extract_text().strip() for page in PdfReader(str(path)).pages]


def test_merges_pdfs_and_images_in_order(tmp_path):
    first = make_pdf(tmp_path / "first.pdf", ["A1", "A2"])
    picture = make_image(tmp_path / "picture.png", "RGB")
    last = make_pdf(tmp_path / "last.pdf", ["B1"])
    out = tmp_path / "out.pdf"

    merge_to_pdf([first, picture, last], str(out))

    texts = page_texts(out)
    assert len(texts) == 4
    assert texts[0] == "A1"
    assert texts[1] == "A2"
    assert texts[3] == "B1"


@pytest.mark.parametrize("mode", ["RGBA", "LA", "P", "L"])
def test_images_in_other_modes_become_one_page(tmp_path, mode):
    picture = make_image(tmp_path / f"{mode}.png", mode)
    out = tmp_path / "out.pdf"

    merge_to_pdf([picture], str(out))

    assert len(PdfReader(str(out)).pages) == 1


def test_reports_progress_for_every_file(tmp_path):
    first = make_pdf(tmp_path / "first.pdf", ["A"])
    picture = make_image(tmp_path / "picture.png", "RGB")
    seen = []

    merge_to_pdf([first, picture], str(tmp_path / "out.pdf"),
                 progress=lambda number, total: seen.append((number, total)))

    assert seen == [(1, 2), (2, 2)]


def test_error_names_the_failing_file_and_writes_nothing(tmp_path):
    good = make_pdf(tmp_path / "good.pdf", ["A"])
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"this is not a pdf")
    out = tmp_path / "out.pdf"

    with pytest.raises(MergeError, match="broken.pdf"):
        merge_to_pdf([good, str(broken)], str(out))

    assert not out.exists()
