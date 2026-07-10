"""Configurable booklet cover page.

The cover is a solid block of the brand's primary color with a centered
white logo, wordmark, title/subtitle, thin accent detail rules, and the
brand URL in the lower-right corner. Logos are usually authored as dark
marks on a transparent background, so :func:`recolor_preserving_alpha`
turns them white while keeping the original anti-aliased edges intact.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

from booklet.brand import Brand
from booklet.pages import new_page, save_page


def recolor_preserving_alpha(
    image: np.ndarray, rgb: tuple[float, float, float] = (1.0, 1.0, 1.0)
) -> np.ndarray:
    """Replace an RGBA image's color channels while keeping its alpha mask.

    This is how a dark logo becomes a white logo on a dark cover: only the
    RGB channels are overwritten, so the shape, anti-aliasing, and any
    partial transparency of the original mark are preserved exactly.

    Args:
        image: ``(H, W, 4)`` float RGBA array in the 0-1 range
            (as returned by ``matplotlib.image.imread`` for a PNG).
        rgb: Replacement color as 0-1 floats.

    Returns:
        A new RGBA array with every pixel set to ``rgb`` and the original
        alpha channel untouched.

    Raises:
        ValueError: If the image has no alpha channel.
    """
    if image.ndim != 3 or image.shape[2] != 4:
        raise ValueError("expected an RGBA image with an alpha channel")
    recolored = image.copy()
    recolored[..., 0:3] = rgb
    return recolored


def render_cover(
    out_path: Path,
    brand: Brand,
    title: str,
    subtitle: str = "",
    *,
    font_family: str = "DejaVu Sans",
    logo_height_fraction: float = 0.26,
) -> Path:
    """Render the cover page PNG.

    Args:
        out_path: Destination ``.png`` path.
        brand: Brand supplying the background color, wordmark, accent color,
            URL, and optional logo.
        title: Report title, centered below the wordmark.
        subtitle: Optional smaller line under the title (e.g. a date range).
        font_family: Font family for all cover text.
        logo_height_fraction: Logo height as a fraction of the page height.

    Returns:
        ``out_path`` for chaining.
    """
    fig = new_page(facecolor=brand.primary_color)

    if brand.logo_path is not None:
        logo = recolor_preserving_alpha(mpimg.imread(brand.logo_path))
        target_px = logo_height_fraction * fig.get_figheight() * fig.dpi
        zoom = target_px / (logo.shape[0] * fig.dpi / 72.0)
        box = AnnotationBbox(
            OffsetImage(logo, zoom=zoom),
            (0.5, 0.62),
            xycoords="figure fraction",
            frameon=False,
        )
        fig.add_artist(box)

    fig.text(
        0.5,
        0.42,
        brand.name,
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        family=font_family,
        color="white",
    )
    for y in (0.475, 0.365):
        fig.add_artist(
            Line2D(
                [0.36, 0.64],
                [y, y],
                transform=fig.transFigure,
                color=brand.accent_color,
                linewidth=1.2,
            )
        )
    fig.text(
        0.5,
        0.30,
        title,
        ha="center",
        va="center",
        fontsize=21,
        family=font_family,
        color="white",
    )
    if subtitle:
        fig.text(
            0.5,
            0.245,
            subtitle,
            ha="center",
            va="center",
            fontsize=14,
            family=font_family,
            color=brand.accent_color,
        )
    if brand.url:
        fig.text(
            0.955,
            0.045,
            brand.url,
            ha="right",
            va="center",
            fontsize=12,
            fontweight="bold",
            family=font_family,
            color="white",
        )
    return save_page(fig, out_path)
