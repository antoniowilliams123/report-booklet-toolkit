"""End-to-end demo: a quarterly business report for a fictional company.

Generates synthetic KPI data for "Meridian Analytics" (seeded RNG, fully
reproducible), renders five pages — cover, about/disclaimer, and three chart
pages — and assembles them into a print-safe, hyperlinked PDF booklet.

Usage:
    python examples/quarterly_report.py [--out DIR]

Writes ``quarterly_report.pdf`` plus three ~1100px-wide PNG previews to the
output directory (default: ``docs/sample`` next to the repo root).
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
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

# Okabe-Ito colorblind-safe palette.
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9"]

MONTHS = [
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
]
SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Self-Serve"]
COST_CATEGORIES = ["Cloud & Infra", "Personnel", "Sales & Marketing", "G&A"]


def make_logo(out_path: Path) -> Path:
    """Draw a simple geometric mark: three nested rings, black on transparent."""
    fig = plt.figure(figsize=(3, 3), dpi=200)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    for radius, width in ((0.9, 0.055), (0.62, 0.085), (0.32, 0.32)):
        ax.add_patch(plt.Circle((0, 0), radius, fill=radius == 0.32, color="black", lw=width * 100))
    fig.savefig(out_path, transparent=True)
    plt.close(fig)
    return out_path


def synth_data(seed: int = 7) -> dict[str, np.ndarray]:
    """Generate reproducible synthetic KPIs for the report."""
    rng = np.random.default_rng(seed)
    base = np.array([4.2, 2.6, 1.8, 1.1])  # $M monthly revenue baseline per segment
    growth = np.array([0.012, 0.020, 0.015, 0.032])
    months = np.arange(12)
    revenue = base[:, None] * (1 + growth[:, None]) ** months
    revenue *= 1 + rng.normal(0, 0.035, size=revenue.shape)

    cost_base = np.array([1.9, 3.4, 2.2, 0.9])
    costs = cost_base[:, None] * (1 + 0.008) ** months
    costs *= 1 + rng.normal(0, 0.03, size=costs.shape)

    cohorts = 8
    retention = np.full((cohorts, cohorts), np.nan)
    for cohort in range(cohorts):
        horizon = cohorts - cohort
        churn = rng.uniform(0.04, 0.09)
        curve = 100 * (1 - churn) ** np.arange(horizon)
        curve[1:] *= 1 + rng.normal(0, 0.015, size=horizon - 1)
        retention[cohort, :horizon] = curve
    return {"revenue": revenue, "costs": costs, "retention": retention}


def style_axes(ax: plt.Axes) -> None:
    """Shared clean styling: no top/right spines, no background gridlines."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=11)


def revenue_page(out_path: Path, revenue: np.ndarray, brand: Brand) -> Path:
    """Grouped bar chart: monthly revenue by customer segment."""
    fig = new_page()
    ax = content_axes(fig)
    x = np.arange(len(MONTHS))
    width = 0.2
    for i, segment in enumerate(SEGMENTS):
        offset = (i - (len(SEGMENTS) - 1) / 2) * width
        ax.bar(x + offset, revenue[i], width=width, label=segment, color=PALETTE[i])
    ax.set_xticks(x, MONTHS)
    ax.set_ylabel("Revenue ($M)", fontsize=12)
    ax.set_title("Revenue by Segment — Trailing 12 Months", fontsize=17, pad=16)
    ax.legend(frameon=False, ncols=4, fontsize=11, loc="upper left")
    style_axes(ax)
    draw_footer(fig, brand)
    return save_page(fig, out_path)


def cost_page(out_path: Path, costs: np.ndarray, brand: Brand) -> Path:
    """Line chart: monthly operating costs by category."""
    fig = new_page()
    ax = content_axes(fig)
    x = np.arange(len(MONTHS))
    for i, category in enumerate(COST_CATEGORIES):
        ax.plot(x, costs[i], color=PALETTE[i], lw=2.4, marker="o", ms=5, label=category)
        ax.annotate(
            category,
            (x[-1], costs[i][-1]),
            xytext=(10, 0),
            textcoords="offset points",
            va="center",
            fontsize=11,
            color=PALETTE[i],
        )
    ax.set_xticks(x, MONTHS)
    ax.set_xlim(-0.4, len(MONTHS) + 1.4)  # headroom for the end-of-line labels
    ax.set_ylabel("Operating Cost ($M)", fontsize=12)
    ax.set_title("Operating Costs by Category — Trailing 12 Months", fontsize=17, pad=16)
    style_axes(ax)
    draw_footer(fig, brand)
    return save_page(fig, out_path)


def retention_page(out_path: Path, retention: np.ndarray, brand: Brand) -> Path:
    """Heatmap: customer retention by signup cohort."""
    fig = new_page()
    ax = content_axes(fig, rect=(0.10, 0.14, 0.78, 0.72))
    masked = np.ma.masked_invalid(retention)
    mesh = ax.pcolormesh(masked, cmap="Blues", vmin=50, vmax=100, edgecolors="white", lw=2)
    rows, cols = retention.shape
    for r in range(rows):
        for c in range(cols):
            value = retention[r, c]
            if np.isnan(value):
                continue
            ax.text(
                c + 0.5,
                r + 0.5,
                f"{value:.0f}",
                ha="center",
                va="center",
                fontsize=11,
                color="white" if value > 82 else "#1a1a1a",
            )
    ax.set_xticks(np.arange(cols) + 0.5, [f"M{c}" for c in range(cols)])
    ax.set_yticks(np.arange(rows) + 0.5, [f"Cohort {MONTHS[r]}" for r in range(rows)])
    ax.invert_yaxis()
    ax.set_xlabel("Months Since Signup", fontsize=12)
    ax.set_title("Customer Retention by Signup Cohort (%)", fontsize=17, pad=16)
    ax.tick_params(labelsize=11, length=0)
    fig.colorbar(mesh, ax=ax, fraction=0.03, pad=0.02, label="Retained (%)")
    draw_footer(fig, brand)
    return save_page(fig, out_path)


ABOUT_PARAGRAPHS = [
    "This report was generated automatically by report-booklet-toolkit as a demonstration of "
    "programmatic PDF report assembly. Meridian Analytics is a fictional company; every figure "
    "in this document is synthetic data produced by a seeded random number generator, so the "
    "report is fully reproducible from source.",
    "The document illustrates the toolkit's standard structure: a branded cover, this about "
    "page, and content pages that each carry the footer band — logo lower-left, page number "
    "center, and URL lower-right. The logo and URL are clickable link annotations added during "
    "PDF assembly.",
    "This material is provided for illustration only, without warranty of any kind, express or "
    "implied, including warranties of accuracy, completeness, or fitness for a particular "
    "purpose. It does not constitute professional advice, and no business decision should be "
    "based on its contents.",
]


def build_report(out_dir: Path) -> Path:
    """Render all pages and assemble the demo booklet. Returns the PDF path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    data = synth_data()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        brand = Brand(
            name="Meridian Analytics",
            url="meridian-analytics.example.com",
            primary_color="#1f3a52",
            accent_color="#9db4c8",
            logo_path=make_logo(work / "logo.png"),
        )
        pages = [
            render_cover(
                work / "p1.png",
                brand,
                title="Quarterly Business Review",
                subtitle="Q2 FY2026 — Synthetic Demonstration Data",
            ),
            render_text_page(work / "p2.png", "About This Report", ABOUT_PARAGRAPHS, brand),
            revenue_page(work / "p3.png", data["revenue"], brand),
            cost_page(work / "p4.png", data["costs"], brand),
            retention_page(work / "p5.png", data["retention"], brand),
        ]
        pdf = write_booklet(pages, out_dir / "quarterly_report.pdf", brand)
        previews = [(pages[0], "cover"), (pages[2], "revenue"), (pages[4], "retention")]
        for page_path, name in previews:
            with Image.open(page_path) as image:
                scale = 1100 / image.width
                preview = image.resize((1100, round(image.height * scale)), Image.LANCZOS)
                preview.save(out_dir / f"preview_{name}.png")
    return pdf


def main() -> None:
    """CLI entry point."""
    default_out = Path(__file__).resolve().parent.parent / "docs" / "sample"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=default_out, help="output directory")
    args = parser.parse_args()
    pdf = build_report(args.out)
    print(f"wrote {pdf} ({pdf.stat().st_size / 1e6:.1f} MB) + previews in {args.out}")


if __name__ == "__main__":
    main()
