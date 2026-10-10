"""Thumbnail images for the file list."""

import logging

from PIL import Image, ImageDraw

from pdf_fusion.core.render import render_pdf_page

THUMBNAIL_SIZE = (80, 80)

logger = logging.getLogger(__name__)


def placeholder(size: tuple[int, int] = THUMBNAIL_SIZE, text: str = "PDF") -> Image.Image:
    """
    Creates a gray placeholder image, for example for PDFs without a preview.

    Args:
        size: Tuple of (width, height) of the placeholder image
        text: Label of the placeholder

    Returns:
        PIL Image object with a gray background and the label
    """
    img = Image.new("RGB", size, "lightgray")
    draw = ImageDraw.Draw(img)
    draw.text((size[0] // 2 - 10, size[1] // 2 - 5), text, fill="black")
    return img


def make_thumbnail(path: str) -> Image.Image:
    """
    Creates the thumbnail of a PDF or image file.

    PDFs without a rendered page get the "PDF" placeholder. Unreadable image files get a
    "?" placeholder, so the error stays visible.
    """
    try:
        if path.lower().endswith(".pdf"):
            img = render_pdf_page(path, scale=0.3) or placeholder()
        else:
            img = Image.open(path)
        img.thumbnail(THUMBNAIL_SIZE)
        return img
    except Exception:
        logger.exception("Could not create thumbnail: %s", path)
        return placeholder(text="?")
