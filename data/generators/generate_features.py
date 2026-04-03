"""
FlowSync — Features Generator
Outputs: data/seeds/features.csv → raw_features (bronze)
"""

from __future__ import annotations
import csv
from pathlib import Path
from config import FEATURES, OUTPUT_DIR


def generate_features() -> list[dict]:
    rows = []
    for f in FEATURES:
        rows.append({
            "feature_id":   f["feature_id"],
            "feature_name": f["feature_name"],
            "category":     f["category"],
            "is_active":    True,
        })
    return rows


def save_features(rows: list[dict], out_dir: Path = OUTPUT_DIR) -> Path:
    path = out_dir / "features.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[features] Wrote {len(rows)} rows → {path}")
    return path


if __name__ == "__main__":
    rows = generate_features()
    save_features(rows)
