"""End-to-end tests for booklet rendering and PDF assembly."""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from booklet import (
    Brand,
    content_axes,
    draw_footer,
    new_page,
    render_cover,
    render_text_page,
    save_page,
    write_booklet,
)
from booklet.assemble import MARGIN_LR_IN, MARGIN_TB_IN

POINTS_PER_INCH = 72.0
PAGE_COUNT = 5

BRAND = Brand(
    name="Aurora Systems",
    url="aurora-systems.example.com",
    primary_color="#336699",
    accent_color="#a3c1dd",
)
LINK_URL = "https://aurora-systems.example.com"


def _content_page(out_path: Path, title: str) -> Path:
    fig = new_page()
    ax = content_axes(fig)
    ax.plot([0, 1, 2, 3], [2, 5, 3, 6])
    ax.set_title(title)
    draw_footer(fig, BRAND)
    return save_page(fig, out_path)


@pytest.fixture(scope="module")
def booklet_pdf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Assemble a five-page booklet once for all tests in this module."""
    work = tmp_path_factory.mktemp("booklet")
    pages = [
        render_cover(work / "p1.png", BRAND, title="Annual Summary", subtitle="Test Edition"),
        render_text_page(work / "p2.png", "About", ["First paragraph.", "Second one."], BRAND),
        _content_page(work / "p3.png", "Metric A"),
        _content_page(work / "p4.png", "Metric B"),
        _content_page(work / "p5.png", "Metric C"),
    ]
    return write_booklet(pages, work / "booklet.pdf", BRAND, link_url=LINK_URL)


def test_page_count_and_letter_landscape_size(booklet_pdf: Path) -> None:
    with pymupdf.open(booklet_pdf) as doc:
        assert doc.page_count == PAGE_COUNT
        for page in doc:
            assert page.rect.width == pytest.approx(11.0 * POINTS_PER_INCH, abs=1.0)
            assert page.rect.height == pytest.approx(8.5 * POINTS_PER_INCH, abs=1.0)


def test_pages_respect_print_margin(booklet_pdf: Path) -> None:
    with pymupdf.open(booklet_pdf) as doc:
        for page in doc:
            (xref, *_rest) = page.get_images()[0]
            placed = page.get_image_rects(xref)[0]
            assert placed.x0 >= MARGIN_LR_IN * POINTS_PER_INCH - 0.5
            assert placed.x1 <= page.rect.width - MARGIN_LR_IN * POINTS_PER_INCH + 0.5
            assert placed.y0 >= MARGIN_TB_IN * POINTS_PER_INCH - 0.5
            assert placed.y1 <= page.rect.height - MARGIN_TB_IN * POINTS_PER_INCH + 0.5
            # equal left/right margins => horizontally centered
            assert placed.x0 == pytest.approx(page.rect.width - placed.x1, abs=0.5)


def test_footer_links_point_to_brand_url(booklet_pdf: Path) -> None:
    with pymupdf.open(booklet_pdf) as doc:
        for index in range(1, doc.page_count):
            links = doc[index].get_links()
            assert len(links) == 2, f"page {index + 1} should have logo + url links"
            assert {link["uri"] for link in links} == {LINK_URL}
            placed = doc[index].get_image_rects(doc[index].get_images()[0][0])[0]
            for link in links:
                assert placed.contains(link["from"])


def test_page_numbers_are_extractable_text(booklet_pdf: Path) -> None:
    with pymupdf.open(booklet_pdf) as doc:
        assert "Page 2 of 5" in doc[1].get_text()
        assert "Page 5 of 5" in doc[4].get_text()
        assert "Page 1 of 5" not in doc[0].get_text()  # cover stays unnumbered


def test_cover_uses_custom_brand_color(tmp_path: Path) -> None:
    cover = render_cover(tmp_path / "cover.png", BRAND, title="Color Check")
    with Image.open(cover) as image:
        assert image.getpixel((20, 20)) == (0x33, 0x66, 0x99)


def test_write_booklet_rejects_empty_page_list(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no pages"):
        write_booklet([], tmp_path / "empty.pdf", BRAND)
