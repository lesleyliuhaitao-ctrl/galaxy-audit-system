#!/usr/bin/env python
"""
Quick gas-curvature scan for the final hard31 galaxies.

We inspect the gas-only channel using Vgas^2 as a proxy field and compute
second-derivative structure on log-radius coordinates:

    C_gas(r) = | d^2 ln(Vgas^2) / d(ln r)^2 |

This tests whether a second-order shape signal survives where first-order
slope activation appears too weak.
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
OUT_PER = OUT_DIR / "hard31_gas_curvature_per_galaxy.csv"
OUT_SUM = OUT_DIR / "hard31_gas_curvature_summary.csv"


def safe_stats(arr):
    arr = np.asarray(arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return np.nan, np.nan
    return float(np.nanmean(arr)), float(np.nanmedian(arr))


def gas_curvature_profile(rc):
    if rc is None or not {"Rad", "Vgas"}.issubset(set(rc.columns)):
        return None

    r = pd.to_numeric(rc["Rad"], errors="coerce").to_numpy(dtype=float)
    vgas = pd.to_numeric(rc["Vgas"], errors="coerce").to_numpy(dtype=float)
    gas = np.clip(vgas, 0.0, None) ** 2

    valid = np.isfinite(r) & np.isfinite(gas) & (r > 0) & (gas > 0)
    if np.count_nonzero(valid) < 6:
        return None

    r = r[valid]
    gas = gas[valid]
    order = np.argsort(r)
    r = r[order]
    gas = gas[order]

    log_r = np.log(r)
    log_g = np.log(gas)
    slope = np.gradient(log_g, log_r)
    curvature = np.gradient(slope, log_r)
    abs_curvature = np.abs(curvature)

    outer_mask = r >= np.nanmedian(r)
    inner_mask = r <= np.nanmedian(r)

    return {
        "n_points": int(len(r)),
        "gas_abs_curvature_mean": float(np.nanmean(abs_curvature)),
        "gas_abs_curvature_median": float(np.nanmedian(abs_curvature)),
        "gas_abs_curvature_outer_mean": float(np.nanmean(abs_curvature[outer_mask])) if np.any(outer_mask) else np.nan,
        "gas_abs_curvature_outer_median": float(np.nanmedian(abs_curvature[outer_mask])) if np.any(outer_mask) else np.nan,
        "gas_abs_curvature_inner_mean": float(np.nanmean(abs_curvature[inner_mask])) if np.any(inner_mask) else np.nan,
        "gas_abs_curvature_inner_median": float(np.nanmedian(abs_curvature[inner_mask])) if np.any(inner_mask) else np.nan,
        "gas_curvature_std": float(np.nanstd(curvature)),
        "gas_curvature_sign_mean": float(np.nanmean(curvature)),
        "gas_curvature_outer_sign_mean": float(np.nanmean(curvature[outer_mask])) if np.any(outer_mask) else np.nan,
    }


def summarize_group(name, df):
    cols = [
        "gas_abs_curvature_mean",
        "gas_abs_curvature_median",
        "gas_abs_curvature_outer_mean",
        "gas_abs_curvature_outer_median",
        "gas_abs_curvature_inner_mean",
        "gas_abs_curvature_inner_median",
        "gas_curvature_std",
        "gas_curvature_sign_mean",
        "gas_curvature_outer_sign_mean",
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
            stats = gas_curvature_profile(rc)
            if stats is None:
                continue
            rows.append({"Galaxy": galaxy, "subset": subset_name, **stats})

    per = pd.DataFrame(rows).sort_values(["subset", "gas_abs_curvature_outer_mean"], ascending=[True, True])
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


if __name__ == "__main__":
    main()
