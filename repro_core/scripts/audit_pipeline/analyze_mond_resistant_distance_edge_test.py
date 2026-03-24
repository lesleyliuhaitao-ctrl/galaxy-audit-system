import os
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_acm_vs_mond import (
    BG_CONTROL_MODE,
    GATE_POWER,
    G_CRIT,
    MAIN7_GALAXIES,
    MOND_A0,
    SHAPE_C_CRIT,
    SHAPE_DEPTH_CRIT,
    SHAPE_DEPTH_MODE,
    load_sparc_dict,
    mond_chi2_per_point,
)
from analyze_mond_resistant_metadata_table import load_table1_explicit
from src.fitting.fit_sparc import (
    chi2_sparc_galaxy_direct_local,
    fit_sparc_gated_background_model,
)
from src.models.eta_path_integral import eta_local_gated_background_profile


ROOT = Path(__file__).resolve().parent
RESEARCH_DATA_DIR = ROOT / "research_assets" / "research_data"
DERIVED_DIR = ROOT / "research_assets" / "derived_exports"
GEOMETRY_PATH = ROOT / "data" / "sparc" / "galaxy_geometry.csv"
COMPARE_PATH = ROOT / "analysis_outputs" / "acm_vs_mond_per_galaxy.csv"


def scale_rc_distance(rc_data: pd.DataFrame, d_new: float) -> pd.DataFrame:
    rc_new = rc_data.copy()
    d_old = float(rc_data["D"].iloc[0]) if "D" in rc_data.columns else np.nan
    if not np.isfinite(d_old) or d_old <= 0 or not np.isfinite(d_new) or d_new <= 0:
        return rc_new

    scale = float(d_new) / float(d_old)
    vel_scale = np.sqrt(scale)

    rc_new["Rad"] = rc_new["Rad"].astype(float) * scale
    for col in ["Vgas", "Vdisk", "Vbul"]:
        if col in rc_new.columns:
            rc_new[col] = rc_new[col].astype(float) * vel_scale

    if all(col in rc_new.columns for col in ["Vgas", "Vdisk", "Vbul"]):
        rc_new["Vbar"] = np.sqrt(rc_new["Vgas"] ** 2 + rc_new["Vdisk"] ** 2 + rc_new["Vbul"] ** 2)

    rc_new["D"] = float(d_new)
    return rc_new


def acm_cpp(rc_data: pd.DataFrame, galaxy: str, trunk_params: tuple[float, float, float, float]) -> float:
    eta_base, beta_density, beta_bg, lambda_sup = trunk_params
    profile = eta_local_gated_background_profile(
        rc_data,
        eta_base=eta_base,
        beta_density=beta_density,
        beta_bg=beta_bg,
        lambda_sup=lambda_sup,
        galaxy_name=galaxy,
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


def margin(acm_cpp_val: float, mond_cpp_val: float) -> float:
    return float(mond_cpp_val - acm_cpp_val)


def summarize_group(df: pd.DataFrame, label: str) -> dict:
    qual = pd.to_numeric(df["Qual"], errors="coerce")
    return {
        "group": label,
        "n_galaxies": int(len(df)),
        "mean_distance_rel_err_pct": float(df["distance_rel_err_pct"].mean()),
        "median_distance_rel_err_pct": float(df["distance_rel_err_pct"].median()),
        "mean_eD_mpc": float(df["e_D"].mean()),
        "median_eD_mpc": float(df["e_D"].median()),
        "qual_eq_3_fraction": float((qual == 3).mean()),
        "qual_ge_2_fraction": float((qual >= 2).mean()),
        "review_geometry_fraction": float((df["geometry_qc_flag"] == "review").mean()),
    }


def main():
    os.chdir(ROOT)
    RESEARCH_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    compare = pd.read_csv(COMPARE_PATH)
    table1 = load_table1_explicit()
    geometry = pd.read_csv(GEOMETRY_PATH)

    metadata = (
        compare.merge(table1, on="Galaxy", how="left")
        .merge(
            geometry[
                [
                    "Galaxy",
                    "geometry_qc_flag",
                    "geometry_qc_reason",
                    "source",
                ]
            ].rename(columns={"source": "geometry_source"}),
            on="Galaxy",
            how="left",
        )
        .copy()
    )
    metadata["distance_rel_err_pct"] = 100.0 * metadata["e_D"] / metadata["D"]

    mond_better = metadata.loc[metadata["delta_cpp_mond_minus_acm"] < 0].copy()
    acm_better = metadata.loc[metadata["delta_cpp_mond_minus_acm"] > 0].copy()

    summary_rows = [
        summarize_group(mond_better, "mond_better_62"),
        summarize_group(acm_better, "acm_better_102"),
    ]
    pd.DataFrame(summary_rows).to_csv(DERIVED_DIR / "distance_bias_group_comparison.csv", index=False)

    sparc_main7 = load_sparc_dict(MAIN7_GALAXIES)
    trunk_fit = fit_sparc_gated_background_model(
        sparc_main7,
        use_direct=True,
        g_crit=G_CRIT,
        gate_power=GATE_POWER,
        bg_control_mode=BG_CONTROL_MODE,
        shape_depth_mode=SHAPE_DEPTH_MODE,
        shape_c_crit=SHAPE_C_CRIT,
        shape_depth_crit=SHAPE_DEPTH_CRIT,
    )
    trunk_params = tuple(float(x) for x in trunk_fit.x)

    sparc_subset = load_sparc_dict(mond_better["Galaxy"].tolist())

    rows = []
    for _, row in mond_better.iterrows():
        galaxy = row["Galaxy"]
        rc = sparc_subset.get(galaxy)
        if rc is None or len(rc) < 3:
            continue

        d_nom = float(row["D"])
        e_d = float(row["e_D"])
        variants = {
            "baseline": d_nom,
            "D_minus_eD": max(1.0e-6, d_nom - e_d),
            "D_plus_eD": d_nom + e_d,
        }

        baseline_margin = None
        for mode, d_new in variants.items():
            rc_variant = scale_rc_distance(rc, d_new)
            acm_cpp_val = acm_cpp(rc_variant, galaxy, trunk_params)
            mond_cpp_val, n_valid = mond_chi2_per_point(rc_variant, a0=MOND_A0)
            m = margin(acm_cpp_val, mond_cpp_val)
            if mode == "baseline":
                baseline_margin = m
            rows.append(
                {
                    "Galaxy": galaxy,
                    "distance_mode": mode,
                    "D_nominal_mpc": d_nom,
                    "e_D_mpc": e_d,
                    "D_test_mpc": d_new,
                    "distance_shift_mpc": d_new - d_nom,
                    "distance_shift_sigma": (d_new - d_nom) / e_d if np.isfinite(e_d) and e_d > 0 else np.nan,
                    "acm_cpp": acm_cpp_val,
                    "mond_cpp": mond_cpp_val,
                    "delta_cpp_mond_minus_acm": m,
                    "n_valid_mond": n_valid,
                    "geometry_qc_flag": row.get("geometry_qc_flag", np.nan),
                    "geometry_qc_reason": row.get("geometry_qc_reason", np.nan),
                    "Qual": row.get("Qual", np.nan),
                }
            )

    edge = pd.DataFrame(rows)
    edge.to_csv(DERIVED_DIR / "mond_resistant_distance_edge_response.csv", index=False)

    pivot = edge.pivot_table(
        index="Galaxy",
        columns="distance_mode",
        values="delta_cpp_mond_minus_acm",
        aggfunc="first",
    ).reset_index()
    pivot["best_margin_shift"] = pivot[["D_minus_eD", "D_plus_eD"]].max(axis=1) - pivot["baseline"]
    pivot["best_distance_mode"] = np.where(
        pivot["D_plus_eD"] >= pivot["D_minus_eD"], "D_plus_eD", "D_minus_eD"
    )
    pivot["flipped_at_edge"] = pivot[["baseline", "D_minus_eD", "D_plus_eD"]].max(axis=1) > 0
    pivot = pivot.sort_values("best_margin_shift", ascending=False)
    pivot.to_csv(DERIVED_DIR / "mond_resistant_distance_edge_ranked.csv", index=False)

    summary = pd.DataFrame(
        [
            {
                "n_mond_better_input": int(len(mond_better)),
                "alpha_mean_distance_rel_err_pct_mond_better": float(mond_better["distance_rel_err_pct"].mean()),
                "alpha_mean_distance_rel_err_pct_acm_better": float(acm_better["distance_rel_err_pct"].mean()),
                "beta_qual_eq_3_fraction_mond_better": float((pd.to_numeric(mond_better["Qual"], errors="coerce") == 3).mean()),
                "beta_qual_eq_3_fraction_acm_better": float((pd.to_numeric(acm_better["Qual"], errors="coerce") == 3).mean()),
                "beta_qual_ge_2_fraction_mond_better": float((pd.to_numeric(mond_better["Qual"], errors="coerce") >= 2).mean()),
                "beta_qual_ge_2_fraction_acm_better": float((pd.to_numeric(acm_better["Qual"], errors="coerce") >= 2).mean()),
                "n_flipped_at_distance_edge": int(pivot["flipped_at_edge"].sum()),
                "median_best_margin_shift": float(pivot["best_margin_shift"].median()),
                "mean_best_margin_shift": float(pivot["best_margin_shift"].mean()),
                "max_best_margin_shift": float(pivot["best_margin_shift"].max()),
            }
        ]
    )
    summary.to_csv(DERIVED_DIR / "mond_resistant_distance_edge_summary.csv", index=False)

    print((DERIVED_DIR / "mond_resistant_distance_edge_summary.csv").resolve())
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
