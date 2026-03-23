from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.special import j1

from .concentration import compute_sfb_metrics
from .config import (
    DEFAULT_BG_CONTROL_MODE,
    DEFAULT_BG_GATE_POWER,
    DEFAULT_BG_G0_SWITCH,
    DEFAULT_BG_GCRIT,
    DEFAULT_COHERENCE_ENABLED,
    DEFAULT_COHERENCE_GAMMA,
    DEFAULT_COHERENCE_L0_RATIO,
    DEFAULT_N_ANCHOR_POWER,
    DEFAULT_SHAPE_C_CRIT,
    DEFAULT_SHAPE_DEPTH_CRIT,
    DEFAULT_SHAPE_DEPTH_MODE,
    FACTOR_2_3,
    MOND_A0,
    OMEGA_B_COSMIC,
    c_ms,
)
from .loaders import (
    load_sparc_galaxy_list,
    load_sparc_geometry_table,
    load_sparc_official_table1,
    load_sparc_rotation_curve,
)


A_CRIT = 1.2e-10
DEFAULT_BG_MU_THRESHOLD = 100.0
DEFAULT_BG_MU_FACTOR_MIN = 0.25
DEFAULT_BG_MU_FACTOR_MAX = 4.0
DEFAULT_BG_SHAPE_FACTOR_MIN = 0.25
DEFAULT_BG_SHAPE_FACTOR_MAX = 4.0
DEFAULT_BG_SHAPE_DEPTH_CRIT_VFLAT = 2.1
DEFAULT_BG_SHAPE_DEPTH_CRIT_L36 = 1.2
DEFAULT_BG_SHAPE_K_C = 2.0
DEFAULT_BG_SHAPE_K_D = 2.0
DEFAULT_Q0_EARLY = 0.12
DEFAULT_Q0_LATE = 0.25


def acm_acceleration(g_bar, eta, factor: float = FACTOR_2_3):
    return g_bar + factor * eta * c_ms**2


def mond_velocity_profile(rc_data):
    r_kpc = rc_data["Rad"].to_numpy(dtype=float)
    vbar = rc_data["Vbar"].to_numpy(dtype=float)
    valid = np.isfinite(r_kpc) & np.isfinite(vbar) & (r_kpc > 0) & (vbar > 0)
    rv = r_kpc[valid]
    r_m = rv * 3.08567758e19
    vbar_ms = vbar[valid] * 1000.0
    g_bar = vbar_ms**2 / r_m
    g_mond = 0.5 * (g_bar + np.sqrt(g_bar**2 + 4.0 * g_bar * float(MOND_A0)))
    v_mond = np.sqrt(r_m * g_mond) / 1000.0
    return valid, v_mond


def load_galaxy_properties(galaxy_name: str, sparc_dir: Path):
    df_list = load_sparc_galaxy_list(sparc_dir)
    row = df_list[df_list["Galaxy"] == galaxy_name]
    if len(row) == 0:
        return None
    return row.iloc[0].to_dict()


def get_rdisk_kpc(galaxy_name: str, rc_data, sparc_dir: Path) -> float:
    props = load_galaxy_properties(galaxy_name, sparc_dir)
    if props is not None:
        rdisk = float(props.get("Rdisk", np.nan))
        if np.isfinite(rdisk) and rdisk > 0:
            return rdisk
    r = rc_data["Rad"].to_numpy(dtype=float)
    r = r[np.isfinite(r) & (r > 0)]
    if len(r) == 0:
        return 1.0
    return float(np.nanmedian(r))


def anchor_density_profile(rc_data, reference_mode: str = "inner_mean"):
    required = {"Rad", "SBdisk", "SBbul", "Vgas"}
    if rc_data is None or not required.issubset(set(rc_data.columns)):
        return None
    r_kpc = rc_data["Rad"].to_numpy(dtype=float)
    sb_disk = rc_data["SBdisk"].to_numpy(dtype=float)
    sb_bul = rc_data["SBbul"].to_numpy(dtype=float)
    v_gas = rc_data["Vgas"].to_numpy(dtype=float)
    valid = np.isfinite(r_kpc) & np.isfinite(sb_disk) & np.isfinite(sb_bul) & np.isfinite(v_gas) & (r_kpc > 0)
    if np.count_nonzero(valid) < 5:
        return None
    order = np.argsort(r_kpc[valid])
    r_kpc = r_kpc[valid][order]
    stellar_proxy = np.clip(sb_disk[valid][order], 0.0, None) + np.clip(sb_bul[valid][order], 0.0, None)
    gas_proxy_raw = np.clip(v_gas[valid][order], 0.0, None) ** 2
    star_ref = np.nanmedian(stellar_proxy[stellar_proxy > 0]) if np.any(stellar_proxy > 0) else 1.0
    gas_ref = np.nanmedian(gas_proxy_raw[gas_proxy_raw > 0]) if np.any(gas_proxy_raw > 0) else 1.0
    star_ref = float(star_ref) if np.isfinite(star_ref) and star_ref > 0 else 1.0
    gas_ref = float(gas_ref) if np.isfinite(gas_ref) and gas_ref > 0 else 1.0
    rho_b_proxy = stellar_proxy / star_ref + gas_proxy_raw / gas_ref
    if reference_mode == "inner_mean":
        rho_ref = float(np.nanmean(rho_b_proxy[: min(3, len(rho_b_proxy))]))
    elif reference_mode == "central_value":
        rho_ref = float(rho_b_proxy[0])
    else:
        rho_ref = float(np.nanmean(rho_b_proxy))
    if not np.isfinite(rho_ref) or rho_ref <= 0:
        rho_ref = 1.0
    return {"r_kpc": r_kpc, "rho_b_proxy": rho_b_proxy, "rho_ref": rho_ref, "n_anchor": rho_b_proxy / rho_ref}


def gradient_profile(rc_data, a_crit: float = A_CRIT):
    if rc_data is None or "Vbar" not in rc_data.columns or "Rad" not in rc_data.columns:
        return None
    r_kpc = rc_data["Rad"].to_numpy(dtype=float)
    vbar = rc_data["Vbar"].to_numpy(dtype=float)
    valid = np.isfinite(r_kpc) & np.isfinite(vbar) & (r_kpc > 0) & (vbar > 0)
    if np.count_nonzero(valid) < 5:
        return None
    r_valid = r_kpc[valid]
    r_m = r_valid * 3.08567758e19
    vbar_ms = vbar[valid] * 1000.0
    g_bar = vbar_ms**2 / r_m
    grad = np.gradient(np.log(g_bar), np.log(r_m))
    return {"r_kpc": r_valid, "g_bar": g_bar, "grad": grad, "lowacc_mask": g_bar < a_crit}


def coherence_score_from_rc(rc_data, gamma: float):
    profile = gradient_profile(rc_data)
    if profile is None:
        return np.nan, np.nan
    grad = np.abs(profile["grad"])
    lowacc_mask = profile["lowacc_mask"]
    ggrad = float(np.nanmean(grad[lowacc_mask])) if np.count_nonzero(lowacc_mask) >= 3 else float(np.nanmean(grad))
    if not np.isfinite(ggrad):
        return np.nan, np.nan
    return float(np.exp(-float(gamma) * ggrad)), ggrad


@lru_cache(maxsize=1)
def _table1_maps(sparc_dir_str: str):
    sparc_dir = Path(sparc_dir_str)
    df = load_sparc_official_table1(sparc_dir)
    sb_map, prop_map = {}, {}
    if not df.empty:
        for _, row in df.iterrows():
            galaxy = str(row.get("Galaxy", "")).strip()
            if not galaxy:
                continue
            sb_disk = row.get("SBdisk", np.nan)
            sb_eff = row.get("SBeff", np.nan)
            mu_val = sb_disk if np.isfinite(sb_disk) else sb_eff
            sb_map[galaxy] = {"mu_mag": float(mu_val) if np.isfinite(mu_val) else np.nan}
            prop_map[galaxy] = {
                "L3.6": float(row.get("L3.6", np.nan)) if np.isfinite(row.get("L3.6", np.nan)) else np.nan,
                "Vflat": float(row.get("Vflat", np.nan)) if np.isfinite(row.get("Vflat", np.nan)) else np.nan,
            }
    return sb_map, prop_map


def _sigmoid(x: float, k: float) -> float:
    return 1.0 / (1.0 + np.exp(-float(k) * float(x)))


def beta_bg_surface_brightness_factor(galaxy_name: str, sparc_dir: Path):
    sb_map, _ = _table1_maps(str(sparc_dir))
    info = sb_map.get(str(galaxy_name).strip(), {})
    mu_value = info.get("mu_mag", np.nan)
    if not np.isfinite(mu_value):
        return {"mu_factor": 1.0}
    raw_factor = float(DEFAULT_BG_MU_THRESHOLD) / max(float(mu_value), 1e-30)
    return {"mu_factor": float(np.clip(raw_factor, DEFAULT_BG_MU_FACTOR_MIN, DEFAULT_BG_MU_FACTOR_MAX))}


def beta_bg_shape_depth_factor(galaxy_name: str, sparc_dir: Path, mode: str = DEFAULT_SHAPE_DEPTH_MODE):
    _, prop_map = _table1_maps(str(sparc_dir))
    props = prop_map.get(str(galaxy_name).strip(), {})
    metrics = compute_sfb_metrics(str(galaxy_name).strip(), sparc_dir)
    if metrics is None:
        return {"shape_depth_factor": 1.0}
    c_metric = metrics["c31_disk"] if np.isfinite(metrics.get("c31_disk", np.nan)) else metrics.get("c31", np.nan)
    if mode == "c31_vflat":
        vflat = float(props.get("Vflat", np.nan))
        depth_metric = float(np.log10(vflat)) if np.isfinite(vflat) and vflat > 0 else np.nan
        depth_crit = DEFAULT_SHAPE_DEPTH_CRIT if DEFAULT_SHAPE_DEPTH_CRIT is not None else DEFAULT_BG_SHAPE_DEPTH_CRIT_VFLAT
    else:
        l36 = float(props.get("L3.6", np.nan))
        depth_metric = float(np.log10(l36)) if np.isfinite(l36) and l36 > 0 else np.nan
        depth_crit = DEFAULT_SHAPE_DEPTH_CRIT if DEFAULT_SHAPE_DEPTH_CRIT is not None else DEFAULT_BG_SHAPE_DEPTH_CRIT_L36
    if not np.isfinite(c_metric) or not np.isfinite(depth_metric):
        return {"shape_depth_factor": 1.0}
    w_c = _sigmoid(float(DEFAULT_SHAPE_C_CRIT) - float(c_metric), DEFAULT_BG_SHAPE_K_C)
    w_d = _sigmoid(float(depth_crit) - float(depth_metric), DEFAULT_BG_SHAPE_K_D)
    raw_factor = w_c * w_d * 4.0
    return {"shape_depth_factor": float(np.clip(raw_factor, DEFAULT_BG_SHAPE_FACTOR_MIN, DEFAULT_BG_SHAPE_FACTOR_MAX))}


def beta_local_hybrid_profile(n_anchor, grad_local, g_bar, beta_density, beta_bg, lambda_sup, galaxy_name: str, sparc_dir: Path, bg_control_mode: str = DEFAULT_BG_CONTROL_MODE):
    n_anchor = np.asarray(n_anchor, dtype=float)
    grad_local = np.asarray(grad_local, dtype=float)
    g_bar = np.asarray(g_bar, dtype=float)
    n_term = np.power(np.clip(n_anchor, 0.0, None), float(DEFAULT_N_ANCHOR_POWER))
    beta_baryon_raw = float(beta_density) * n_term
    suppress = np.clip(1.0 - float(lambda_sup) * np.abs(grad_local), 0.0, 1.0)
    beta_baryon_suppressed = beta_baryon_raw * suppress
    grad_switch = np.tanh(np.abs(grad_local) / max(float(DEFAULT_BG_G0_SWITCH), 1e-6))
    g_ratio = np.clip(float(DEFAULT_BG_GCRIT) / np.clip(g_bar, 1e-30, None), 0.0, None)
    gate_w = 1.0 - np.exp(-np.power(g_ratio, float(DEFAULT_BG_GATE_POWER)))
    mu_info = beta_bg_surface_brightness_factor(galaxy_name, sparc_dir)
    shape_depth_info = beta_bg_shape_depth_factor(galaxy_name, sparc_dir)
    if str(bg_control_mode).strip() == "surface_brightness":
        bg_factor = float(mu_info["mu_factor"])
    elif str(bg_control_mode).strip() == "none":
        bg_factor = 1.0
    else:
        bg_factor = float(shape_depth_info["shape_depth_factor"])
    beta_bg_local = float(beta_bg) * bg_factor * grad_switch * gate_w
    return {"beta_baryon_suppressed": beta_baryon_suppressed, "beta_bg_local": beta_bg_local}


def get_intrinsic_thickness(t_type: float) -> float:
    if not np.isfinite(t_type):
        return np.nan
    if t_type <= 3:
        return DEFAULT_Q0_EARLY
    if t_type >= 8:
        return DEFAULT_Q0_LATE
    return DEFAULT_Q0_EARLY + (DEFAULT_Q0_LATE - DEFAULT_Q0_EARLY) * (float(t_type) - 3.0) / 5.0


@lru_cache(maxsize=1)
def _property_map(sparc_dir_str: str):
    sparc_dir = Path(sparc_dir_str)
    df = load_sparc_official_table1(sparc_dir)[["Galaxy", "T", "Inc"]]
    if df.empty:
        df = load_sparc_galaxy_list(sparc_dir)[["Galaxy", "T", "Inc"]].drop_duplicates(subset=["Galaxy"], keep="first")
    return {row["Galaxy"]: {"T": row["T"], "Inc": row["Inc"]} for _, row in df.iterrows()}


@lru_cache(maxsize=1)
def _geometry_map(sparc_dir_str: str):
    sparc_dir = Path(sparc_dir_str)
    df = load_sparc_geometry_table(sparc_dir)
    if df.empty:
        return {}
    return {row["Galaxy"]: {"ba_obs": row["ba_obs"], "T": row["T"], "Inc": row["Inc"]} for _, row in df.iterrows()}


def get_inclination_correction_for_galaxy(galaxy_name: str, sparc_dir: Path):
    geom = _geometry_map(str(sparc_dir)).get(galaxy_name, {})
    props = _property_map(str(sparc_dir)).get(galaxy_name, {})
    t_type = float(geom.get("T", props.get("T", np.nan)))
    inc_catalog = float(geom.get("Inc", props.get("Inc", np.nan)))
    ba_obs = float(geom.get("ba_obs", np.nan))
    q0 = get_intrinsic_thickness(t_type)
    if np.isfinite(ba_obs):
        if ba_obs <= q0:
            inc_true = 90.0
        else:
            cos2_true = (ba_obs**2 - q0**2) / max(1e-12, 1.0 - q0**2)
            cos2_true = float(np.clip(cos2_true, 0.0, 1.0))
            inc_true = math.degrees(math.acos(math.sqrt(cos2_true)))
    else:
        ba_obs = float(np.clip(math.cos(math.radians(float(inc_catalog))), 0.0, 1.0)) if np.isfinite(inc_catalog) else np.nan
        if not np.isfinite(ba_obs):
            inc_true = np.nan
        elif ba_obs <= q0:
            inc_true = 90.0
        else:
            cos2_true = (ba_obs**2 - q0**2) / max(1e-12, 1.0 - q0**2)
            cos2_true = float(np.clip(cos2_true, 0.0, 1.0))
            inc_true = math.degrees(math.acos(math.sqrt(cos2_true)))
    s_cat = math.sin(math.radians(float(inc_catalog))) if np.isfinite(inc_catalog) else np.nan
    s_true = math.sin(math.radians(float(inc_true))) if np.isfinite(inc_true) else np.nan
    k_inc = 1.0 if not np.isfinite(s_true) or s_true <= 0 else float(s_cat / s_true)
    return {"k_inc": k_inc, "inc_true_deg": inc_true}


def adaptive_gaussian_smooth(r_kpc, values, sigma_profile_kpc):
    r = np.asarray(r_kpc, dtype=float)
    y = np.asarray(values, dtype=float)
    sigma = np.asarray(sigma_profile_kpc, dtype=float)
    smoothed = np.empty_like(y)
    for i, r_i in enumerate(r):
        sigma_i = max(float(sigma[i]), 1e-6)
        w = np.exp(-0.5 * ((r - r_i) / sigma_i) ** 2)
        smoothed[i] = np.sum(w * y) / max(np.sum(w), 1e-30)
    return smoothed


def build_coherence_smoothed_profile(rc_data, base_profile, galaxy_name: str, sparc_dir: Path):
    score, ggrad = coherence_score_from_rc(rc_data, DEFAULT_COHERENCE_GAMMA)
    if not np.isfinite(score):
        return None
    rdisk = get_rdisk_kpc(galaxy_name, rc_data, sparc_dir)
    l_obs_kpc = float(DEFAULT_COHERENCE_L0_RATIO) * float(score) * float(rdisk)
    r = np.asarray(base_profile["r_kpc"], dtype=float)
    eta_local = np.asarray(base_profile["eta_local"], dtype=float)
    valid = np.isfinite(r) & np.isfinite(eta_local) & (r > 0) & (eta_local > 0)
    sigma_profile = np.full_like(r, l_obs_kpc, dtype=float)
    eta_full = eta_local.astype(float, copy=True)
    if np.count_nonzero(valid) >= 5:
        rv = r[valid]
        ev = eta_local[valid]
        order = np.argsort(rv)
        rv = rv[order]
        ev = ev[order]
        deta_dr = np.gradient(ev, rv)
        slope_eta = np.abs(rv * deta_dr / np.maximum(ev, 1e-30))
        correction = 1.0 + float(DEFAULT_COHERENCE_GAMMA) * np.log(1.0 + 1.0 / (slope_eta + 1e-30))
        sigma_valid = np.clip(l_obs_kpc * correction, 0.0, max(float(np.nanmax(rv) - np.nanmin(rv)), 1e-6))
        eta_smoothed = adaptive_gaussian_smooth(rv, ev, sigma_valid)
        sigma_profile[valid] = np.interp(r[valid], rv, sigma_valid, left=float(sigma_valid[0]), right=float(sigma_valid[-1]))
        eta_full[valid] = np.interp(r[valid], rv, eta_smoothed, left=float(eta_smoothed[0]), right=float(eta_smoothed[-1]))
    profile = dict(base_profile)
    profile["eta_local"] = eta_full
    profile["coherence_score"] = float(score)
    profile["ggrad_lowacc_mean"] = float(ggrad)
    profile["sigma_kpc"] = float(np.nanmedian(sigma_profile))
    profile["sigma_profile_kpc"] = sigma_profile
    profile["l_obs_kpc"] = float(l_obs_kpc)
    profile["rdisk_kpc"] = float(rdisk)
    return profile


def eta_local_gated_background_profile(rc_data, eta_base: float, beta_density: float, beta_bg: float, lambda_sup: float, galaxy_name: str, sparc_dir: Path):
    anchor_profile = anchor_density_profile(rc_data)
    profile = gradient_profile(rc_data)
    if profile is None or anchor_profile is None:
        return None
    r_grad = profile["r_kpc"]
    grad_local = np.abs(profile["grad"])
    g_bar = profile["g_bar"]
    n_anchor_interp = np.interp(r_grad, anchor_profile["r_kpc"], np.clip(anchor_profile["n_anchor"], 0.0, None), left=float(anchor_profile["n_anchor"][0]), right=float(anchor_profile["n_anchor"][-1]))
    beta_info = beta_local_hybrid_profile(n_anchor_interp, grad_local, g_bar, beta_density, beta_bg, lambda_sup, galaxy_name, sparc_dir)
    coherence_score_pre, _ = coherence_score_from_rc(rc_data, DEFAULT_COHERENCE_GAMMA)
    if not np.isfinite(coherence_score_pre):
        coherence_score_pre = 1.0
    beta_total_coupled = np.asarray(beta_info["beta_baryon_suppressed"], dtype=float) + np.asarray(beta_info["beta_bg_local"], dtype=float) * float(coherence_score_pre)
    eta_local_pre = float(eta_base) + beta_total_coupled * grad_local
    eta_local = eta_local_pre.astype(float, copy=True)
    valid_eta = np.isfinite(eta_local_pre) & (eta_local_pre > 0)
    if np.any(valid_eta):
        phi_local = eta_local_pre[valid_eta] / max(float(eta_base), 1e-30)
        saturation_ratio = np.clip(float(eta_base) / eta_local_pre[valid_eta], 0.0, 1.0)
        eta_dynamic_factor = 1.0 - float(OMEGA_B_COSMIC) * j1(phi_local) * saturation_ratio
        eta_local[valid_eta] = eta_local_pre[valid_eta] * eta_dynamic_factor
    base_profile = {"r_kpc": r_grad, "eta_local": eta_local}
    if DEFAULT_COHERENCE_ENABLED:
        coherence_profile = build_coherence_smoothed_profile(rc_data, base_profile, galaxy_name, sparc_dir)
        if coherence_profile is not None:
            return coherence_profile
    return base_profile


def acm_velocity_profile(galaxy: str, rc_data, trunk_params: dict, sparc_dir: Path):
    profile = eta_local_gated_background_profile(rc_data, float(trunk_params["eta_base"]), float(trunk_params["beta_density"]), float(trunk_params["beta_bg"]), float(trunk_params["lambda_sup"]), galaxy, sparc_dir)
    if profile is None:
        return None
    r_kpc = rc_data["Rad"].to_numpy(dtype=float)
    vbar = rc_data["Vbar"].to_numpy(dtype=float)
    valid = np.isfinite(r_kpc) & np.isfinite(vbar) & (r_kpc > 0) & (vbar > 0)
    rv = r_kpc[valid]
    eta_local = np.interp(rv, profile["r_kpc"], profile["eta_local"], left=float(profile["eta_local"][0]), right=float(profile["eta_local"][-1]))
    r_m = rv * 3.08567758e19
    vbar_ms = vbar[valid] * 1000.0
    g_bar = vbar_ms**2 / r_m
    g_acm = acm_acceleration(g_bar, eta_local)
    return valid, np.sqrt(r_m * g_acm) / 1000.0


def predict_rotation_curve(galaxy_name: str, sparc_dir: Path, trunk_params: dict):
    rc = load_sparc_rotation_curve(galaxy_name, sparc_dir)
    if rc is None or len(rc) < 6:
        return None
    acm_prof = acm_velocity_profile(galaxy_name, rc, trunk_params, sparc_dir)
    mond_prof = mond_velocity_profile(rc)
    if acm_prof is None:
        return None
    valid_acm, v_acm_valid = acm_prof
    valid_mond, v_mond_valid = mond_prof
    k_inc = float(get_inclination_correction_for_galaxy(galaxy_name, sparc_dir).get("k_inc", 1.0))
    r_all = rc["Rad"].to_numpy(dtype=float)
    v_acm = np.full_like(r_all, np.nan, dtype=float)
    v_mond = np.full_like(r_all, np.nan, dtype=float)
    v_acm[valid_acm] = v_acm_valid * k_inc
    v_mond[valid_mond] = v_mond_valid * k_inc
    mask = np.isfinite(r_all)
    return {
        "id": galaxy_name,
        "radiusKpc": [float(x) for x in r_all[mask]],
        "vObs": [float(x) for x in rc["Vobs"].to_numpy(dtype=float)[mask]],
        "vObsErr": [float(x) for x in rc["errV"].to_numpy(dtype=float)[mask]],
        "vAcm": [float(x) if np.isfinite(x) else None for x in v_acm[mask]],
        "vMond": [float(x) if np.isfinite(x) else None for x in v_mond[mask]],
        "vGas": [float(x) for x in rc["Vgas"].to_numpy(dtype=float)[mask]],
        "vDisk": [float(x) for x in rc["Vdisk"].to_numpy(dtype=float)[mask]],
        "vBulge": [float(x) for x in rc["Vbul"].to_numpy(dtype=float)[mask]],
    }
