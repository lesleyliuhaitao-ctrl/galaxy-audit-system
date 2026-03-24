#!/usr/bin/env python
"""
Analyze the remaining 40 distance-hard MOND-favored galaxies.

Two questions:
1. Are they unusually gas-rich relative to the 22 distance-edge surrender systems
   and the 102 ACM-better galaxies?
2. Does a reasonable stellar M/L rescaling trigger trapdoor flips for ACM?
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_acm_vs_mond import mond_chi2_per_point
from analyze_mond_resistant_metadata_table import load_table1_explicit
from src.data_loader.load_sparc import load_sparc_galaxy_list, load_sparc_rotation_curve
from src.fitting.fit_sparc import chi2_sparc_galaxy_direct_local, fit_sparc_gated_background_model
from src.models.eta_path_integral import eta_local_gated_background_profile


MAIN7_GALAXIES = [
    "NGC3521",
    "NGC2841",
    "NGC3198",
    "NGC6946",
    "NGC2403",
    "NGC2903",
    "NGC5055",
]

G_CRIT = 3.0e-11
GATE_POWER = 1.0
BG_CONTROL_MODE = "shape_depth"
SHAPE_DEPTH_MODE = "c31_vflat"
SHAPE_C_CRIT = 2.6
SHAPE_DEPTH_CRIT = 2.1

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "research_assets" / "derived_exports"
OUT_GAS = OUT_DIR / "holdout40_gas_richness_summary.csv"
OUT_ML_RANKED = OUT_DIR / "holdout40_ml_sensitivity_ranked.csv"
OUT_ML_SUMMARY = OUT_DIR / "holdout40_ml_sensitivity_summary.csv"


def load_sparc_dict(galaxies=None):
    if galaxies is None:
        table = load_sparc_galaxy_list()
        galaxies = table["Galaxy"].astype(str).tolist()
    out = {}
    for galaxy in galaxies:
        rc = load_sparc_rotation_curve(galaxy)
        if rc is not None and len(rc) > 5:
            rc = rc.copy()
            rc["Galaxy"] = galaxy
            out[galaxy] = rc
    return out


def fit_current_trunk():
    summary_path = ROOT / "analysis_outputs" / "acm_vs_mond_summary.csv"
    if summary_path.exists():
        summary = pd.read_csv(summary_path).iloc[0]
        return (
            float(summary["acm_eta_base"]),
            float(summary["acm_beta_density"]),
            float(summary["acm_beta_bg"]),
            float(summary["acm_lambda_sup"]),
        )

    sparc_main7 = load_sparc_dict(MAIN7_GALAXIES)
    result = fit_sparc_gated_background_model(
        sparc_main7,
        use_direct=True,
        g_crit=G_CRIT,
        gate_power=GATE_POWER,
        bg_control_mode=BG_CONTROL_MODE,
        shape_depth_mode=SHAPE_DEPTH_MODE,
        shape_c_crit=SHAPE_C_CRIT,
        shape_depth_crit=SHAPE_DEPTH_CRIT,
    )
    return tuple(result.x)


def acm_cpp_for_rc(rc_data, params):
    eta_base, beta_density, beta_bg, lambda_sup = params
    profile = eta_local_gated_background_profile(
        rc_data,
        eta_base=eta_base,
        beta_density=beta_density,
        beta_bg=beta_bg,
        lambda_sup=lambda_sup,
        galaxy_name=rc_data["Galaxy"].iloc[0],
        g_crit=G_CRIT,
        gate_power=GATE_POWER,
        bg_control_mode=BG_CONTROL_MODE,
        shape_depth_mode=SHAPE_DEPTH_MODE,
        shape_c_crit=SHAPE_C_CRIT,
        shape_depth_crit=SHAPE_DEPTH_CRIT,
    )
    if profile is None:
        return np.nan
    return float(chi2_sparc_galaxy_direct_local(rc_data, profile) / max(1, len(rc_data)))


def rescale_stellar_ml(rc_data, ml_scale):
    rc = rc_data.copy()
    scale = float(max(0.0, ml_scale))
    root_scale = np.sqrt(scale)
    for col in ("Vdisk", "Vbul"):
        if col in rc.columns:
            rc[col] = pd.to_numeric(rc[col], errors="coerce") * root_scale
    rc["Vbar"] = np.sqrt(
        np.square(pd.to_numeric(rc["Vgas"], errors="coerce"))
        + np.square(pd.to_numeric(rc["Vdisk"], errors="coerce"))
        + np.square(pd.to_numeric(rc["Vbul"], errors="coerce"))
    )
    return rc


def safe_ratio(num, den):
    if not np.isfinite(num) or not np.isfinite(den) or den <= 0:
        return np.nan
    return float(num / den)


def main():
    os.chdir(ROOT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    metadata = pd.read_csv(ROOT / "research_assets" / "research_data" / "mond_resistant_original_metadata.csv")
    table1 = load_table1_explicit()
    edge = pd.read_csv(ROOT / "research_assets" / "derived_exports" / "distance_edge_surrender_members.csv")
    full = pd.read_csv(ROOT / "analysis_outputs" / "acm_vs_mond_per_galaxy.csv")

    holdout40 = edge[edge["subset"] == "holdout_40"][["Galaxy"]].drop_duplicates()
    surrender22 = edge[edge["subset"] == "surrender_22"][["Galaxy"]].drop_duplicates()
    acm102 = full[full["delta_cpp_mond_minus_acm"] > 0][["Galaxy"]].drop_duplicates()

    meta_holdout = holdout40.merge(metadata, on="Galaxy", how="left")
    meta_surrender = surrender22.merge(metadata, on="Galaxy", how="left")
    meta_acm = acm102.merge(table1, on="Galaxy", how="left")

    for df in (meta_holdout, meta_surrender, meta_acm):
        df["gas_to_light_proxy"] = [
            safe_ratio(mhi, l36) for mhi, l36 in zip(pd.to_numeric(df["MHI"], errors="coerce"), pd.to_numeric(df["L3.6"], errors="coerce"))
        ]
        df["gas_surface_proxy"] = [
            safe_ratio(mhi, rdisk ** 2) for mhi, rdisk in zip(pd.to_numeric(df["MHI"], errors="coerce"), pd.to_numeric(df["Rdisk"], errors="coerce"))
        ]

    def summarize_group(name, df):
        return {
            "group": name,
            "n": int(len(df)),
            "mean_MHI": float(np.nanmean(pd.to_numeric(df["MHI"], errors="coerce"))),
            "median_MHI": float(np.nanmedian(pd.to_numeric(df["MHI"], errors="coerce"))),
            "mean_L3p6": float(np.nanmean(pd.to_numeric(df["L3.6"], errors="coerce"))),
            "median_L3p6": float(np.nanmedian(pd.to_numeric(df["L3.6"], errors="coerce"))),
            "mean_gas_to_light_proxy": float(np.nanmean(pd.to_numeric(df["gas_to_light_proxy"], errors="coerce"))),
            "median_gas_to_light_proxy": float(np.nanmedian(pd.to_numeric(df["gas_to_light_proxy"], errors="coerce"))),
            "mean_gas_surface_proxy": float(np.nanmean(pd.to_numeric(df["gas_surface_proxy"], errors="coerce"))),
            "median_gas_surface_proxy": float(np.nanmedian(pd.to_numeric(df["gas_surface_proxy"], errors="coerce"))),
            "mean_sbdisk": float(np.nanmean(pd.to_numeric(df["SBdisk"], errors="coerce"))),
            "median_sbdisk": float(np.nanmedian(pd.to_numeric(df["SBdisk"], errors="coerce"))),
        }

    gas_summary = pd.DataFrame(
        [
            summarize_group("holdout_40", meta_holdout),
            summarize_group("surrender_22", meta_surrender),
            summarize_group("acm_better_102", meta_acm),
        ]
    )
    gas_summary.to_csv(OUT_GAS, index=False)

    params = fit_current_trunk()
    sparc_holdout = load_sparc_dict(meta_holdout["Galaxy"].astype(str).tolist())

    ml_scales = [0.70, 0.85, 1.00, 1.15, 1.30]
    rows = []
    for galaxy in meta_holdout["Galaxy"].astype(str):
        rc = sparc_holdout.get(galaxy)
        if rc is None:
            continue
        base_row = full.loc[full["Galaxy"] == galaxy]
        if len(base_row) == 0:
            continue
        base_row = base_row.iloc[0]
        baseline_mond = float(base_row["mond_cpp"])
        baseline_acm = float(base_row["acm_cpp"])
        best_margin = float(base_row["delta_cpp_mond_minus_acm"])
        best_scale = 1.0
        best_acm = baseline_acm
        best_mond = baseline_mond
        flipped = False

        for scale in ml_scales:
            rc_scaled = rescale_stellar_ml(rc, scale)
            acm_cpp = acm_cpp_for_rc(rc_scaled, params)
            mond_cpp, _ = mond_chi2_per_point(rc_scaled)
            margin = mond_cpp - acm_cpp
            if margin > best_margin:
                best_margin = margin
                best_scale = scale
                best_acm = acm_cpp
                best_mond = mond_cpp
            if best_margin > 0:
                flipped = True

        rows.append(
            {
                "Galaxy": galaxy,
                "baseline_acm_cpp": float(baseline_acm),
                "baseline_mond_cpp": float(baseline_mond),
                "baseline_margin": float(baseline_mond - baseline_acm),
                "best_ml_scale": float(best_scale),
                "best_acm_cpp": float(best_acm),
                "best_mond_cpp": float(best_mond),
                "best_margin": float(best_margin),
                "best_margin_shift": float(best_margin - (baseline_mond - baseline_acm)),
                "flipped_to_acm": bool(flipped),
            }
        )

    ranked = pd.DataFrame(rows).sort_values(["flipped_to_acm", "best_margin_shift"], ascending=[False, False])
    ranked.to_csv(OUT_ML_RANKED, index=False)

    summary = pd.DataFrame(
        [
            {
                "n_holdout_40": int(len(ranked)),
                "n_flipped_to_acm": int(ranked["flipped_to_acm"].sum()),
                "flip_fraction": float(ranked["flipped_to_acm"].mean()) if len(ranked) else np.nan,
                "mean_best_margin_shift": float(np.nanmean(ranked["best_margin_shift"])) if len(ranked) else np.nan,
                "median_best_margin_shift": float(np.nanmedian(ranked["best_margin_shift"])) if len(ranked) else np.nan,
                "best_scale_mode": float(ranked["best_ml_scale"].mode().iloc[0]) if len(ranked) and not ranked["best_ml_scale"].mode().empty else np.nan,
                "n_best_scale_0p70": int(np.sum(np.isclose(ranked["best_ml_scale"], 0.70))),
                "n_best_scale_0p85": int(np.sum(np.isclose(ranked["best_ml_scale"], 0.85))),
                "n_best_scale_1p00": int(np.sum(np.isclose(ranked["best_ml_scale"], 1.00))),
                "n_best_scale_1p15": int(np.sum(np.isclose(ranked["best_ml_scale"], 1.15))),
                "n_best_scale_1p30": int(np.sum(np.isclose(ranked["best_ml_scale"], 1.30))),
            }
        ]
    )
    summary.to_csv(OUT_ML_SUMMARY, index=False)

    print("Saved:")
    print(OUT_GAS)
    print(OUT_ML_RANKED)
    print(OUT_ML_SUMMARY)
    print(f"holdout_40 flips under M/L sweep = {int(ranked['flipped_to_acm'].sum())}")


if __name__ == "__main__":
    main()
