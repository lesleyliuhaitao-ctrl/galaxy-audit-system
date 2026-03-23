from __future__ import annotations

import json
from pathlib import Path

import numpy as np


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parent
PUBLIC_DATA_DIR = REPO_ROOT / "public" / "data"
TRUNK_SNAPSHOT_PATH = PACKAGE_ROOT / "TRUNK_SNAPSHOT.json"
DEV_ACM_PROJECT_ROOT = REPO_ROOT.parent / "ACM_Project"

DEFAULT_DATA_ROOT = PACKAGE_ROOT / "data"
DEFAULT_SPARC_DIR = (
    DEFAULT_DATA_ROOT / "sparc"
    if (DEFAULT_DATA_ROOT / "sparc").exists()
    else DEV_ACM_PROJECT_ROOT / "data" / "sparc"
)
DEFAULT_RESEARCH_ROOT = (
    DEFAULT_DATA_ROOT / "research_assets"
    if (DEFAULT_DATA_ROOT / "research_assets").exists()
    else DEV_ACM_PROJECT_ROOT / "research_assets"
)
DEFAULT_RESEARCH_DATA_DIR = DEFAULT_RESEARCH_ROOT / "research_data"
DEFAULT_DERIVED_EXPORTS_DIR = DEFAULT_RESEARCH_ROOT / "derived_exports"

c = 299792.458
c_ms = 299792458.0
G = 6.67430e-11
Mpc_to_m = 3.08567758e22
km_to_m = 1000.0
FACTOR_2_3 = 2.0 / 3.0

H0_km_s_Mpc = ((8.0 / (3.0 * np.pi)) ** 2) * 100.0
BETA_BG_KAPPA = 0.01
BETA_BG_COSMIC = BETA_BG_KAPPA * (H0_km_s_Mpc * km_to_m / Mpc_to_m) / c_ms
OMEGA_B_COSMIC = 3.0 / 64.0

DEFAULT_N_ANCHOR_POWER = 1.0 / 3.0
DEFAULT_BG_G0_SWITCH = 1.0
DEFAULT_BG_GCRIT = 3.0e-11
DEFAULT_BG_GATE_POWER = 1.0
DEFAULT_BG_CONTROL_MODE = "shape_depth"
DEFAULT_COHERENCE_ENABLED = True
DEFAULT_COHERENCE_L0_RATIO = 1.0 / (4.0 * np.pi)
DEFAULT_COHERENCE_GAMMA = 1.0 / (32.0 * np.pi)

DEFAULT_SHAPE_DEPTH_MODE = "c31_vflat"
DEFAULT_SHAPE_C_CRIT = 2.6
DEFAULT_SHAPE_DEPTH_CRIT = None
MOND_A0 = 1.2e-10

with open(TRUNK_SNAPSHOT_PATH, "r", encoding="utf-8") as _f:
    _SNAPSHOT = json.load(_f)

STABLE_TRUNK_PARAMS = _SNAPSHOT["stable_galaxy_trunk"]
