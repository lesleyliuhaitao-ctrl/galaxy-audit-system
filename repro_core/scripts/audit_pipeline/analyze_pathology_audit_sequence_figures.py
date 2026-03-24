from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Ellipse


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "research_assets" / "research_data" / "full_sample_residual_pathology_audit.csv"
OUT_DIR = ROOT / "research_assets" / "derived_exports"

GEOM_FIG = OUT_DIR / "pathology_geometry_hostages_focus.png"
STELLAR_FIG = OUT_DIR / "pathology_stellar_hostages_focus.png"
HARD31_FIG = OUT_DIR / "pathology_hard31_focus.png"
OUT_SUM = OUT_DIR / "pathology_sequence_figures_summary.csv"

COLORS = {
    "background": "#b8b8b8",
    "geom": "#c93a2f",
    "stellar": "#dd8a1f",
    "hard31": "#2b9a4a",
    "acm": "#2f6db5",
}


def add_confidence_ellipse(ax, x, y, color, alpha=0.14, lw=1.2, zorder=1):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    if len(x) < 3:
        return
    cov = np.cov(x, y)
    if not np.all(np.isfinite(cov)):
        return
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    angle = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
    # Use ~2 sigma envelope for visual grouping.
    width, height = 4 * np.sqrt(np.maximum(vals, 1e-12))
    ell = Ellipse(
        (np.mean(x), np.mean(y)),
        width=width,
        height=height,
        angle=angle,
        facecolor=color,
        edgecolor=color,
        alpha=alpha,
        lw=lw,
        zorder=zorder,
    )
    ax.add_patch(ell)


def style_axes(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=13, weight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.22, linestyle="--")
    for spine in ax.spines.values():
        spine.set_alpha(0.35)


def add_corner_label(ax, x, y, text, color, ha="left", va="top"):
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        color=color,
        fontsize=10,
        weight="bold",
        ha=ha,
        va=va,
        bbox=dict(
            boxstyle="round,pad=0.3",
            facecolor="white",
            edgecolor=color,
            alpha=0.9,
        ),
        zorder=6,
    )


def plot_background(ax, df, x_col, y_col):
    x = pd.to_numeric(df[x_col], errors="coerce")
    y = pd.to_numeric(df[y_col], errors="coerce")
    valid = np.isfinite(x) & np.isfinite(y)
    ax.scatter(
        x[valid],
        y[valid],
        s=22,
        color=COLORS["background"],
        alpha=0.06,
        edgecolors="none",
        zorder=1,
    )


def make_geometry_focus(df):
    fig, ax = plt.subplots(figsize=(8.2, 6.1))
    plot_background(ax, df, "distance_rel_err_pct", "delta_cpp_mond_minus_acm")

    sub = df[df["pathology_group"] == "geom_hostage_22"].copy()
    x = pd.to_numeric(sub["distance_rel_err_pct"], errors="coerce")
    y = pd.to_numeric(sub["delta_cpp_mond_minus_acm"], errors="coerce")
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    add_confidence_ellipse(ax, x, y, COLORS["geom"], alpha=0.12, zorder=2)
    ax.scatter(
        x,
        y,
        s=64,
        marker="D",
        color=COLORS["geom"],
        edgecolors="white",
        linewidths=0.6,
        alpha=0.95,
        zorder=3,
        label="Geometry hostages (22)",
    )
    add_corner_label(
        ax,
        0.44,
        0.56,
        "Distance sensitive\nD + e_D flips the verdict",
        COLORS["geom"],
        ha="center",
        va="center",
    )
    ax.axhline(0.0, color="gray", linestyle="--", linewidth=1.0, alpha=0.8)
    style_axes(
        ax,
        "Geometry Hostages: Distance-Edge Surrender Cluster",
        "Distance Relative Error (%)",
        "Delta CPP (MOND - ACM)",
    )
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(GEOM_FIG, dpi=240, bbox_inches="tight")
    plt.close(fig)


def make_stellar_focus(df):
    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    plot_background(ax, df, "L3.6", "gas_to_light_proxy")

    sub = df[df["pathology_group"] == "stellar_hostage_9"].copy()
    x0 = pd.to_numeric(sub["L3.6"], errors="coerce")
    y0 = pd.to_numeric(sub["gas_to_light_proxy"], errors="coerce")
    scale = pd.to_numeric(sub["best_ml_scale"], errors="coerce").fillna(1.0)

    valid = np.isfinite(x0) & np.isfinite(y0) & np.isfinite(scale) & (x0 > 0) & (y0 > 0) & (scale > 0)
    sub = sub.loc[valid]
    x0 = x0.loc[valid]
    y0 = y0.loc[valid]
    scale = scale.loc[valid]

    # Proxy relocation after conservative stellar M/L rescaling.
    x1 = x0 * scale
    y1 = y0 / scale

    add_confidence_ellipse(ax, x0, y0, COLORS["stellar"], alpha=0.10, zorder=2)
    add_confidence_ellipse(ax, x1, y1, COLORS["acm"], alpha=0.08, zorder=2)

    ax.scatter(
        x0,
        y0,
        s=64,
        marker="o",
        color=COLORS["stellar"],
        edgecolors="white",
        linewidths=0.6,
        zorder=3,
        label="Stellar hostages (original)",
    )
    ax.scatter(
        x1,
        y1,
        s=54,
        marker="^",
        color=COLORS["acm"],
        edgecolors="white",
        linewidths=0.6,
        zorder=4,
        label="Recovered under conservative M/L",
    )
    for xa, ya, xb, yb in zip(x0, y0, x1, y1):
        ax.annotate(
            "",
            xy=(xb, yb),
            xytext=(xa, ya),
            arrowprops=dict(arrowstyle="->", lw=1.1, color=COLORS["stellar"], alpha=0.8),
            zorder=3,
        )
    if len(x0) > 0:
        add_corner_label(
            ax,
            0.30,
            0.24,
            "Mass recovery\nconservative M/L shift",
            COLORS["stellar"],
            ha="center",
            va="center",
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    style_axes(
        ax,
        "Stellar Hostages: Conservative M/L Return Vectors",
        "L3.6",
        "Gas-to-light proxy (MHI / L3.6)",
    )
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(STELLAR_FIG, dpi=240, bbox_inches="tight")
    plt.close(fig)


def make_hard31_focus(df):
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.7))
    sub = df[df["pathology_group"] == "gas_flat_hard31"].copy()

    # Panel 1: outer gas shape
    ax = axes[0]
    plot_background(ax, df, "gas_abs_slope_outer_mean", "gas_outer_to_inner_ratio")
    x = pd.to_numeric(sub["gas_abs_slope_outer_mean"], errors="coerce")
    y = pd.to_numeric(sub["gas_outer_to_inner_ratio"], errors="coerce")
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    add_confidence_ellipse(ax, x, y, COLORS["hard31"], alpha=0.14, zorder=2)
    ax.scatter(
        x,
        y,
        s=62,
        marker="s",
        color=COLORS["hard31"],
        edgecolors="white",
        linewidths=0.6,
        alpha=0.95,
        zorder=3,
        label="hard31",
    )
    add_corner_label(
        ax,
        0.62,
        0.55,
        "Low-structure outer disk\nshape-poor persistence-rich",
        COLORS["hard31"],
        ha="center",
        va="center",
    )
    style_axes(
        ax,
        "Hard31 Focus I: Outer Gas Shape",
        "Outer gas slope",
        "Outer / inner gas ratio",
    )
    ax.legend(frameon=False, loc="upper right")

    # Panel 2: structure vs spectrum
    ax = axes[1]
    plot_background(ax, df, "gas_abs_curvature_outer_mean", "vgas_high_freq_power_frac")
    x = pd.to_numeric(sub["gas_abs_curvature_outer_mean"], errors="coerce")
    y = pd.to_numeric(sub["vgas_high_freq_power_frac"], errors="coerce")
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    add_confidence_ellipse(ax, x, y, COLORS["hard31"], alpha=0.14, zorder=2)
    ax.scatter(
        x,
        y,
        s=62,
        marker="P",
        color=COLORS["hard31"],
        edgecolors="white",
        linewidths=0.6,
        alpha=0.95,
        zorder=3,
        label="hard31",
    )
    add_corner_label(
        ax,
        0.74,
        0.56,
        "Blind-zone cluster\ncurvature-poor, not noise-free",
        COLORS["hard31"],
        ha="center",
        va="center",
    )
    style_axes(
        ax,
        "Hard31 Focus II: Curvature-Poor but Not Spectrum-Free",
        "Outer gas curvature",
        "Vgas high-frequency power fraction",
    )
    ax.legend(frameon=False, loc="upper right")

    fig.tight_layout()
    fig.savefig(HARD31_FIG, dpi=240, bbox_inches="tight")
    plt.close(fig)


def main():
    df = pd.read_csv(DATA_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    make_geometry_focus(df)
    make_stellar_focus(df)
    make_hard31_focus(df)

    summary = pd.DataFrame(
        [
            {"figure": GEOM_FIG.name, "focus_group": "geom_hostage_22", "n_focus": 22},
            {"figure": STELLAR_FIG.name, "focus_group": "stellar_hostage_9", "n_focus": 9},
            {"figure": HARD31_FIG.name, "focus_group": "gas_flat_hard31", "n_focus": 31},
        ]
    )
    summary.to_csv(OUT_SUM, index=False)

    print("Saved:")
    print(GEOM_FIG)
    print(STELLAR_FIG)
    print(HARD31_FIG)
    print(OUT_SUM)


if __name__ == "__main__":
    main()
