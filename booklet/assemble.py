"""Assemble rendered page PNGs into a print-safe, hyperlinked PDF.

Two-stage pipeline:

1. **img2pdf** places each page image on US Letter landscape (11" x 8.5")
   inside a uniform print margin (:data:`MARGIN_LR_IN` left/right,
   :data:`MARGIN_TB_IN` top/bottom, ``FitMode.into``). Consumer printers
   cannot print to the paper edge, so a full-bleed layout would clip the
   footer logo and edge content; the margin insets the image and, because
   the left/right borders are equal, centers it horizontally.
2. **PyMuPDF** then overlays what raster pixels cannot carry: clickable
   link annotations over the footer logo and URL, and ``Page X of Y``
   as real vector text (selectable, searchable, and always numbered
   correctly no matter how the page images were produced or reordered).

Both overlays are positioned relative to the *actual placed image
rectangle* (``page.get_image_rects``), not full-page fractions — the print
margin shifts and shrinks the image, so full-page fractions would drift
off the footer marks.
"""

from __future__ import annotations

from pathlib import Path

import img2pdf
import pymupdf

from booklet.brand import Brand
from booklet.footer import (
    LOGO_LINK_FRACTION,
    PAGE_NUMBER_Y_FRACTION,
    URL_LINK_FRACTION,
)
from booklet.pages import PAGE_HEIGHT_IN, PAGE_WIDTH_IN

#: Uniform print-safe margin, in inches. Left/right are equal so FitMode.into
#: centers the page image horizontally; top/bottom keep footer and header
#: content clear of the printer's non-printable strip.
MARGIN_LR_IN: float = 0.45
MARGIN_TB_IN: float = 0.30


def _placed_image_rect(page: pymupdf.Page) -> pymupdf.Rect:
    """Return the rectangle where the page's image was actually drawn.

    Falls back to the full page rectangle for pages without images.
    """
    images = page.get_images()
    if not images:
        return page.rect
    return page.get_image_rects(images[0][0])[0]


def _fraction_rect(
    placed: pymupdf.Rect, fraction: tuple[float, float, float, float]
) -> pymupdf.Rect:
    """Map an ``(x0, y0, x1, y1)`` fraction of the placed image to PDF points."""
    x0, y0, x1, y1 = fraction
    return pymupdf.Rect(
        placed.x0 + placed.width * x0,
        placed.y0 + placed.height * y0,
        placed.x0 + placed.width * x1,
        placed.y0 + placed.height * y1,
    )


def _annotate(
    pdf_path: Path,
    link_url: str | None,
    page_count: int,
    number_pages: bool,
    skip_first_page_number: bool,
) -> None:
    """Single PyMuPDF pass: footer link annotations + vector page numbers."""
    doc = pymupdf.open(str(pdf_path))
    try:
        for index, page in enumerate(doc):
            placed = _placed_image_rect(page)
            if link_url:
                for fraction in (LOGO_LINK_FRACTION, URL_LINK_FRACTION):
                    page.insert_link(
                        {
                            "kind": pymupdf.LINK_URI,
                            "from": _fraction_rect(placed, fraction),
                            "uri": link_url,
                        }
                    )
            if number_pages and not (skip_first_page_number and index == 0):
                label = f"Page {index + 1} of {page_count}"
                fontsize = 9.0
                width = pymupdf.get_text_length(label, fontname="helv", fontsize=fontsize)
                baseline = pymupdf.Point(
                    placed.x0 + placed.width / 2 - width / 2,
                    placed.y0 + placed.height * PAGE_NUMBER_Y_FRACTION,
                )
                page.insert_text(
                    baseline,
                    label,
                    fontname="helv",
                    fontsize=fontsize,
                    color=(0.45, 0.45, 0.45),
                )
        temp_path = str(pdf_path) + ".tmp"
        doc.save(temp_path, deflate=True)
    finally:
        doc.close()
    Path(temp_path).replace(pdf_path)


def write_booklet(
    pages: list[Path],
    out_pdf: Path,
    brand: Brand,
    link_url: str | None = None,
    *,
    number_pages: bool = True,
    skip_first_page_number: bool = True,
) -> Path:
    """Assemble page PNGs into the final booklet PDF.

    Args:
        pages: Ordered page image paths (all rendered at the same size, e.g.
            via :func:`booklet.pages.save_page`).
        out_pdf: Destination ``.pdf`` path (parent directories are created).
        brand: Brand for the booklet. If ``link_url`` is omitted, a clickable
            link is derived from ``brand.url`` when present.
        link_url: URL for the footer link annotations (logo lower-left and
            URL lower-right on every page). Pass ``None`` with an empty
            ``brand.url`` to skip links entirely.
        number_pages: Stamp ``Page X of Y`` as vector text on each page.
        skip_first_page_number: Leave the cover (page 1) unnumbered; it still
            counts toward ``Y``.

    Returns:
        ``out_pdf`` for chaining.

    Raises:
        ValueError: If ``pages`` is empty.
    """
    if not pages:
        raise ValueError("cannot assemble a booklet with no pages")
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    # img2pdf's border tuple is (vertical, horizontal): the layout computes
    # fitwidth = pagewidth - 2 * border[1] and fitheight = pageheight - 2 * border[0].
    layout = img2pdf.get_layout_fun(
        pagesize=(img2pdf.in_to_pt(PAGE_WIDTH_IN), img2pdf.in_to_pt(PAGE_HEIGHT_IN)),
        border=(img2pdf.in_to_pt(MARGIN_TB_IN), img2pdf.in_to_pt(MARGIN_LR_IN)),
        fit=img2pdf.FitMode.into,
    )
    with open(out_pdf, "wb") as handle:
        handle.write(img2pdf.convert([str(page) for page in pages], layout_fun=layout))

    effective_url = link_url if link_url is not None else (brand.url or None)
    if effective_url and not effective_url.startswith(("http://", "https://")):
        effective_url = f"https://{effective_url}"
    _annotate(
        out_pdf,
        effective_url,
        page_count=len(pages),
        number_pages=number_pages,
        skip_first_page_number=skip_first_page_number,
    )
    return out_pdf
