from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np


DEFAULT_SFB_ZIP_NAME = "sfb_LTG.zip"
DEFAULT_CORE_CUT_KPC = 0.5


def _candidate_sfb_names(galaxy: str) -> list[str]:
    names = [f"{galaxy}.sfb"]
    for prefix in ("NGC", "UGC", "IC"):
        if galaxy.startswith(prefix):
            suffix = galaxy[len(prefix):]
            stripped = suffix.lstrip("0")
            if stripped and stripped != suffix:
                names.append(f"{prefix}{stripped}.sfb")
    return list(dict.fromkeys(names))


def load_sfb_profile(galaxy: str, sparc_dir: Path, zip_name: str = DEFAULT_SFB_ZIP_NAME):
    sfb_zip = Path(sparc_dir) / zip_name
    if not sfb_zip.exists():
        return None
    with zipfile.ZipFile(sfb_zip) as zf:
        names = set(zf.namelist())
        for candidate in _candidate_sfb_names(galaxy):
            if candidate not in names:
                continue
            lines = zf.read(candidate).decode("utf-8", errors="replace").splitlines()
            rows = []
            for line in lines[1:]:
                parts = line.split()
                if len(parts) < 2:
                    continue
                try:
                    rows.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    continue
            if len(rows) < 5:
                return None
            arr = np.asarray(rows, dtype=float)
            return {"radius": arr[:, 0], "mu": arr[:, 1], "source_name": candidate}
    return None


def compute_sfb_metrics(galaxy: str, sparc_dir: Path, core_cut_kpc: float = DEFAULT_CORE_CUT_KPC):
    profile = load_sfb_profile(galaxy, sparc_dir)
    if profile is None:
        return None
    r = np.asarray(profile["radius"], dtype=float)
    mu = np.asarray(profile["mu"], dtype=float)
    valid = np.isfinite(r) & np.isfinite(mu) & (r > 0)
    if np.count_nonzero(valid) < 5:
        return None
    r = r[valid]
    mu = mu[valid]
    order = np.argsort(r)
    r = r[order]
    mu = mu[order]
    intensity = np.power(10.0, -0.4 * mu)
    area_term = 2.0 * np.pi * r * intensity
    dr = np.gradient(r)
    flux_shell = area_term * dr
    cum_flux = np.cumsum(np.clip(flux_shell, 0.0, None))
    total_flux = float(cum_flux[-1])
    if not np.isfinite(total_flux) or total_flux <= 0:
        return None
    frac = cum_flux / total_flux
    r25 = float(np.interp(0.25, frac, r))
    r75 = float(np.interp(0.75, frac, r))
    c31 = r75 / max(r25, 1e-9)

    disk_mask = r >= float(core_cut_kpc)
    if np.count_nonzero(disk_mask) < 5:
        c31_disk = np.nan
    else:
        r_disk = r[disk_mask]
        intensity_disk = intensity[disk_mask]
        area_disk = 2.0 * np.pi * r_disk * intensity_disk
        dr_disk = np.gradient(r_disk)
        flux_disk = area_disk * dr_disk
        cum_disk = np.cumsum(np.clip(flux_disk, 0.0, None))
        total_disk = float(cum_disk[-1])
        if not np.isfinite(total_disk) or total_disk <= 0:
            c31_disk = np.nan
        else:
            frac_disk = cum_disk / total_disk
            r25_disk = float(np.interp(0.25, frac_disk, r_disk))
            r75_disk = float(np.interp(0.75, frac_disk, r_disk))
            c31_disk = r75_disk / max(r25_disk, 1e-9)
    return {"Galaxy": galaxy, "c31": float(c31), "c31_disk": float(c31_disk) if np.isfinite(c31_disk) else np.nan, "sfb_source": profile["source_name"]}
