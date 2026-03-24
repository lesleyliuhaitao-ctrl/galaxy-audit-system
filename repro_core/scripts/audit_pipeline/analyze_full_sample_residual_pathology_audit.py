from pathlib import Path

import numpy as np
import pandas as pd

from analyze_mond_resistant_metadata_table import load_table1_explicit
from src.data_loader.load_sparc import load_sparc_rotation_curve


ROOT = Path(__file__).resolve().parent
OUT_RESEARCH = ROOT / "research_assets" / "research_data"
OUT_DERIVED = ROOT / "research_assets" / "derived_exports"

OUT_TABLE = OUT_RESEARCH / "full_sample_residual_pathology_audit.csv"
OUT_SUMMARY = OUT_DERIVED / "full_sample_residual_pathology_summary.csv"
OUT_GROUPS = OUT_DERIVED / "full_sample_residual_pathology_group_counts.csv"

GEOMETRY_PATH = ROOT / "data" / "sparc" / "galaxy_geometry.csv"


def safe_mean(series):
    arr = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.nanmean(arr)) if len(arr) else np.nan


def safe_median(series):
    arr = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.nanmedian(arr)) if len(arr) else np.nan


def gas_gradient_metrics(rc):
    if rc is None or not {"Rad", "Vgas"}.issubset(rc.columns):
        return {}

    r = pd.to_numeric(rc["Rad"], errors="coerce").to_numpy(dtype=float)
    vgas = pd.to_numeric(rc["Vgas"], errors="coerce").to_numpy(dtype=float)
    gas = np.clip(vgas, 0.0, None) ** 2

    valid = np.isfinite(r) & np.isfinite(gas) & (r > 0) & (gas > 0)
    if np.count_nonzero(valid) < 5:
        return {}

    r = r[valid]
    gas = gas[valid]
    order = np.argsort(r)
    r = r[order]
    gas = gas[order]

    log_r = np.log(r)
    log_g = np.log(gas)
    slope = np.gradient(log_g, log_r)
    abs_slope = np.abs(slope)
    curvature = np.gradient(slope, log_r)
    abs_curvature = np.abs(curvature)

    outer_mask = r >= np.nanmedian(r)
    inner_mask = r <= np.nanmedian(r)
    peak_idx = int(np.nanargmax(gas))
    peak_radius = float(r[peak_idx])
    peak_gas = float(gas[peak_idx])
    outer_mean = float(np.nanmean(gas[outer_mask])) if np.any(outer_mask) else np.nan
    inner_mean = float(np.nanmean(gas[inner_mask])) if np.any(inner_mask) else np.nan

    return {
        "n_rc_valid": int(len(r)),
        "gas_peak_radius_kpc": peak_radius,
        "gas_peak_value": peak_gas,
        "gas_outer_to_inner_ratio": float(outer_mean / inner_mean)
        if np.isfinite(outer_mean) and np.isfinite(inner_mean) and inner_mean > 0
        else np.nan,
        "gas_abs_slope_outer_mean": float(np.nanmean(abs_slope[outer_mask]))
        if np.any(outer_mask)
        else np.nan,
        "gas_abs_slope_outer_median": float(np.nanmedian(abs_slope[outer_mask]))
        if np.any(outer_mask)
        else np.nan,
        "gas_abs_curvature_outer_mean": float(np.nanmean(abs_curvature[outer_mask]))
        if np.any(outer_mask)
        else np.nan,
        "gas_abs_curvature_outer_median": float(np.nanmedian(abs_curvature[outer_mask]))
        if np.any(outer_mask)
        else np.nan,
    }


def vgas_spectrum_metrics(rc, n_grid=64):
    if rc is None or not {"Rad", "Vgas"}.issubset(rc.columns):
        return {}

    r = pd.to_numeric(rc["Rad"], errors="coerce").to_numpy(dtype=float)
    v = pd.to_numeric(rc["Vgas"], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(r) & np.isfinite(v) & (r > 0) & (v >= 0)
    if np.count_nonzero(valid) < 6:
        return {}

    r = r[valid]
    v = v[valid]
    order = np.argsort(r)
    r = r[order]
    v = v[order]
    r_norm = r / np.nanmax(r)
    grid = np.linspace(float(np.nanmin(r_norm)), 1.0, n_grid)
    v_interp = np.interp(grid, r_norm, v, left=float(v[0]), right=float(v[-1]))
    vmax = float(np.nanmax(v_interp))
    if not np.isfinite(vmax) or vmax <= 0:
        return {}

    y = v_interp / vmax
    y = y - np.nanmean(y)
    power = np.abs(np.fft.rfft(y)) ** 2
    if len(power) <= 1:
        return {}
    power = power[1:]
    total = float(np.sum(power))
    if not np.isfinite(total) or total <= 0:
        return {}
    power = power / total
    hi_start = int(np.ceil(len(power) * 0.5))
    hi_frac = float(np.sum(power[hi_start:])) if hi_start < len(power) else 0.0
    return {
        "vgas_high_freq_power_frac": hi_frac,
        "vgas_smoothness_score": float(1.0 - hi_frac),
    }


def classify(galaxy, delta_cpp, geom_set, ml_set, hard31_set):
    if delta_cpp > 0:
        return "acm_better_102"
    if galaxy in geom_set:
        return "geom_hostage_22"
    if galaxy in ml_set:
        return "stellar_hostage_9"
    if galaxy in hard31_set:
        return "gas_flat_hard31"
    return "mond_better_other"


def main():
    OUT_RESEARCH.mkdir(parents=True, exist_ok=True)
    OUT_DERIVED.mkdir(parents=True, exist_ok=True)

    compare = pd.read_csv(ROOT / "analysis_outputs" / "acm_vs_mond_per_galaxy.csv")
    table1 = load_table1_explicit()
    geometry = pd.read_csv(GEOMETRY_PATH)
    edge_ranked = pd.read_csv(OUT_DERIVED / "mond_resistant_distance_edge_ranked.csv")
    edge_members = pd.read_csv(OUT_DERIVED / "distance_edge_surrender_members.csv")
    ml_ranked = pd.read_csv(OUT_DERIVED / "holdout40_ml_sensitivity_ranked.csv")

    geom22 = set(edge_members.loc[edge_members["subset"] == "surrender_22", "Galaxy"].astype(str))
    holdout40 = set(edge_members.loc[edge_members["subset"] == "holdout_40", "Galaxy"].astype(str))
    ml9 = set(ml_ranked.loc[ml_ranked["flipped_to_acm"], "Galaxy"].astype(str))
    hard31 = holdout40 - ml9

    edge_short = edge_ranked[
        ["Galaxy", "best_margin_shift", "best_distance_mode", "flipped_at_edge"]
    ].rename(
        columns={
            "best_margin_shift": "distance_edge_best_margin_shift",
            "best_distance_mode": "distance_edge_best_mode",
            "flipped_at_edge": "distance_edge_flipped",
        }
    )
    ml_short = ml_ranked[
        ["Galaxy", "best_ml_scale", "best_margin_shift", "flipped_to_acm"]
    ].rename(
        columns={
            "best_margin_shift": "ml_best_margin_shift",
            "flipped_to_acm": "ml_flipped",
        }
    )

    merged = compare.merge(table1, on="Galaxy", how="left")
    merged = merged.merge(
        geometry[
            [
                "Galaxy",
                "ba_obs",
                "source",
                "inc_true_deg",
                "k_inc",
                "velocity_shift_pct",
                "correction_source_used",
                "geometry_qc_flag",
                "geometry_qc_reason",
            ]
        ].rename(columns={"source": "geometry_source"}),
        on="Galaxy",
        how="left",
    )
    merged = merged.merge(edge_short, on="Galaxy", how="left")
    merged = merged.merge(ml_short, on="Galaxy", how="left")

    merged["distance_rel_err"] = merged["e_D"] / merged["D"]
    merged["distance_rel_err_pct"] = 100.0 * merged["distance_rel_err"]
    merged["gas_to_light_proxy"] = merged["MHI"] / merged["L3.6"]
    merged["gas_surface_proxy"] = merged["MHI"] / np.where(
        pd.to_numeric(merged["Rdisk"], errors="coerce") > 0,
        pd.to_numeric(merged["Rdisk"], errors="coerce") ** 2,
        np.nan,
    )
    merged["pathology_group"] = [
        classify(g, d, geom22, ml9, hard31)
        for g, d in zip(merged["Galaxy"].astype(str), merged["delta_cpp_mond_minus_acm"])
    ]

    metric_rows = []
    for galaxy in merged["Galaxy"].astype(str):
        rc = load_sparc_rotation_curve(galaxy)
        metric_rows.append({"Galaxy": galaxy, **gas_gradient_metrics(rc), **vgas_spectrum_metrics(rc)})
    metrics = pd.DataFrame(metric_rows)
    expected_metric_cols = [
        "n_rc_valid",
        "gas_peak_radius_kpc",
        "gas_peak_value",
        "gas_outer_to_inner_ratio",
        "gas_abs_slope_outer_mean",
        "gas_abs_slope_outer_median",
        "gas_abs_curvature_outer_mean",
        "gas_abs_curvature_outer_median",
        "vgas_high_freq_power_frac",
        "vgas_smoothness_score",
    ]
    for col in expected_metric_cols:
        if col not in metrics.columns:
            metrics[col] = np.nan

    full = merged.merge(metrics, on="Galaxy", how="left")
    full = full.sort_values(["pathology_group", "delta_cpp_mond_minus_acm"], ascending=[True, False])
    full.to_csv(OUT_TABLE, index=False)

    group_counts = (
        full["pathology_group"]
        .value_counts()
        .rename_axis("pathology_group")
        .reset_index(name="count")
        .sort_values("pathology_group")
    )
    group_counts.to_csv(OUT_GROUPS, index=False)

    summary_rows = []
    for group_name, df in full.groupby("pathology_group"):
        summary_rows.append(
            {
                "pathology_group": group_name,
                "n": int(len(df)),
                "mean_acm_cpp": safe_mean(df["acm_cpp"]),
                "median_acm_cpp": safe_median(df["acm_cpp"]),
                "mean_mond_cpp": safe_mean(df["mond_cpp"]),
                "median_mond_cpp": safe_median(df["mond_cpp"]),
                "mean_delta_cpp_mond_minus_acm": safe_mean(df["delta_cpp_mond_minus_acm"]),
                "median_delta_cpp_mond_minus_acm": safe_median(df["delta_cpp_mond_minus_acm"]),
                "mean_distance_rel_err_pct": safe_mean(df["distance_rel_err_pct"]),
                "median_distance_rel_err_pct": safe_median(df["distance_rel_err_pct"]),
                "fd1_fraction": float((df["f_D"] == 1).mean()),
                "fd5_fraction": float((df["f_D"] == 5).mean()),
                "review_geometry_fraction": float((df["geometry_qc_flag"] == "review").mean()),
                "mean_gas_to_light_proxy": safe_mean(df["gas_to_light_proxy"]),
                "median_gas_to_light_proxy": safe_median(df["gas_to_light_proxy"]),
                "mean_L3p6": safe_mean(df["L3.6"]),
                "median_L3p6": safe_median(df["L3.6"]),
                "mean_outer_gas_slope": safe_mean(df["gas_abs_slope_outer_mean"]),
                "median_outer_gas_slope": safe_median(df["gas_abs_slope_outer_mean"]),
                "mean_outer_gas_curvature": safe_mean(df["gas_abs_curvature_outer_mean"]),
                "median_outer_gas_curvature": safe_median(df["gas_abs_curvature_outer_mean"]),
                "mean_outer_to_inner_gas_ratio": safe_mean(df["gas_outer_to_inner_ratio"]),
                "median_outer_to_inner_gas_ratio": safe_median(df["gas_outer_to_inner_ratio"]),
                "distance_edge_flip_fraction": float(df["distance_edge_flipped"].fillna(False).astype(bool).mean()),
                "ml_flip_fraction": float(df["ml_flipped"].fillna(False).astype(bool).mean()),
                "mean_vgas_high_freq_power_frac": safe_mean(df["vgas_high_freq_power_frac"]),
                "median_vgas_high_freq_power_frac": safe_median(df["vgas_high_freq_power_frac"]),
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values("pathology_group")
    summary.to_csv(OUT_SUMMARY, index=False)

    print("Saved:")
    print(OUT_TABLE)
    print(OUT_SUMMARY)
    print(OUT_GROUPS)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
