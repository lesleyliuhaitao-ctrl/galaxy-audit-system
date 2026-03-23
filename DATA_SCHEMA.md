# Data Schema Draft

The public frontend should read static exported data from the research workspace.

The preferred public export path is now:

- `repro_core/scripts/export_frontend_bundle.py`

which regenerates:

- `public/data/audit-bundle.json`
- `public/data/galaxies.json`
- `public/data/pathology-map.json`
- `public/data/profiles/*.json`

## `galaxies.json`

Per galaxy summary entry:

```json
{
  "id": "UGC00128",
  "displayName": "UGC 00128",
  "pathologyTag": "geometry-hostage",
  "winner": "mond",
  "confidence": "fragile",
  "primarySensitivity": "distance",
  "distanceMpc": 64.5,
  "distanceErrorMpc": 9.7,
  "inclinationDeg": 57,
  "acmCpp": 771.68,
  "mondCpp": 292.97,
  "tags": ["LSB", "distance-sensitive", "MOND-resistant"]
}
```

## `profiles/<galaxy>.json`

```json
{
  "id": "UGC00128",
  "radiusKpc": [0.4, 0.8, 1.2],
  "vObs": [20, 30, 42],
  "vObsErr": [3, 2, 4],
  "vAcm": [18, 29, 40],
  "vMond": [22, 31, 43],
  "vGas": [4, 8, 14],
  "vDisk": [10, 18, 24],
  "vBulge": [0, 0, 0]
}
```
