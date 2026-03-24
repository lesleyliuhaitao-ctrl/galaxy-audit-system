#!/usr/bin/env python
"""
Compare raw Vgas observational spectra between the final hard31 galaxies and
the ACM-dominant 102 galaxies.
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
from src.data_loader.load_sparc import load_sparc_rotation_curve


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "research_assets" / "derived_exports"
OUT_SUM = OUT_DIR / "vgas_spectrum_hard31_vs_acm102_summary.csv"
OUT_PER = OUT_DIR / "vgas_spectrum_hard31_vs_acm102_per_galaxy.csv"
OUT_FD = OUT_DIR / "vgas_spectrum_hard31_vs_acm102_fd_counts.csv"
OUT_REF = OUT_DIR / "vgas_spectrum_hard31_vs_acm102_ref_tokens.csv"
OUT_FIG = OUT_DIR / "vgas_spectrum_hard31_vs_acm102.png"


def interp_profile(rc, n_grid=64):
    if rc is None or not {"Rad", "Vgas"}.issubset(set(rc.columns)):
        return None
    r = pd.to_numeric(rc["Rad"], errors="coerce").to_numpy(dtype=float)
    v = pd.to_numeric(rc["Vgas"], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(r) & np.isfinite(v) & (r > 0) & (v >= 0)
    if np.count_nonzero(valid) < 6:
        return None
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
        return None
    return grid, v_interp / vmax


def spectrum_metrics(v_norm):
    y = np.asarray(v_norm, dtype=float)
    y = y - np.nanmean(y)
    power = np.abs(np.fft.rfft(y)) ** 2
    if len(power) <= 1:
        return None
    power = power[1:]  # drop DC
    total = float(np.sum(power))
    if not np.isfinite(total) or total <= 0:
        return None
    power_norm = power / total
    freqs = np.arange(1, len(power_norm) + 1, dtype=float)
    hi_start = int(np.ceil(len(power_norm) * 0.5))
    hi_frac = float(np.sum(power_norm[hi_start:])) if hi_start < len(power_norm) else 0.0
    mid_start = int(np.ceil(len(power_norm) * 0.25))
    mid_frac = float(np.sum(power_norm[mid_start:])) if mid_start < len(power_norm) else 0.0
    smoothness = 1.0 - hi_frac
    return freqs, power_norm, hi_frac, mid_frac, smoothness


def tokenize_refs(series):
    counter = Counter()
    for val in series.dropna().astype(str):
        for token in [t.strip() for t in val.split(",") if t.strip()]:
            counter[token] += 1
    return counter


def main():
    os.chdir(ROOT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    per_gal = pd.read_csv(ROOT / "analysis_outputs" / "acm_vs_mond_per_galaxy.csv")
    edge = pd.read_csv(OUT_DIR / "distance_edge_surrender_members.csv")
    ml = pd.read_csv(OUT_DIR / "holdout40_ml_sensitivity_ranked.csv")
    table1 = load_table1_explicit()

    holdout40 = set(edge.loc[edge["subset"] == "holdout_40", "Galaxy"].astype(str))
    ml_flip9 = set(ml.loc[ml["flipped_to_acm"], "Galaxy"].astype(str))
    hard31 = sorted(holdout40 - ml_flip9)
    acm102 = sorted(per_gal.loc[per_gal["delta_cpp_mond_minus_acm"] > 0, "Galaxy"].astype(str))

    rows = []
    spectra = {"hard31": [], "acm102": []}
    for subset_name, galaxies in [("hard31", hard31), ("acm102", acm102)]:
        for galaxy in galaxies:
            rc = load_sparc_rotation_curve(galaxy)
            prof = interp_profile(rc)
            if prof is None:
                continue
            _, v_norm = prof
            spec = spectrum_metrics(v_norm)
            if spec is None:
                continue
            freqs, power_norm, hi_frac, mid_frac, smoothness = spec
            spectra[subset_name].append(power_norm)
            rows.append(
                {
                    "Galaxy": galaxy,
                    "subset": subset_name,
                    "n_freq_bins": int(len(power_norm)),
                    "high_freq_power_frac": hi_frac,
                    "midplus_freq_power_frac": mid_frac,
                    "smoothness_score": smoothness,
                }
            )

    per = pd.DataFrame(rows)
    per.to_csv(OUT_PER, index=False)

    meta = table1[["Galaxy", "f_D", "Ref"]].copy()
    meta["Galaxy"] = meta["Galaxy"].astype(str)
    hard_meta = pd.DataFrame({"Galaxy": hard31}).merge(meta, on="Galaxy", how="left")
    acm_meta = pd.DataFrame({"Galaxy": acm102}).merge(meta, on="Galaxy", how="left")

    fd_rows = []
    for subset_name, df in [("hard31", hard_meta), ("acm102", acm_meta)]:
        counts = df["f_D"].value_counts(dropna=False).sort_index()
        total = max(int(counts.sum()), 1)
        for key, val in counts.items():
            fd_rows.append(
                {
                    "subset": subset_name,
                    "f_D": int(key) if pd.notna(key) else -1,
                    "count": int(val),
                    "fraction": float(val / total),
                }
            )
    fd_df = pd.DataFrame(fd_rows)
    fd_df.to_csv(OUT_FD, index=False)

    ref_rows = []
    hard_counter = tokenize_refs(hard_meta["Ref"])
    acm_counter = tokenize_refs(acm_meta["Ref"])
    top_tokens = sorted(
        set([k for k, _ in hard_counter.most_common(8)] + [k for k, _ in acm_counter.most_common(8)])
    )
    for subset_name, counter, total in [
        ("hard31", hard_counter, max(sum(hard_counter.values()), 1)),
        ("acm102", acm_counter, max(sum(acm_counter.values()), 1)),
    ]:
        for token in top_tokens:
            ref_rows.append(
                {
                    "subset": subset_name,
                    "ref_token": token,
                    "count": int(counter.get(token, 0)),
                    "fraction": float(counter.get(token, 0) / total),
                }
            )
    ref_df = pd.DataFrame(ref_rows)
    ref_df.to_csv(OUT_REF, index=False)

    def summarize_subset(name):
        sub = per[per["subset"] == name]
        return {
            "subset": name,
            "n_galaxies": int(len(sub)),
            "mean_high_freq_power_frac": float(sub["high_freq_power_frac"].mean()),
            "median_high_freq_power_frac": float(sub["high_freq_power_frac"].median()),
            "mean_smoothness_score": float(sub["smoothness_score"].mean()),
            "median_smoothness_score": float(sub["smoothness_score"].median()),
        }

    summary = pd.DataFrame([summarize_subset("hard31"), summarize_subset("acm102")])
    summary.to_csv(OUT_SUM, index=False)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    for subset_name, color in [("hard31", "#d62728"), ("acm102", "#1f77b4")]:
        if spectra[subset_name]:
            mat = np.vstack(spectra[subset_name])
            median_spec = np.nanmedian(mat, axis=0)
            q25 = np.nanpercentile(mat, 25, axis=0)
            q75 = np.nanpercentile(mat, 75, axis=0)
            x = np.arange(1, len(median_spec) + 1)
            axes[0, 0].plot(x, median_spec, color=color, lw=2, label=subset_name)
            axes[0, 0].fill_between(x, q25, q75, color=color, alpha=0.18)
    axes[0, 0].set_title("Raw Vgas Spectral Power")
    axes[0, 0].set_xlabel("Frequency Bin")
    axes[0, 0].set_ylabel("Normalized Power")
    axes[0, 0].legend()

    for subset_name, color in [("hard31", "#d62728"), ("acm102", "#1f77b4")]:
        sub = per[per["subset"] == subset_name]["high_freq_power_frac"].to_numpy(dtype=float)
        x0 = 0 if subset_name == "hard31" else 1
        jitter = np.linspace(-0.12, 0.12, len(sub)) if len(sub) else np.array([])
        axes[0, 1].scatter(np.full(len(sub), x0) + jitter, sub, color=color, alpha=0.7, s=16)
        if len(sub):
            axes[0, 1].hlines(np.nanmedian(sub), x0 - 0.2, x0 + 0.2, color=color, lw=2)
    axes[0, 1].set_xticks([0, 1], ["hard31", "acm102"])
    axes[0, 1].set_ylabel("High-Frequency Power Fraction")
    axes[0, 1].set_title("Spectral Smoothness Contrast")

    fd_pivot = fd_df.pivot(index="f_D", columns="subset", values="fraction").fillna(0.0).sort_index()
    fd_pivot.plot(kind="bar", ax=axes[1, 0], color=["#d62728", "#1f77b4"])
    axes[1, 0].set_title("Distance-Flag (f_D) Distribution")
    axes[1, 0].set_xlabel("f_D")
    axes[1, 0].set_ylabel("Fraction")
    axes[1, 0].legend(title="")

    ref_pivot = ref_df.pivot(index="ref_token", columns="subset", values="fraction").fillna(0.0)
    ref_pivot = ref_pivot.sort_values(by="hard31", ascending=False)
    ref_pivot.head(8).plot(kind="bar", ax=axes[1, 1], color=["#d62728", "#1f77b4"])
    axes[1, 1].set_title("Top Ref Tokens")
    axes[1, 1].set_xlabel("Ref token")
    axes[1, 1].set_ylabel("Token Fraction")
    axes[1, 1].legend(title="")
    axes[1, 1].tick_params(axis="x", rotation=45)

    fig.suptitle("Hard31 vs ACM-better 102: Raw Vgas Spectra and Source Fingerprints")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("Saved:")
    print(OUT_SUM)
    print(OUT_PER)
    print(OUT_FD)
    print(OUT_REF)
    print(OUT_FIG)


if __name__ == "__main__":
    main()
