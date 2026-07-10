"""Plain text pages: about pages, disclaimers, methodology notes.

Renders a white page with a centered heading and left-aligned, wrapped body
paragraphs. Passing a :class:`~booklet.brand.Brand` also draws the standard
footer (logo + URL) so the page participates in the booklet's hyperlink and
page-numbering passes like any other content page.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import fill

from booklet.brand import Brand
from booklet.footer import draw_footer
from booklet.pages import new_page, save_page


def render_text_page(
    out_path: Path,
    title: str,
    paragraphs: list[str],
    brand: Brand | None = None,
    *,
    font_family: str = "DejaVu Sans",
    wrap_width: int = 128,
    body_fontsize: float = 11.5,
) -> Path:
    """Render a text-only page PNG.

    Args:
        out_path: Destination ``.png`` path.
        title: Heading centered near the top of the page.
        paragraphs: Body paragraphs; each is word-wrapped independently and
            separated by a blank line.
        brand: If given, the standard footer (logo lower-left, URL
            lower-right) is drawn on the page.
        font_family: Font family for all text on the page.
        wrap_width: Characters per wrapped line; tuned for landscape pages.
        body_fontsize: Body text size in points.

    Returns:
        ``out_path`` for chaining.
    """
    fig = new_page(facecolor="white")
    fig.text(
        0.5,
        0.90,
        title,
        ha="center",
        va="top",
        fontsize=20,
        fontweight="bold",
        family=font_family,
        color="#111111",
    )
    body = "\n\n".join(fill(paragraph, width=wrap_width) for paragraph in paragraphs)
    fig.text(
        0.07,
        0.80,
        body,
        ha="left",
        va="top",
        fontsize=body_fontsize,
        family=font_family,
        color="#1a1a1a",
        linespacing=1.55,
    )
    if brand is not None:
        draw_footer(fig, brand, font_family=font_family)
    return save_page(fig, out_path)
