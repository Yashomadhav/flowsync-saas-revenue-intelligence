"""
FlowSync — Accounts Generator
Outputs: data/seeds/accounts.csv → raw_accounts (bronze)

Generates realistic B2B SaaS accounts with:
- Industry, region, company size, acquisition channel segmentation
- Health score baseline (used downstream by subscription/usage generators)
- Account creation spread across 24-month simulation window
- Realistic company name generation using Faker
"""

from __future__ import annotations
import csv
import uuid
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker
from config import (
    RANDOM_SEED, OUTPUT_DIR, SIM_START_DATE, SIM_END_DATE,
    INDUSTRIES, REGIONS, COMPANY_SIZES, ACQUISITION_CHANNELS,
    PLAN_IDS, PLAN_MAP, TARGET_ACCOUNTS, weighted_choice, add_months,
)

fake = Faker()
fake.seed_instance(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Segmentation weights — realistic B2B SaaS distribution
# ---------------------------------------------------------------------------
INDUSTRY_WEIGHTS   = [18, 14, 10, 12, 8, 8, 7, 7, 8, 8]   # sum=100
REGION_WEIGHTS     = [45, 28, 15, 8, 4]                     # NA-heavy
SIZE_WEIGHTS       = [50, 35, 15]                            # SMB-heavy
CHANNEL_WEIGHTS    = [20, 18, 15, 12, 12, 12, 6, 5]

# Plan distribution by company size
PLAN_BY_SIZE = {
    "SMB":         {"plan_starter": 0.55, "plan_growth": 0.35, "plan_pro": 0.08, "plan_enterprise": 0.02},
    "Mid-Market":  {"plan_starter": 0.10, "plan_growth": 0.40, "plan_pro": 0.35, "plan_enterprise": 0.15},
    "Enterprise":  {"plan_starter": 0.02, "plan_growth": 0.10, "plan_pro": 0.30, "plan_enterprise": 0.58},
}

# Employee count ranges by company size
EMPLOYEE_RANGES = {
    "SMB":        (5, 50),
    "Mid-Market": (51, 500),
    "Enterprise": (501, 10_000),
}

# Health score baseline by plan tier (higher plan → better onboarding → higher health)
HEALTH_BASELINE_BY_PLAN = {
    "plan_starter":    (45, 75),
    "plan_growth":     (55, 82),
    "plan_pro":        (62, 88),
    "plan_enterprise": (70, 95),
}


def _pick_plan(company_size: str) -> str:
    dist = PLAN_BY_SIZE[company_size]
    return random.choices(list(dist.keys()), weights=list(dist.values()), k=1)[0]


def _random_account_created_at(idx: int, total: int) -> date:
    """
    Spread account creation across the simulation window with a growth curve.
    Earlier months get fewer accounts; later months get more (organic growth).
    """
    total_days = (SIM_END_DATE - SIM_START_DATE).days
    # Growth curve: weight later dates more heavily
    progress = (idx / total) ** 0.6  # sub-linear → more accounts in later months
    day_offset = int(progress * total_days * random.uniform(0.85, 1.0))
    day_offset = min(day_offset, total_days - 1)
    return SIM_START_DATE + timedelta(days=day_offset)


def generate_accounts(n: int = TARGET_ACCOUNTS) -> list[dict]:
    rows: list[dict] = []

    for i in range(n):
        account_id   = f"acc_{uuid.uuid4().hex[:12]}"
        company_size = weighted_choice(COMPANY_SIZES, SIZE_WEIGHTS)
        industry     = weighted_choice(INDUSTRIES, INDUSTRY_WEIGHTS)
        region       = weighted_choice(REGIONS, REGION_WEIGHTS)
        channel      = weighted_choice(ACQUISITION_CHANNELS, CHANNEL_WEIGHTS)
        plan_id      = _pick_plan(company_size)
        plan         = PLAN_MAP[plan_id]

        emp_lo, emp_hi = EMPLOYEE_RANGES[company_size]
        employee_count = random.randint(emp_lo, emp_hi)

        # Seats: between plan min and a fraction of employees
        seat_lo = plan["min_seats"]
        seat_hi = min(plan["max_seats"], max(seat_lo + 1, employee_count // 4))
        seats   = random.randint(seat_lo, seat_hi)

        created_at = _random_account_created_at(i, n)

        # Health score baseline — used by downstream generators
        h_lo, h_hi = HEALTH_BASELINE_BY_PLAN[plan_id]
        health_score_baseline = round(random.uniform(h_lo, h_hi), 1)

        # Churn propensity — inversely correlated with health
        churn_propensity = round(max(0.005, min(0.15, (100 - health_score_baseline) / 800)), 4)

        rows.append({
            "account_id":             account_id,
            "company_name":           fake.company(),
            "industry":               industry,
            "region":                 region,
            "country":                fake.country(),
            "company_size":           company_size,
            "employee_count":         employee_count,
            "acquisition_channel":    channel,
            "initial_plan_id":        plan_id,
            "seats_purchased":        seats,
            "health_score_baseline":  health_score_baseline,
            "churn_propensity":       churn_propensity,
            "created_at":             created_at.isoformat(),
            "updated_at":             created_at.isoformat(),
            "is_deleted":             False,
            "account_owner":          fake.name(),
            "csm_name":               fake.name() if plan["tier"] >= 3 else None,
            "website":                fake.url(),
            "timezone":               fake.timezone(),
        })

    # Sort by created_at for natural ordering
    rows.sort(key=lambda r: r["created_at"])
    print(f"[accounts] Generated {len(rows)} accounts")
    return rows


def save_accounts(rows: list[dict], out_dir: Path = OUTPUT_DIR) -> Path:
    path = out_dir / "accounts.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[accounts] Wrote {len(rows)} rows → {path}")
    return path


if __name__ == "__main__":
    rows = generate_accounts()
    save_accounts(rows)
