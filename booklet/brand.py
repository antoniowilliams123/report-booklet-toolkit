"""Brand configuration shared by every page renderer in the toolkit.

A :class:`Brand` bundles the handful of visual identity choices (colors,
wordmark text, URL, optional logo) that must stay consistent across the
cover, disclaimer, footers, and the hyperlink pass in :mod:`booklet.assemble`.
Passing one object around keeps every page of a booklet on-brand without
sprinkling color literals through report code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Brand:
    """Visual identity for a booklet.

    Attributes:
        name: Organization wordmark rendered on the cover page.
        url: Display URL for footers and the cover (e.g. ``"example.com"``).
            Rendered as text; :func:`booklet.assemble.write_booklet` overlays
            the clickable link annotation.
        primary_color: Cover background color (any matplotlib color spec).
            Dark colors work best because the cover logo/wordmark are white.
        accent_color: Color for detail rules and secondary text on the cover.
        logo_path: Optional path to a logo PNG with transparency. Expected to
            be a dark logo on a transparent background; the cover recolors it
            to white while footers use it as-is on white pages.
    """

    name: str
    url: str = ""
    primary_color: str = "#2b3d4f"
    accent_color: str = "#9db4c8"
    logo_path: Path | None = None
