"""
Audit whether the holographic impedance adaptation operator generalizes beyond
the hard31 subset.

Questions:
- Does it preserve the ACM-better majority?
- Does it help the stellar-hostage 9?
- What is the net effect on the full matched sample?
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_acm_vs_mond import load_sparc_dict
from analyze_hard31_holographic_impedance_operator import (
    build_impedance_profile,
    current_trunk_params,
)
from src.fitting.fit_sparc import chi2_sparc_galaxy_direct_local


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "research_assets" / "derived_exports"
OUT_PER = OUT_DIR / "impedance_operator_generalization_per_galaxy.csv"
OUT_SUM = OUT_DIR / "impedance_operator_generalization_summary.csv"


def classify_group(galaxy, delta_cpp, geom22, ml9, hard31):
    if delta_cpp > 0:
        return "acm_better_102"
    if galaxy in geom22:
        return "geom_hostage_22"
    if galaxy in ml9:
        return "stellar_hostage_9"
    if galaxy in hard31:
        return "gas_flat_hard31"
    return "other"


def summarize_group(name, df):
    return {
        "subset": name,
        "n": int(len(df)),
        "n_flipped_to_acm": int(df["new_margin"].gt(0).sum()),
        "flip_fraction": float(df["new_margin"].gt(0).mean()) if len(df) else np.nan,
        "mean_baseline_margin": float(np.nanmean(df["baseline_margin"])) if len(df) else np.nan,
        "median_baseline_margin": float(np.nanmedian(df["baseline_margin"])) if len(df) else np.nan,
        "mean_new_margin": float(np.nanmean(df["new_margin"])) if len(df) else np.nan,
        "median_new_margin": float(np.nanmedian(df["new_margin"])) if len(df) else np.nan,
        "mean_margin_shift": float(np.nanmean(df["margin_shift"])) if len(df) else np.nan,
        "median_margin_shift": float(np.nanmedian(df["margin_shift"])) if len(df) else np.nan,
        "mean_baseline_acm_cpp": float(np.nanmean(df["baseline_acm_cpp"])) if len(df) else np.nan,
        "median_baseline_acm_cpp": float(np.nanmedian(df["baseline_acm_cpp"])) if len(df) else np.nan,
        "mean_new_acm_cpp": float(np.nanmean(df["new_acm_cpp"])) if len(df) else np.nan,
        "median_new_acm_cpp": float(np.nanmedian(df["new_acm_cpp"])) if len(df) else np.nan,
        "mean_impedance_correction": float(np.nanmean(df["leff_impedance_correction_median"])) if len(df) else np.nan,
        "median_impedance_correction": float(np.nanmedian(df["leff_impedance_correction_median"])) if len(df) else np.nan,
    }


def main():
    os.chdir(ROOT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    per_gal = pd.read_csv(ROOT / "analysis_outputs" / "acm_vs_mond_per_galaxy.csv")
    edge = pd.read_csv(OUT_DIR / "distance_edge_surrender_members.csv")
    ml = pd.read_csv(OUT_DIR / "holdout40_ml_sensitivity_ranked.csv")

    geom22 = set(edge.loc[edge["subset"] == "surrender_22", "Galaxy"].astype(str))
    holdout40 = set(edge.loc[edge["subset"] == "holdout_40", "Galaxy"].astype(str))
    ml9 = set(ml.loc[ml["flipped_to_acm"], "Galaxy"].astype(str))
    hard31 = holdout40 - ml9

    sparc = load_sparc_dict()
    trunk_params = current_trunk_params()

    rows = []
    for _, row in per_gal.iterrows():
        galaxy = str(row["Galaxy"])
        rc = sparc.get(galaxy)
        if rc is None:
            continue

        profile = build_impedance_profile(rc, galaxy, trunk_params)
        if profile is None:
            continue

        baseline_acm = float(row["acm_cpp"])
        mond_cpp = float(row["mond_cpp"])
        baseline_margin = float(row["delta_cpp_mond_minus_acm"])
        new_acm_cpp = float(chi2_sparc_galaxy_direct_local(rc, profile) / max(1, len(rc)))
        new_margin = float(mond_cpp - new_acm_cpp)
        group = classify_group(galaxy, baseline_margin, geom22, ml9, hard31)

        rows.append(
            {
                "Galaxy": galaxy,
                "pathology_group": group,
                "baseline_acm_cpp": baseline_acm,
                "new_acm_cpp": new_acm_cpp,
                "mond_cpp": mond_cpp,
                "baseline_margin": baseline_margin,
                "new_margin": new_margin,
                "margin_shift": new_margin - baseline_margin,
                "baseline_acm_better": bool(baseline_margin > 0),
                "new_acm_better": bool(new_margin > 0),
                "sigma_kpc_new": float(profile.get("sigma_kpc", np.nan)),
                "l_obs_kpc": float(profile.get("l_obs_kpc", np.nan)),
                "leff_impedance_correction_median": float(profile.get("leff_impedance_correction_median", np.nan)),
                "eta_enclosed_bar_median": float(profile.get("eta_enclosed_bar_median", np.nan)),
            }
        )

    out = pd.DataFrame(rows).sort_values(["pathology_group", "margin_shift"], ascending=[True, False])
    out.to_csv(OUT_PER, index=False)

    summary = pd.DataFrame(
        [
            summarize_group("full_sample_164", out),
            summarize_group("acm_better_102", out[out["pathology_group"] == "acm_better_102"]),
            summarize_group("stellar_hostage_9", out[out["pathology_group"] == "stellar_hostage_9"]),
            summarize_group("geom_hostage_22", out[out["pathology_group"] == "geom_hostage_22"]),
            summarize_group("gas_flat_hard31", out[out["pathology_group"] == "gas_flat_hard31"]),
        ]
    )
    summary.to_csv(OUT_SUM, index=False)

    print("Saved:")
    print(OUT_PER)
    print(OUT_SUM)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
