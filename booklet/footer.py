"""Footer band for content pages.

The footer has three slots on every content page:

* lower-left  — optional brand logo (rasterized with the page),
* center      — ``Page X of Y`` (added later as *vector* text by
  :mod:`booklet.assemble`, so it stays selectable/searchable and is always
  correct even if pages are reordered before assembly),
* lower-right — brand URL (rasterized here; made clickable by the link
  annotation pass in :mod:`booklet.assemble`).

The fractional geometry constants below are the single source of truth for
where those slots live. :mod:`booklet.assemble` reuses them to position the
link rectangles and the page-number text relative to the placed page image,
which is what keeps everything aligned after the print margin insets the page.
"""

from __future__ import annotations

import matplotlib.image as mpimg
from matplotlib.figure import Figure
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

from booklet.brand import Brand

#: Link rectangle over the footer logo, as fractions of the placed page image
#: ``(x0, y0, x1, y1)`` with the origin at the image's top-left (PDF axes).
LOGO_LINK_FRACTION: tuple[float, float, float, float] = (0.010, 0.910, 0.105, 0.990)

#: Link rectangle over the footer URL text (lower-right), same convention.
URL_LINK_FRACTION: tuple[float, float, float, float] = (0.800, 0.910, 0.990, 0.990)

#: Vertical position (fraction from image top) of the page-number baseline.
PAGE_NUMBER_Y_FRACTION: float = 0.962

#: Figure-fraction placement used when drawing the raster footer below.
_LOGO_CENTER: tuple[float, float] = (0.057, 0.048)
_URL_ANCHOR: tuple[float, float] = (0.955, 0.045)
_LOGO_HEIGHT_FRACTION: float = 0.052


def draw_footer(
    fig: Figure,
    brand: Brand,
    *,
    text_color: str = "#111111",
    font_family: str = "DejaVu Sans",
) -> None:
    """Draw the raster footer (logo lower-left, URL lower-right) on a page.

    The center ``Page X of Y`` slot is intentionally left empty here; see the
    module docstring for why page numbers are stamped at assembly time.

    Args:
        fig: Page figure created by :func:`booklet.pages.new_page`.
        brand: Brand supplying the logo path and URL text.
        text_color: Color of the URL text.
        font_family: Font family for the URL text.
    """
    if brand.logo_path is not None:
        image = mpimg.imread(brand.logo_path)
        target_px = _LOGO_HEIGHT_FRACTION * fig.get_figheight() * fig.dpi
        zoom = target_px / (image.shape[0] * fig.dpi / 72.0)
        box = AnnotationBbox(
            OffsetImage(image, zoom=zoom),
            _LOGO_CENTER,
            xycoords="figure fraction",
            frameon=False,
        )
        fig.add_artist(box)
    if brand.url:
        fig.text(
            *_URL_ANCHOR,
            brand.url,
            ha="right",
            va="center",
            fontsize=12,
            fontweight="bold",
            family=font_family,
            color=text_color,
        )
