"""Fixed-geometry page rendering helpers.

Every page in a booklet is rendered as a PNG with identical pixel dimensions:
US Letter landscape (11" x 8.5") at 192 DPI = 2112 x 1632 px. Rendering all
pages at one fixed size means the PDF assembly step (:mod:`booklet.assemble`)
can place each image identically, so footers, margins, and link rectangles
line up on every page of the document.
"""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from PIL import Image

#: Physical page size in inches (US Letter, landscape).
PAGE_WIDTH_IN: float = 11.0
PAGE_HEIGHT_IN: float = 8.5

#: Render resolution. 192 DPI makes each page exactly 2112 x 1632 px, which
#: opens at 100% zoom as a normal-sized letter page in PDF viewers.
DPI: int = 192

#: Expected pixel dimensions of every rendered page.
PAGE_PIXELS: tuple[int, int] = (
    int(PAGE_WIDTH_IN * DPI),
    int(PAGE_HEIGHT_IN * DPI),
)

#: Default axes rectangle (left, bottom, width, height) in figure fractions.
#: The bottom offset keeps chart content clear of the footer band.
CONTENT_RECT: tuple[float, float, float, float] = (0.07, 0.14, 0.86, 0.74)


def new_page(facecolor: str = "white") -> Figure:
    """Create an empty page-sized matplotlib figure.

    Args:
        facecolor: Background color of the page.

    Returns:
        A figure sized ``PAGE_WIDTH_IN x PAGE_HEIGHT_IN`` at :data:`DPI`.
    """
    fig = plt.figure(figsize=(PAGE_WIDTH_IN, PAGE_HEIGHT_IN), dpi=DPI)
    fig.patch.set_facecolor(facecolor)
    return fig


def content_axes(fig: Figure, rect: tuple[float, float, float, float] = CONTENT_RECT) -> Axes:
    """Add a plotting axes that leaves the footer band clear.

    Args:
        fig: Page figure from :func:`new_page`.
        rect: Axes rectangle ``(left, bottom, width, height)`` in figure
            fractions. The default reserves the bottom of the page for the
            footer drawn by :func:`booklet.footer.draw_footer`.

    Returns:
        The newly added axes.
    """
    return fig.add_axes(rect)


def save_page(fig: Figure, out_path: Path) -> Path:
    """Save a page figure as an opaque RGB PNG and close it.

    The alpha channel is flattened deliberately: img2pdf refuses images with
    transparency, so every page written here is guaranteed to be accepted by
    :func:`booklet.assemble.write_booklet`.

    Args:
        fig: Figure to save. Closed after saving.
        out_path: Destination ``.png`` path (parent directories are created).

    Returns:
        ``out_path`` for chaining.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    buffer.seek(0)
    with Image.open(buffer) as image:
        image.convert("RGB").save(out_path, format="PNG")
    return out_path
