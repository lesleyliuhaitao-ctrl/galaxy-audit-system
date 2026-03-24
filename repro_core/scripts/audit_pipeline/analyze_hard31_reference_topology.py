#!/usr/bin/env python
"""
Reference-family audit for the hard31 galaxies.

Outputs:
- residual topology by reference-token family
- geometry-distance audit focused on whether any hard31 systems have hard
  geometric distance anchors (e.g. f_D = 5)
"""

import os
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_mond_resistant_metadata_table import load_table1_explicit
from analyze_acm_vs_mond import (
    BG_CONTROL_MODE,
    GATE_POWER,
    G_CRIT,
    SHAPE_C_CRIT,
    SHAPE_DEPTH_CRIT,
    SHAPE_DEPTH_MODE,
)
from src.data_loader.load_sparc import load_sparc_rotation_curve
from src.models.acm_dynamics import acm_acceleration
from src.models.eta_path_integral import eta_local_gated_background_profile
from src.models.inclination_correction import get_inclination_correction_for_galaxy


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "research_assets" / "derived_exports"
OUT_TOPO = OUT_DIR / "hard31_reference_topology.csv"
OUT_AUDIT = OUT_DIR / "hard31_geometry_distance_audit.csv"
OUT_FIG = OUT_DIR / "hard31_reference_topology.png"


def current_trunk_params():
    summary = pd.read_csv(ROOT / "analysis_outputs" / "acm_vs_mond_summary.csv").iloc[0]
    return (
        float(summary["acm_eta_base"]),
        float(summary["acm_beta_density"]),
        float(summary["acm_beta_bg"]),
        float(summary["acm_lambda_sup"]),
    )


def tokenize_refs(val):
    if pd.isna(val):
        return []
    return [t.strip() for t in str(val).split(",") if t.strip()]


def acm_residual_profile(galaxy, trunk_params, n_grid=40):
    rc = load_sparc_rotation_curve(galaxy)
    if rc is None or len(rc) < 6 or "Vbar" not in rc.columns:
        return None

    eta_base, beta_density, beta_bg, lambda_sup = trunk_params
    profile = eta_local_gated_background_profile(
        rc,
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
        return None

    r_kpc = rc["Rad"].to_numpy(dtype=float)
    v_obs = rc["Vobs"].to_numpy(dtype=float)
    err_v = rc["errV"].to_numpy(dtype=float)
    vbar = rc["Vbar"].to_numpy(dtype=float)
    valid = (
        np.isfinite(r_kpc) & np.isfinite(v_obs) & np.isfinite(err_v) & np.isfinite(vbar)
        & (r_kpc > 0) & (err_v > 0) & (vbar > 0)
    )
    if np.count_nonzero(valid) < 6:
        return None

    rv = r_kpc[valid]
    vobs = v_obs[valid]
    err = err_v[valid]
    vbar_v = vbar[valid]
    eta_local = np.interp(
        rv,
        profile["r_kpc"],
        profile["eta_local"],
        left=float(profile["eta_local"][0]),
        right=float(profile["eta_local"][-1]),
    )

    r_m = rv * 3.08567758e19
    g_bar = (vbar_v * 1000.0) ** 2 / r_m
    g_acm = acm_acceleration(g_bar, eta_local)
    v_acm = np.sqrt(r_m * g_acm) / 1000.0
    k_inc = float(get_inclination_correction_for_galaxy(galaxy).get("k_inc", 1.0))
    v_acm = v_acm * k_inc

    r_norm = rv / np.nanmax(rv)
    grid = np.linspace(float(np.nanmin(r_norm)), 1.0, n_grid)
    resid = vobs - v_acm
    resid_interp = np.interp(grid, r_norm, resid, left=float(resid[0]), right=float(resid[-1]))
    err_interp = np.interp(grid, r_norm, err, left=float(err[0]), right=float(err[-1]))

    outer_mask = r_norm >= np.nanmedian(r_norm)
    outer_resid_mean = float(np.nanmean(resid[outer_mask])) if np.any(outer_mask) else np.nan
    inner_resid_mean = float(np.nanmean(resid[~outer_mask])) if np.any(~outer_mask) else np.nan

    return {
        "grid": grid,
        "resid_interp": resid_interp,
        "err_interp": err_interp,
        "outer_resid_mean": outer_resid_mean,
        "inner_resid_mean": inner_resid_mean,
        "outer_minus_inner": float(outer_resid_mean - inner_resid_mean) if np.isfinite(outer_resid_mean) and np.isfinite(inner_resid_mean) else np.nan,
        "n_points": int(np.count_nonzero(valid)),
    }


def main():
    os.chdir(ROOT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    per_gal = pd.read_csv(ROOT / "analysis_outputs" / "acm_vs_mond_per_galaxy.csv")
    ml = pd.read_csv(OUT_DIR / "holdout40_ml_sensitivity_ranked.csv")
    edge = pd.read_csv(OUT_DIR / "distance_edge_surrender_members.csv")
    table1 = load_table1_explicit()

    holdout40 = set(edge.loc[edge["subset"] == "holdout_40", "Galaxy"].astype(str))
    ml_flip9 = set(ml.loc[ml["flipped_to_acm"], "Galaxy"].astype(str))
    hard31 = sorted(holdout40 - ml_flip9)

    hard_meta = pd.DataFrame({"Galaxy": hard31}).merge(table1[["Galaxy", "f_D", "Ref", "Qual", "D", "e_D", "Inc", "e_Inc"]], on="Galaxy", how="left")

    token_counter = Counter()
    for ref in hard_meta["Ref"]:
        token_counter.update(tokenize_refs(ref))
    top_tokens = [tok for tok, cnt in token_counter.items() if cnt >= 3]
    top_tokens = sorted(top_tokens, key=lambda t: (-token_counter[t], t))

    trunk_params = current_trunk_params()

    rows = []
    family_curves = {}
    all_hard_curves = []
    for galaxy in hard31:
        meta_row = hard_meta.loc[hard_meta["Galaxy"] == galaxy].iloc[0]
        prof = acm_residual_profile(galaxy, trunk_params)
        if prof is None:
            continue
        all_hard_curves.append(prof["resid_interp"])
        tokens = tokenize_refs(meta_row["Ref"])
        matched = [t for t in tokens if t in top_tokens]
        for token in matched:
            family_curves.setdefault(token, []).append(prof["resid_interp"])
            rows.append(
                {
                    "Galaxy": galaxy,
                    "ref_token": token,
                    "f_D": meta_row["f_D"],
                    "Qual": meta_row["Qual"],
                    "outer_resid_mean": prof["outer_resid_mean"],
                    "inner_resid_mean": prof["inner_resid_mean"],
                    "outer_minus_inner": prof["outer_minus_inner"],
                    "n_points": prof["n_points"],
                }
            )

    topo = pd.DataFrame(rows).sort_values(["ref_token", "outer_minus_inner"], ascending=[True, False])
    topo.to_csv(OUT_TOPO, index=False)

    fd_counts = hard_meta["f_D"].value_counts().sort_index()
    audit = pd.DataFrame(
        [
            {
                "n_hard31": int(len(hard_meta)),
                "n_fd_eq_1": int(fd_counts.get(1, 0)),
                "n_fd_eq_2": int(fd_counts.get(2, 0)),
                "n_fd_eq_3": int(fd_counts.get(3, 0)),
                "n_fd_eq_4": int(fd_counts.get(4, 0)),
                "n_fd_eq_5": int(fd_counts.get(5, 0)),
                "has_fd_eq_5": bool(fd_counts.get(5, 0) > 0),
                "top_tokens": ",".join(top_tokens),
            }
        ]
    )
    audit.to_csv(OUT_AUDIT, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    x = None
    if all_hard_curves:
        hard_mat = np.vstack(all_hard_curves)
        x = np.linspace(0, 1, hard_mat.shape[1])
        axes[0].plot(x, np.nanmedian(hard_mat, axis=0), color="black", lw=2.5, label="hard31 median")

    colors = ["#d62728", "#ff7f0e", "#9467bd", "#2ca02c", "#8c564b", "#1f77b4"]
    for color, token in zip(colors, top_tokens[:6]):
        curves = family_curves.get(token, [])
        if not curves:
            continue
        mat = np.vstack(curves)
        x = np.linspace(0, 1, mat.shape[1])
        med = np.nanmedian(mat, axis=0)
        q25 = np.nanpercentile(mat, 25, axis=0)
        q75 = np.nanpercentile(mat, 75, axis=0)
        axes[0].plot(x, med, color=color, lw=1.8, label=f"{token} (n={len(curves)})")
        axes[0].fill_between(x, q25, q75, color=color, alpha=0.12)
    axes[0].axhline(0.0, color="gray", lw=1, ls="--")
    axes[0].set_title("Hard31 Residual Topology by Ref Token")
    axes[0].set_xlabel("Normalized Radius")
    axes[0].set_ylabel(r"$V_{obs} - V_{ACM}$ (km/s)")
    axes[0].legend(fontsize=8)

    fds = sorted(fd_counts.index.tolist())
    counts = [fd_counts.get(fd, 0) for fd in fds]
    axes[1].bar([str(int(fd)) for fd in fds], counts, color="#d62728", alpha=0.8)
    axes[1].set_title("Hard31 Distance-Flag Audit")
    axes[1].set_xlabel("f_D")
    axes[1].set_ylabel("Count")
    fd5 = int(fd_counts.get(5, 0))
    txt = f"f_D=5 count: {fd5}\nTop tokens: {', '.join(top_tokens[:5])}"
    axes[1].text(0.98, 0.98, txt, ha="right", va="top", transform=axes[1].transAxes,
                 bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))

    fig.suptitle("Hard31 Reference-Family Residual Audit")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("Saved:")
    print(OUT_TOPO)
    print(OUT_AUDIT)
    print(OUT_FIG)


if __name__ == "__main__":
    main()
