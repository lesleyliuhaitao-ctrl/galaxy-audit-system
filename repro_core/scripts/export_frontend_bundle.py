from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
REPRO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPRO_ROOT))

from acm_audit_repro.config import DEFAULT_RESEARCH_DATA_DIR, DEFAULT_SPARC_DIR, PUBLIC_DATA_DIR, STABLE_TRUNK_PARAMS
from acm_audit_repro.trunk import predict_rotation_curve


def pathology_tags(group: str) -> list[str]:
    return {
        "acm_better_102": ["acm-recovered"],
        "geom_hostage_22": ["distance-sensitive", "MOND-resistant"],
        "stellar_hostage_9": ["stellar-hostage", "MOND-resistant"],
        "gas_flat_hard31": ["gas-flat", "MOND-resistant", "geometry-fragile"],
    }.get(group, ["MOND-resistant"])


def primary_sensitivity(group: str) -> str:
    return {
        "acm_better_102": "distance",
        "geom_hostage_22": "distance",
        "stellar_hostage_9": "mass-normalization",
        "gas_flat_hard31": "shape-depth",
    }.get(group, "distance")


def confidence_label(group: str) -> str:
    return {
        "acm_better_102": "high",
        "geom_hostage_22": "fragile",
        "stellar_hostage_9": "medium",
        "gas_flat_hard31": "fragile",
    }.get(group, "medium")


def winner(delta_cpp: float) -> str:
    if delta_cpp > 0:
        return "acm"
    if delta_cpp < 0:
        return "mond"
    return "ambiguous"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sparc-dir", type=Path, default=DEFAULT_SPARC_DIR)
    parser.add_argument("--audit-csv", type=Path, default=DEFAULT_RESEARCH_DATA_DIR / "full_sample_residual_pathology_audit.csv")
    parser.add_argument("--output-dir", type=Path, default=PUBLIC_DATA_DIR)
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = args.output_dir
    profile_dir = output_dir / "profiles"
    output_dir.mkdir(parents=True, exist_ok=True)
    profile_dir.mkdir(parents=True, exist_ok=True)
    audit = pd.read_csv(args.audit_csv)

    galaxy_entries = []
    pathology_points = []
    for _, row in audit.iterrows():
        galaxy = str(row["Galaxy"])
        profile_payload = predict_rotation_curve(galaxy, args.sparc_dir, STABLE_TRUNK_PARAMS)
        if profile_payload is None:
            continue
        with open(profile_dir / f"{galaxy}.json", "w", encoding="utf-8") as f:
            json.dump(profile_payload, f, ensure_ascii=False)

        group = str(row["pathology_group"])
        galaxy_entries.append(
            {
                "id": galaxy,
                "displayName": galaxy.replace("_", " "),
                "pathologyGroup": group,
                "winner": winner(float(row["delta_cpp_mond_minus_acm"])),
                "confidence": confidence_label(group),
                "primarySensitivity": primary_sensitivity(group),
                "pathologyTags": pathology_tags(group),
                "distanceMpc": float(row["D"]),
                "distanceErrorMpc": float(row["e_D"]),
                "inclinationDeg": float(row["Inc"]),
                "geometryFlag": str(row["geometry_qc_flag"]) if pd.notna(row.get("geometry_qc_flag", None)) else "ok",
                "acmCpp": float(row["acm_cpp"]),
                "mondCpp": float(row["mond_cpp"]),
                "profilePath": f"/data/profiles/{galaxy}.json",
                "profile": profile_payload,
                "structure": {
                    "l36": float(row["L3.6"]),
                    "gasToLightProxy": float(row["gas_to_light_proxy"]),
                    "outerGasSlope": float(row["gas_abs_slope_outer_mean"]),
                    "outerGasCurvature": float(row["gas_abs_curvature_outer_mean"]),
                    "outerToInnerGasRatio": float(row["gas_outer_to_inner_ratio"]),
                },
            }
        )
        pathology_points.append(
            {
                "id": galaxy,
                "group": group,
                "distanceRelErrPct": float(row["distance_rel_err_pct"]),
                "deltaCppMondMinusAcm": float(row["delta_cpp_mond_minus_acm"]),
                "l36": float(row["L3.6"]),
                "gasToLightProxy": float(row["gas_to_light_proxy"]),
                "outerGasSlope": float(row["gas_abs_slope_outer_mean"]),
                "outerToInnerGasRatio": float(row["gas_outer_to_inner_ratio"]),
                "outerGasCurvature": float(row["gas_abs_curvature_outer_mean"]),
                "vgasHighFreqPowerFrac": float(row["vgas_high_freq_power_frac"]),
            }
        )

    bundle = {
        "summary": {"nGalaxies": len(galaxy_entries), "defaultGalaxyId": "UGC00128", "source": "galaxy-audit-system/repro_core", "stableTrunk": STABLE_TRUNK_PARAMS},
        "galaxies": galaxy_entries,
        "pathologyMap": {"points": pathology_points},
    }
    for name, payload in [("audit-bundle.json", bundle), ("galaxies.json", galaxy_entries), ("pathology-map.json", {"points": pathology_points})]:
        with open(output_dir / name, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    print(output_dir / "audit-bundle.json")


if __name__ == "__main__":
    main()
