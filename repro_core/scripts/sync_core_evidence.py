from __future__ import annotations

import csv
import shutil
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
MANIFEST = REPO_ROOT / "data" / "evidence" / "manifests" / "core_evidence_manifest.csv"


def main():
    with open(MANIFEST, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        src = REPO_ROOT.parent / row["source_path"]
        dst = REPO_ROOT / row["target_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"{src} -> {dst}")


if __name__ == "__main__":
    main()
