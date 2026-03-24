## Repro Core

This folder contains the minimal reproducible galaxy-dynamics trunk used by the
second paper's public audit frontend.

Design goal:

- keep the public frontend lightweight
- keep the physics trunk reproducible
- keep the stable galaxy trunk consistent with the current first-paper mainline

This is not a copy of the entire `ACM_Project` research workspace.
It is a compact snapshot of the active galaxy-side forward model:

1. SPARC data loading
2. shape-depth conditioned background continuity
3. anchor-density field construction
4. fully coupled local-response eta field
5. slope-adaptive `L_eff`
6. ACM vs MOND forward rotation-curve prediction
7. frontend audit-bundle export

## Stable Trunk Snapshot

Current retained galaxy-trunk parameters:

- `eta_base = 1.0e-29`
- `beta_density = 4.199484386503164e-28`
- `beta_bg = 7.788726810199519e-29`
- `lambda_sup = 0.16901528439936672`
- `MOND a0 = 1.2e-10`

These values are taken from:

- `ACM_Project/analysis_outputs/acm_vs_mond_summary.csv`

and match the active stable galaxy trunk used for the audit frontend export.

## Layout

- `acm_audit_repro/`
  - minimal Python package for the retained galaxy trunk
- `scripts/export_frontend_bundle.py`
  - regenerates `public/data/*.json`
- `scripts/sync_core_evidence.py`
  - copies the curated evidence subset from `ACM_Project/research_assets/`
- `scripts/audit_pipeline/`
  - archived script snapshots for the paper-II main audit chain
- `scripts/archive_operators/`
  - archived no-new-parameter operator tests referenced by the appendices
- `requirements.txt`
  - minimal Python dependencies
- `TRUNK_SNAPSHOT.json`
  - frozen parameter snapshot and provenance

## Data Expectations

By default the exporter expects:

- `repro_core/data/sparc/`
- `repro_core/data/research_assets/research_data/`
- `repro_core/data/research_assets/derived_exports/`

If your data live elsewhere, pass explicit paths to the exporter.

## Quick Start

```bash
pip install -r repro_core/requirements.txt
python repro_core/scripts/sync_core_evidence.py
python repro_core/scripts/export_frontend_bundle.py
```

## Scope

This package is intentionally galaxy-side only.
It does not duplicate the cosmology trunk.

## Audit Script Snapshots

The second paper does not rely only on the retained trunk and exported tables.
It also depends on a sequence of procedural audit scripts that produced the
distance-edge, stellar-normalization, hard31, topology, and archived-operator
results discussed in the manuscript.

Those scripts are now preserved in two folders:

- `scripts/audit_pipeline/`
- `scripts/archive_operators/`

These are included as provenance-preserving research snapshots. Some of them
still reflect the original research-workspace layout and may require path
cleanup for fully standalone execution, but they are kept here so that the
public repository exposes the actual audit process rather than only its final
tables.
