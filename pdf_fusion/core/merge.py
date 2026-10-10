"""Merges PDF files and images into one PDF. No GUI code in here."""

import os
from collections.abc import Callable, Sequence

from PyPDF2 import PdfReader, PdfWriter

from pdf_fusion.core.images import add_image_page


class MergeError(Exception):
    """Raised when an input file cannot be added to the output."""


def merge_to_pdf(
    paths: Sequence[str],
    output_path: str,
    progress: Callable[[int, int], None] | None = None,
) -> None:
    """
    Merges the given PDF and image files, in order, into one PDF file.

    The output file is only written when every input file was added.

    Args:
        paths: Input file paths, in output order
        output_path: Path of the PDF to write
        progress: Optional callback, called with (current, total) before each file

    Raises:
        MergeError: If an input file cannot be read. The message names the file.
    """
    writer = PdfWriter()
    total = len(paths)
    for number, path in enumerate(paths, 1):
        if progress is not None:
            progress(number, total)
        try:
            if path.lower().endswith(".pdf"):
                _add_pdf_pages(path, writer)
            else:
                add_image_page(path, writer)
        except Exception as exc:
            # Without the file name it is unclear which file stopped the export
            name = os.path.basename(path)
            raise MergeError(f"Could not process '{name}': {exc}") from exc

    with open(output_path, "wb") as output_file:
        writer.write(output_file)


def _add_pdf_pages(pdf_path: str, writer: PdfWriter) -> None:
    """Adds all pages of a PDF to the writer."""
    for page in PdfReader(pdf_path).pages:
        writer.add_page(page)
