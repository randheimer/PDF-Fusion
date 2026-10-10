"""Tests for the drag & drop callbacks of the main window. They need a display and skip without one."""

from types import SimpleNamespace

import pymupdf
import pytest
from PIL import Image

tk = pytest.importorskip("tkinter")

from pdf_fusion.ui.app import PDFFusionApp  # noqa: E402
from pdf_fusion.ui.window import MainWindow  # noqa: E402


@pytest.fixture
def window():
    try:
        root = MainWindow()
    except tk.TclError:
        pytest.skip("no display available")
    yield root
    root.destroy()


def test_drop_callbacks_return_the_accepted_action(window):
    app = PDFFusionApp(window)
    event = SimpleNamespace(data="", action="copy")

    assert app._accept_drop(event) == "copy"
    assert app.drop_files(event) == "copy"


def test_dropped_files_are_added_in_order_and_unsupported_ones_skipped(window, tmp_path):
    pdf = tmp_path / "my file.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(pdf)
    doc.close()
    picture = tmp_path / "picture.png"
    Image.new("RGB", (20, 20)).save(picture)
    note = tmp_path / "note.docx"
    note.write_bytes(b"not a supported format")

    # tkinterdnd2 passes a Tcl list with forward slashes; paths with spaces are braced
    data = f"{{{pdf.as_posix()}}} {picture.as_posix()} {note.as_posix()}"
    app = PDFFusionApp(window)

    assert app.drop_files(SimpleNamespace(data=data, action="copy")) == "copy"
    assert app.files == [pdf.as_posix(), picture.as_posix()]
