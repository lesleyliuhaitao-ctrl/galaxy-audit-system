from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "research_assets" / "research_data" / "full_sample_residual_pathology_audit.csv"
OUT_FIG = ROOT / "research_assets" / "derived_exports" / "full_sample_residual_pathology_map.png"
OUT_SUM = ROOT / "research_assets" / "derived_exports" / "full_sample_residual_pathology_map_summary.csv"

GROUP_ORDER = [
    "acm_better_102",
    "geom_hostage_22",
    "stellar_hostage_9",
    "gas_flat_hard31",
]

GROUP_LABELS = {
    "acm_better_102": "ACM better (102)",
    "geom_hostage_22": "Geometry hostages (22)",
    "stellar_hostage_9": "Stellar hostages (9)",
    "gas_flat_hard31": "Gas-flat hard31 (31)",
}

GROUP_COLORS = {
    "acm_better_102": "#1f77b4",
    "geom_hostage_22": "#d62728",
    "stellar_hostage_9": "#ff7f0e",
    "gas_flat_hard31": "#2ca02c",
}


def median_points(df, x_col, y_col):
    rows = []
    for group in GROUP_ORDER:
        sub = df[df["pathology_group"] == group]
        rows.append(
            {
                "pathology_group": group,
                "x_median": float(pd.to_numeric(sub[x_col], errors="coerce").median()),
                "y_median": float(pd.to_numeric(sub[y_col], errors="coerce").median()),
                "n": int(len(sub)),
            }
        )
    return pd.DataFrame(rows)


def scatter_group(ax, df, x_col, y_col, title, xlabel, ylabel, annotate=True, xlog=False, ylog=False):
    for group in GROUP_ORDER:
        sub = df[df["pathology_group"] == group].copy()
        x = pd.to_numeric(sub[x_col], errors="coerce")
        y = pd.to_numeric(sub[y_col], errors="coerce")
        valid = np.isfinite(x) & np.isfinite(y)
        sub = sub.loc[valid]
        x = x.loc[valid]
        y = y.loc[valid]
        if len(sub) == 0:
            continue
        ax.scatter(
            x,
            y,
            s=34,
            alpha=0.78,
            color=GROUP_COLORS[group],
            edgecolors="white",
            linewidths=0.4,
            label=GROUP_LABELS[group],
        )
        if annotate:
            xm = float(np.nanmedian(x))
            ym = float(np.nanmedian(y))
            ax.scatter([xm], [ym], s=120, color=GROUP_COLORS[group], edgecolors="black", linewidths=0.8, marker="X")
            ax.annotate(
                GROUP_LABELS[group],
                (xm, ym),
                xytext=(6, 6),
                textcoords="offset points",
                fontsize=8,
                color=GROUP_COLORS[group],
            )
    if xlog:
        ax.set_xscale("log")
    if ylog:
        ax.set_yscale("log")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)


def main():
    df = pd.read_csv(DATA_PATH)

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    scatter_group(
        axes[0, 0],
        df,
        "distance_rel_err_pct",
        "delta_cpp_mond_minus_acm",
        "Geometry Plane",
        "Distance Relative Error (%)",
        "Delta CPP (MOND - ACM)",
    )
    axes[0, 0].axhline(0.0, color="gray", linestyle="--", linewidth=1.0)

    scatter_group(
        axes[0, 1],
        df,
        "L3.6",
        "gas_to_light_proxy",
        "Mass / Baryon Plane",
        "L3.6",
        "Gas-to-light proxy (MHI / L3.6)",
        xlog=True,
        ylog=True,
    )

    scatter_group(
        axes[1, 0],
        df,
        "gas_abs_slope_outer_mean",
        "gas_outer_to_inner_ratio",
        "Outer Gas Shape Plane",
        "Outer gas slope",
        "Outer / inner gas ratio",
    )

    scatter_group(
        axes[1, 1],
        df,
        "gas_abs_curvature_outer_mean",
        "vgas_high_freq_power_frac",
        "Gas Structure vs Raw Spectrum",
        "Outer gas curvature",
        "Vgas high-frequency power fraction",
    )

    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(handles[:4], labels[:4], loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.98))

    fig.suptitle("Full-Sample Residual Pathology Map", fontsize=16, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.965])
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_FIG, dpi=220, bbox_inches="tight")
    plt.close(fig)

    summary = pd.concat(
        [
            median_points(df, "distance_rel_err_pct", "delta_cpp_mond_minus_acm").assign(panel="geometry"),
            median_points(df, "L3.6", "gas_to_light_proxy").assign(panel="mass_baryon"),
            median_points(df, "gas_abs_slope_outer_mean", "gas_outer_to_inner_ratio").assign(panel="outer_gas_shape"),
            median_points(df, "gas_abs_curvature_outer_mean", "vgas_high_freq_power_frac").assign(panel="gas_structure_spectrum"),
        ],
        ignore_index=True,
    )
    summary.to_csv(OUT_SUM, index=False)

    print("Saved:")
    print(OUT_FIG)
    print(OUT_SUM)


if __name__ == "__main__":
    main()
