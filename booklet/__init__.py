"""report-booklet-toolkit: print-safe, hyperlinked multi-page PDF reports.

Render pages as fixed-size PNGs (matplotlib or any other renderer), then
assemble them into a US Letter landscape PDF with a uniform print margin,
clickable footer links, and vector page numbers.
"""

from booklet.assemble import write_booklet
from booklet.brand import Brand
from booklet.cover import recolor_preserving_alpha, render_cover
from booklet.disclaimer import render_text_page
from booklet.footer import draw_footer
from booklet.pages import DPI, PAGE_PIXELS, content_axes, new_page, save_page

__all__ = [
    "DPI",
    "PAGE_PIXELS",
    "Brand",
    "content_axes",
    "draw_footer",
    "new_page",
    "recolor_preserving_alpha",
    "render_cover",
    "render_text_page",
    "save_page",
    "write_booklet",
]

__version__ = "0.1.0"
