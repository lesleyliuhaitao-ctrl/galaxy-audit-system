from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


TABLE1_COLUMNS = [
    "Galaxy", "T", "D", "e_D", "f_D", "Inc", "e_Inc", "L3.6", "e_L3.6",
    "Reff", "SBeff", "Rdisk", "SBdisk", "MHI", "RHI", "Vflat", "e_Vflat", "Qual", "Ref",
]
TABLE2_COLUMNS = [
    "Galaxy", "T", "D", "e_D", "Inc", "e_Inc", "L3.6", "e_L3.6", "Reff", "Sersic",
    "Mb", "e_Mb", "Rdisk", "Mstar", "e_Mstar", "Mg", "e_Mg", "Qual",
]
GEOMETRY_COLUMNS = ["Galaxy", "ba_obs", "T", "Inc", "source", "geometry_qc_flag", "geometry_qc_reason"]


def load_sparc_galaxy_list(sparc_dir: Path) -> pd.DataFrame:
    return pd.read_csv(Path(sparc_dir) / "Table2.mrt", skiprows=42, sep=r"\s+", names=TABLE2_COLUMNS)


def load_sparc_rotation_curve(galaxy_name: str, sparc_dir: Path) -> pd.DataFrame | None:
    file_path = Path(sparc_dir) / "rotmod" / f"{galaxy_name}_rotmod.dat"
    if not file_path.exists():
        return None
    df = pd.read_csv(file_path, sep=r"\s+", comment="#", names=["Rad", "Vobs", "errV", "Vgas", "Vdisk", "Vbul", "SBdisk", "SBbul"])
    df = df[df["Vobs"] > 0].copy()
    if df.empty:
        return None
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "Distance" in line:
                try:
                    df["D"] = float(line.split("=")[1].split()[0])
                except Exception:
                    pass
                break
    df["Vbar"] = np.sqrt(df["Vgas"] ** 2 + df["Vdisk"] ** 2 + df["Vbul"] ** 2)
    return df


def load_sparc_official_table1(sparc_dir: Path) -> pd.DataFrame:
    file_path = Path(sparc_dir) / "SPARC_Table1_official.mrt"
    if not file_path.exists():
        return pd.DataFrame(columns=TABLE1_COLUMNS)
    df = pd.read_csv(file_path, skiprows=98, sep=r"\s+", names=TABLE1_COLUMNS)
    df["Galaxy"] = df["Galaxy"].astype(str).str.strip()
    return df.dropna(subset=["Galaxy"]).reset_index(drop=True)


def load_sparc_geometry_table(sparc_dir: Path) -> pd.DataFrame:
    file_path = Path(sparc_dir) / "galaxy_geometry.csv"
    if not file_path.exists():
        return pd.DataFrame(columns=GEOMETRY_COLUMNS)
    df = pd.read_csv(file_path)
    required = {"Galaxy", "ba_obs"}
    if not required.issubset(df.columns):
        missing = ", ".join(sorted(required - set(df.columns)))
        raise ValueError(f"galaxy_geometry.csv missing required columns: {missing}")
    for optional in ["T", "Inc", "source", "geometry_qc_flag", "geometry_qc_reason"]:
        if optional not in df.columns:
            df[optional] = np.nan if optional != "source" else "user_supplied"
    return df[GEOMETRY_COLUMNS].drop_duplicates(subset=["Galaxy"], keep="first").reset_index(drop=True)
