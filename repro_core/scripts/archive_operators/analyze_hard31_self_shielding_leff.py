#!/usr/bin/env python
"""
Test a self-shielding coherence-length operator on the final hard31 galaxies.

Hypothesis:
    L_eff should depend on the local field occupancy itself rather than on
    derivatives of the field.

Operator:
    L_eff(r) = L_base * [1 + gamma_LH * ln(1 + eta_crit / (eta(r) + eps))]

Minimal no-new-parameter choice:
    eta_crit = eta_base
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_acm_vs_mond import (
    BG_CONTROL_MODE,
    GATE_POWER,
    G_CRIT,
    SHAPE_C_CRIT,
    SHAPE_DEPTH_CRIT,
    SHAPE_DEPTH_MODE,
    load_sparc_dict,
)
from src.fitting.fit_sparc import chi2_sparc_galaxy_direct_local
from src.models.coherence_propagation import (
    DEFAULT_COHERENCE_GAMMA,
    DEFAULT_COHERENCE_L0_RATIO,
    adaptive_gaussian_smooth,
    get_rdisk_kpc,
)
from src.models.eta_path_integral import eta_local_gated_background_profile


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "research_assets" / "derived_exports"
OUT_PER = OUT_DIR / "hard31_self_shielding_leff_per_galaxy.csv"
OUT_SUM = OUT_DIR / "hard31_self_shielding_leff_summary.csv"


def current_trunk_params():
    summary = pd.read_csv(ROOT / "analysis_outputs" / "acm_vs_mond_summary.csv").iloc[0]
    return (
        float(summary["acm_eta_base"]),
        float(summary["acm_beta_density"]),
        float(summary["acm_beta_bg"]),
        float(summary["acm_lambda_sup"]),
    )


def build_self_shielding_profile(rc_data, galaxy_name, trunk_params):
    eta_base, beta_density, beta_bg, lambda_sup = trunk_params
    base = eta_local_gated_background_profile(
        rc_data,
        eta_base=eta_base,
        beta_density=beta_density,
        beta_bg=beta_bg,
        lambda_sup=lambda_sup,
        galaxy_name=galaxy_name,
        g_crit=G_CRIT,
        gate_power=GATE_POWER,
        bg_control_mode=BG_CONTROL_MODE,
        shape_depth_mode=SHAPE_DEPTH_MODE,
        shape_c_crit=SHAPE_C_CRIT,
        shape_depth_crit=SHAPE_DEPTH_CRIT,
        coherence_enabled=False,
    )
    if base is None:
        return None

    r = np.asarray(base["r_kpc"], dtype=float)
    eta_local = np.asarray(base["eta_local"], dtype=float)
    valid = np.isfinite(r) & np.isfinite(eta_local) & (r > 0) & (eta_local > 0)
    if np.count_nonzero(valid) < 5:
        return base

    rv = r[valid]
    ev = eta_local[valid]
    order = np.argsort(rv)
    rv = rv[order]
    ev = ev[order]

    eta_crit = float(eta_base)
    correction = 1.0 + float(DEFAULT_COHERENCE_GAMMA) * np.log(
        1.0 + eta_crit / np.maximum(ev, 1.0e-30)
    )

    score_pre = float(base.get("coherence_score_pre", 1.0))
    if not np.isfinite(score_pre):
        score_pre = 1.0
    rdisk = get_rdisk_kpc(galaxy_name, rc_data)
    l_base = float(DEFAULT_COHERENCE_L0_RATIO) * score_pre * float(rdisk)

    radial_span = max(float(np.nanmax(rv) - np.nanmin(rv)), 1.0e-6)
    sigma_valid = np.clip(
        np.nan_to_num(l_base * correction, nan=l_base, posinf=radial_span, neginf=l_base),
        0.0,
        radial_span,
    )
    eta_smooth = adaptive_gaussian_smooth(rv, ev, sigma_valid)

    eta_full = eta_local.astype(float, copy=True)
    eta_full[valid] = np.interp(
        r[valid], rv, eta_smooth, left=float(eta_smooth[0]), right=float(eta_smooth[-1])
    )
    sigma_profile = np.full_like(r, np.nan, dtype=float)
    sigma_profile[valid] = np.interp(
        r[valid], rv, sigma_valid, left=float(sigma_valid[0]), right=float(sigma_valid[-1])
    )
    correction_full = np.full_like(r, np.nan, dtype=float)
    correction_full[valid] = np.interp(
        r[valid], rv, correction, left=float(correction[0]), right=float(correction[-1])
    )

    profile = dict(base)
    profile["eta_local"] = eta_full
    profile["sigma_profile_kpc"] = sigma_profile
    profile["sigma_kpc"] = float(np.nanmedian(sigma_profile[np.isfinite(sigma_profile)])) if np.any(np.isfinite(sigma_profile)) else float(l_base)
    profile["l_obs_kpc"] = float(l_base)
    profile["leff_self_shielding_correction"] = correction_full
    profile["leff_self_shielding_correction_median"] = float(np.nanmedian(correction_full[np.isfinite(correction_full)])) if np.any(np.isfinite(correction_full)) else 1.0
    profile["eta_crit"] = float(eta_crit)
    profile["gamma_coherence"] = float(DEFAULT_COHERENCE_GAMMA)
    profile["l0_ratio"] = float(DEFAULT_COHERENCE_L0_RATIO)
    profile["rdisk_kpc"] = float(rdisk)
    return profile


def main():
    os.chdir(ROOT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    per_gal = pd.read_csv(ROOT / "analysis_outputs" / "acm_vs_mond_per_galaxy.csv")
    ml = pd.read_csv(OUT_DIR / "holdout40_ml_sensitivity_ranked.csv")
    edge = pd.read_csv(OUT_DIR / "distance_edge_surrender_members.csv")

    holdout40 = set(edge.loc[edge["subset"] == "holdout_40", "Galaxy"].astype(str))
    ml_flip9 = set(ml.loc[ml["flipped_to_acm"], "Galaxy"].astype(str))
    hard31 = sorted(holdout40 - ml_flip9)

    sparc = load_sparc_dict()
    trunk_params = current_trunk_params()

    rows = []
    for galaxy in hard31:
        rc = sparc.get(galaxy)
        if rc is None:
            continue
        base_row = per_gal.loc[per_gal["Galaxy"] == galaxy]
        if len(base_row) == 0:
            continue
        base_row = base_row.iloc[0]
        profile = build_self_shielding_profile(rc, galaxy, trunk_params)
        if profile is None:
            continue

        acm_cpp_new = float(chi2_sparc_galaxy_direct_local(rc, profile) / max(1, len(rc)))
        mond_cpp = float(base_row["mond_cpp"])
        baseline_acm = float(base_row["acm_cpp"])
        baseline_margin = float(base_row["delta_cpp_mond_minus_acm"])
        new_margin = float(mond_cpp - acm_cpp_new)
        rows.append(
            {
                "Galaxy": galaxy,
                "baseline_acm_cpp": baseline_acm,
                "new_acm_cpp": acm_cpp_new,
                "mond_cpp": mond_cpp,
                "baseline_margin": baseline_margin,
                "new_margin": new_margin,
                "margin_shift": new_margin - baseline_margin,
                "flipped_to_acm": bool(new_margin > 0),
                "sigma_kpc_new": float(profile.get("sigma_kpc", np.nan)),
                "l_obs_kpc": float(profile.get("l_obs_kpc", np.nan)),
                "leff_self_shielding_correction_median": float(profile.get("leff_self_shielding_correction_median", np.nan)),
                "eta_crit": float(profile.get("eta_crit", np.nan)),
                "eta_dynamic_factor_median": float(profile.get("eta_dynamic_factor_median", np.nan)),
            }
        )

    out = pd.DataFrame(rows).sort_values(["flipped_to_acm", "margin_shift"], ascending=[False, False])
    out.to_csv(OUT_PER, index=False)

    summary = pd.DataFrame(
        [
            {
                "n_hard31": int(len(out)),
                "n_flipped_to_acm": int(out["flipped_to_acm"].sum()),
                "flip_fraction": float(out["flipped_to_acm"].mean()) if len(out) else np.nan,
                "mean_margin_shift": float(np.nanmean(out["margin_shift"])) if len(out) else np.nan,
                "median_margin_shift": float(np.nanmedian(out["margin_shift"])) if len(out) else np.nan,
                "mean_leff_self_shielding_correction_median": float(np.nanmean(out["leff_self_shielding_correction_median"])) if len(out) else np.nan,
                "median_leff_self_shielding_correction_median": float(np.nanmedian(out["leff_self_shielding_correction_median"])) if len(out) else np.nan,
                "mean_sigma_kpc_new": float(np.nanmean(out["sigma_kpc_new"])) if len(out) else np.nan,
                "median_sigma_kpc_new": float(np.nanmedian(out["sigma_kpc_new"])) if len(out) else np.nan,
            }
        ]
    )
    summary.to_csv(OUT_SUM, index=False)

    print("Saved:")
    print(OUT_PER)
    print(OUT_SUM)


if __name__ == "__main__":
    main()
