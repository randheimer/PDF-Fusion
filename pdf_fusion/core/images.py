"""Converts image files into single PDF pages."""

import os
import tempfile

from PIL import Image
from PyPDF2 import PdfReader, PdfWriter


def add_image_page(image_path: str, writer: PdfWriter) -> None:
    """
    Converts an image to a one-page PDF and adds that page to the writer.

    Transparent images are placed on a white background.

    Args:
        image_path: Path of the image file
        writer: PDF writer that receives the new page
    """
    image = Image.open(image_path)

    # Convert to RGB if necessary
    if image.mode in ("RGBA", "LA", "P"):
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")

        # Paste the image over white, using its transparency as the mask
        alpha_mask = image.split()[-1] if image.mode in ("RGBA", "LA") else None
        rgb_image.paste(image, mask=alpha_mask)
        image = rgb_image
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Save as a temporary PDF
    temp_pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    try:
        image.save(temp_pdf_path, "PDF", resolution=100.0, quality=95)
        writer.add_page(PdfReader(temp_pdf_path).pages[0])
    finally:
        # Always delete, otherwise a failed export leaves a file in %TEMP%
        os.unlink(temp_pdf_path)
