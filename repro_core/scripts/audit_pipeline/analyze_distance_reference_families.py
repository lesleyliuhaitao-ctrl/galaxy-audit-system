from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
DERIVED_DIR = ROOT / "research_assets" / "derived_exports"


def ref_tokens(ref: str) -> list[str]:
    if not isinstance(ref, str):
        return []
    return [part.strip() for part in ref.split(",") if part.strip()]


def main():
    df = pd.read_csv(DERIVED_DIR / "distance_edge_surrender_members.csv")

    token_rows = []
    for _, row in df.iterrows():
        for token in ref_tokens(row.get("Ref", "")):
            token_rows.append(
                {
                    "Galaxy": row["Galaxy"],
                    "subset": row["subset"],
                    "flipped_at_edge": row["flipped_at_edge"],
                    "best_margin_shift": row["best_margin_shift"],
                    "distance_rel_err_pct": row["distance_rel_err_pct"],
                    "f_D": row["f_D"],
                    "Ref_token": token,
                }
            )

    token_df = pd.DataFrame(token_rows)
    token_df.to_csv(DERIVED_DIR / "distance_edge_surrender_ref_tokens.csv", index=False)

    token_summary = (
        token_df.groupby(["subset", "Ref_token"], dropna=False)
        .agg(
            n_galaxies=("Galaxy", "nunique"),
            mean_best_margin_shift=("best_margin_shift", "mean"),
            median_distance_rel_err_pct=("distance_rel_err_pct", "median"),
            mean_f_D=("f_D", "mean"),
        )
        .reset_index()
        .sort_values(["subset", "n_galaxies", "mean_best_margin_shift"], ascending=[True, False, False])
    )
    token_summary.to_csv(DERIVED_DIR / "distance_edge_surrender_ref_token_summary.csv", index=False)

    surrendered = df[df["subset"] == "surrender_22"].copy()
    surrendered_fd1 = surrendered[surrendered["f_D"] == 1].copy()
    surrendered_fd1.to_csv(DERIVED_DIR / "distance_edge_surrender_fd1_members.csv", index=False)

    print((DERIVED_DIR / "distance_edge_surrender_ref_token_summary.csv").resolve())
    print(token_summary.to_string(index=False))


if __name__ == "__main__":
    main()
