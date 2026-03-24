from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
ANALYSIS_DIR = ROOT / "analysis_outputs"
RESEARCH_DATA_DIR = ROOT / "research_assets" / "research_data"
GEOMETRY_PATH = ROOT / "data" / "sparc" / "galaxy_geometry.csv"
TABLE1_PATH = ROOT / "data" / "sparc" / "SPARC_Table1_official.mrt"

TABLE1_COLUMNS = [
    "Galaxy",
    "T",
    "D",
    "e_D",
    "f_D",
    "Inc",
    "e_Inc",
    "L3.6",
    "e_L3.6",
    "Reff",
    "SBeff",
    "Rdisk",
    "SBdisk",
    "MHI",
    "RHI",
    "Vflat",
    "e_Vflat",
    "Qual",
    "Ref",
]


def load_table1_explicit():
    df = pd.read_csv(TABLE1_PATH, skiprows=98, sep=r"\s+", names=TABLE1_COLUMNS)
    df["Galaxy"] = df["Galaxy"].astype(str).str.strip()
    return df.dropna(subset=["Galaxy"]).reset_index(drop=True)


def main():
    RESEARCH_DATA_DIR.mkdir(parents=True, exist_ok=True)

    compare = pd.read_csv(ANALYSIS_DIR / "acm_vs_mond_per_galaxy.csv")
    table1 = load_table1_explicit()
    geometry = pd.read_csv(GEOMETRY_PATH)

    mond_better = compare.loc[compare["delta_cpp_mond_minus_acm"] < 0].copy()
    mond_better = mond_better.sort_values("delta_cpp_mond_minus_acm").reset_index(drop=True)

    merged = mond_better.merge(table1, on="Galaxy", how="left", suffixes=("", "_table1"))
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
                "geometry_mode",
                "is_proxy_fallback",
            ]
        ].rename(columns={"source": "geometry_source"}),
        on="Galaxy",
        how="left",
    )

    merged["distance_rel_err"] = merged["e_D"] / merged["D"]
    merged["distance_rel_err_pct"] = 100.0 * merged["distance_rel_err"]

    column_order = [
        "Galaxy",
        "acm_cpp",
        "mond_cpp",
        "delta_cpp_mond_minus_acm",
        "n_points",
        "n_valid_mond",
        "T",
        "D",
        "e_D",
        "distance_rel_err",
        "distance_rel_err_pct",
        "f_D",
        "Inc",
        "e_Inc",
        "L3.6",
        "e_L3.6",
        "Reff",
        "SBeff",
        "Rdisk",
        "SBdisk",
        "MHI",
        "RHI",
        "Vflat",
        "e_Vflat",
        "Qual",
        "Ref",
        "ba_obs",
        "geometry_source",
        "inc_true_deg",
        "k_inc",
        "velocity_shift_pct",
        "correction_source_used",
        "geometry_qc_flag",
        "geometry_qc_reason",
        "geometry_mode",
        "is_proxy_fallback",
    ]
    merged = merged[column_order]

    out_path = RESEARCH_DATA_DIR / "mond_resistant_original_metadata.csv"
    merged.to_csv(out_path, index=False)

    summary = pd.DataFrame(
        [
            {
                "subset": "mond_better_current_trunk",
                "n_galaxies": int(len(merged)),
                "median_acm_cpp": float(merged["acm_cpp"].median()),
                "median_mond_cpp": float(merged["mond_cpp"].median()),
                "median_delta_cpp_mond_minus_acm": float(merged["delta_cpp_mond_minus_acm"].median()),
                "median_distance_rel_err_pct": float(merged["distance_rel_err_pct"].median()),
                "median_inc_deg": float(merged["Inc"].median()),
                "median_sbeff": float(merged["SBeff"].median()),
                "median_sbdisk": float(merged["SBdisk"].median()),
                "review_geometry_fraction": float((merged["geometry_qc_flag"] == "review").mean()),
                "proxy_geometry_fraction": float(merged["is_proxy_fallback"].fillna(False).astype(bool).mean()),
            }
        ]
    )
    summary.to_csv(RESEARCH_DATA_DIR / "mond_resistant_original_metadata_summary.csv", index=False)

    print(out_path)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
