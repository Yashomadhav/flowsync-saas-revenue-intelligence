"""
FlowSync — Plans Generator
Outputs: data/seeds/plans.csv → raw_plans (bronze)
"""

from __future__ import annotations
import csv
import json
from pathlib import Path
from config import PLANS, OUTPUT_DIR


def generate_plans() -> list[dict]:
    rows = []
    for p in PLANS:
        rows.append({
            "plan_id":          p["plan_id"],
            "plan_name":        p["plan_name"],
            "monthly_price":    p["monthly_price"],
            "annual_price":     p["annual_price"],
            "seat_based":       p["seat_based"],
            "price_per_seat":   p["price_per_seat"],
            "min_seats":        p["min_seats"],
            "max_seats":        p["max_seats"],
            "tier":             p["tier"],
            "features_json":    json.dumps(p["features"]),
            "is_active":        True,
        })
    return rows


def save_plans(rows: list[dict], out_dir: Path = OUTPUT_DIR) -> Path:
    path = out_dir / "plans.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[plans] Wrote {len(rows)} rows → {path}")
    return path


if __name__ == "__main__":
    rows = generate_plans()
    save_plans(rows)
