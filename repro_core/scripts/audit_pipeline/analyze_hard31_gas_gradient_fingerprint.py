#!/usr/bin/env python
"""
Gas-gradient fingerprint for the final 31 hard-bone galaxies.

Definition:
- Start from holdout_40 (distance-hard systems).
- Remove the 9 galaxies that flip to ACM under a reasonable stellar M/L sweep.
- Study only the gas channel via Vgas^2, without stellar contamination.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader.load_sparc import load_sparc_rotation_curve


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "research_assets" / "derived_exports"
OUT_PER = OUT_DIR / "hard31_gas_gradient_per_galaxy.csv"
OUT_SUM = OUT_DIR / "hard31_gas_gradient_summary.csv"


def safe_stats(arr):
    arr = np.asarray(arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return np.nan, np.nan
    return float(np.nanmean(arr)), float(np.nanmedian(arr))


def gas_gradient_profile(rc):
    if rc is None or not {"Rad", "Vgas"}.issubset(set(rc.columns)):
        return None

    r = pd.to_numeric(rc["Rad"], errors="coerce").to_numpy(dtype=float)
    vgas = pd.to_numeric(rc["Vgas"], errors="coerce").to_numpy(dtype=float)
    gas = np.clip(vgas, 0.0, None) ** 2

    valid = np.isfinite(r) & np.isfinite(gas) & (r > 0) & (gas > 0)
    if np.count_nonzero(valid) < 5:
        return None

    r = r[valid]
    gas = gas[valid]
    order = np.argsort(r)
    r = r[order]
    gas = gas[order]

    log_r = np.log(r)
    log_g = np.log(gas)

    slope = np.gradient(log_g, log_r)
    abs_slope = np.abs(slope)
    outer_mask = r >= np.nanmedian(r)
    inner_mask = r <= np.nanmedian(r)

    peak_idx = int(np.nanargmax(gas))
    peak_radius = float(r[peak_idx])
    peak_gas = float(gas[peak_idx])
    outer_mean = float(np.nanmean(gas[outer_mask])) if np.any(outer_mask) else np.nan
    center_mean = float(np.nanmean(gas[inner_mask])) if np.any(inner_mask) else np.nan

    return {
        "n_points": int(len(r)),
        "gas_peak_radius_kpc": peak_radius,
        "gas_peak_value": peak_gas,
        "gas_outer_to_inner_ratio": float(outer_mean / center_mean) if np.isfinite(outer_mean) and np.isfinite(center_mean) and center_mean > 0 else np.nan,
        "gas_abs_slope_mean": float(np.nanmean(abs_slope)),
        "gas_abs_slope_median": float(np.nanmedian(abs_slope)),
        "gas_abs_slope_outer_mean": float(np.nanmean(abs_slope[outer_mask])) if np.any(outer_mask) else np.nan,
        "gas_abs_slope_outer_median": float(np.nanmedian(abs_slope[outer_mask])) if np.any(outer_mask) else np.nan,
        "gas_abs_slope_inner_mean": float(np.nanmean(abs_slope[inner_mask])) if np.any(inner_mask) else np.nan,
        "gas_slope_std": float(np.nanstd(slope)),
    }


def summarize_group(name, df):
    cols = [
        "gas_outer_to_inner_ratio",
        "gas_abs_slope_mean",
        "gas_abs_slope_median",
        "gas_abs_slope_outer_mean",
        "gas_abs_slope_outer_median",
        "gas_abs_slope_inner_mean",
        "gas_slope_std",
        "gas_peak_radius_kpc",
    ]
    row = {"group": name, "n": int(len(df))}
    for col in cols:
        mean_val, med_val = safe_stats(df[col])
        row[f"mean_{col}"] = mean_val
        row[f"median_{col}"] = med_val
    return row


def main():
    os.chdir(ROOT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ml = pd.read_csv(OUT_DIR / "holdout40_ml_sensitivity_ranked.csv")
    edge = pd.read_csv(OUT_DIR / "distance_edge_surrender_members.csv")

    holdout40 = set(edge.loc[edge["subset"] == "holdout_40", "Galaxy"].astype(str))
    ml_flip9 = set(ml.loc[ml["flipped_to_acm"], "Galaxy"].astype(str))
    hard31 = sorted(holdout40 - ml_flip9)
    ml9 = sorted(holdout40 & ml_flip9)
    surrender22 = sorted(edge.loc[edge["subset"] == "surrender_22", "Galaxy"].astype(str))

    rows = []
    for subset_name, galaxies in [
        ("hard31", hard31),
        ("ml_flip9", ml9),
        ("surrender22", surrender22),
    ]:
        for galaxy in galaxies:
            rc = load_sparc_rotation_curve(galaxy)
            stats = gas_gradient_profile(rc)
            if stats is None:
                continue
            rows.append({"Galaxy": galaxy, "subset": subset_name, **stats})

    per = pd.DataFrame(rows).sort_values(["subset", "gas_abs_slope_outer_mean"], ascending=[True, True])
    per.to_csv(OUT_PER, index=False)

    summary = pd.DataFrame(
        [
            summarize_group("hard31", per[per["subset"] == "hard31"]),
            summarize_group("ml_flip9", per[per["subset"] == "ml_flip9"]),
            summarize_group("surrender22", per[per["subset"] == "surrender22"]),
        ]
    )
    summary.to_csv(OUT_SUM, index=False)

    print("Saved:")
    print(OUT_PER)
    print(OUT_SUM)
    print(f"hard31 count = {len(hard31)}")


if __name__ == "__main__":
    main()
