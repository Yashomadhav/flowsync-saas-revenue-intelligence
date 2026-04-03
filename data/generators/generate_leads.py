"""
FlowSync - Leads / Opportunities Generator
Outputs: data/seeds/leads.csv -> raw_leads (bronze)
Simulates the full sales funnel: lead -> qualified -> trial -> trial_active -> converted/lost
Conversion rates and timing vary by channel and plan.
"""

from __future__ import annotations
import calendar
import csv
import uuid
import random
from datetime import date, timedelta
from pathlib import Path

from config import (
    RANDOM_SEED, OUTPUT_DIR, SIM_START_DATE, SIM_END_DATE,
    TARGET_LEADS, ACQUISITION_CHANNELS, INDUSTRIES, REGIONS,
    COMPANY_SIZES, PLAN_IDS, PLAN_MAP, LEAD_STAGES,
    LEAD_STAGE_CONVERSION, add_months, month_start, clamp,
)

random.seed(RANDOM_SEED + 4)

CHANNEL_WEIGHTS = [18, 15, 14, 12, 12, 12, 10, 7]

CHANNEL_PLAN_AFFINITY = {
    "Organic Search":       {"plan_starter": 0.45, "plan_growth": 0.35, "plan_pro": 0.15, "plan_enterprise": 0.05},
    "Paid Search":          {"plan_starter": 0.40, "plan_growth": 0.35, "plan_pro": 0.18, "plan_enterprise": 0.07},
    "Referral":             {"plan_starter": 0.20, "plan_growth": 0.35, "plan_pro": 0.30, "plan_enterprise": 0.15},
    "Partner":              {"plan_starter": 0.15, "plan_growth": 0.30, "plan_pro": 0.35, "plan_enterprise": 0.20},
    "Outbound Sales":       {"plan_starter": 0.10, "plan_growth": 0.25, "plan_pro": 0.35, "plan_enterprise": 0.30},
    "Product-Led Growth":   {"plan_starter": 0.50, "plan_growth": 0.35, "plan_pro": 0.12, "plan_enterprise": 0.03},
    "Content Marketing":    {"plan_starter": 0.40, "plan_growth": 0.38, "plan_pro": 0.17, "plan_enterprise": 0.05},
    "Event / Conference":   {"plan_starter": 0.10, "plan_growth": 0.25, "plan_pro": 0.35, "plan_enterprise": 0.30},
}

CHANNEL_CONVERSION_MODIFIER = {
    "Organic Search":       1.0,
    "Paid Search":          0.85,
    "Referral":             1.25,
    "Partner":              1.15,
    "Outbound Sales":       0.90,
    "Product-Led Growth":   1.10,
    "Content Marketing":    0.95,
    "Event / Conference":   1.20,
}

STAGE_DAYS = {
    "lead_to_qualified":    (1, 14),
    "qualified_to_trial":   (1, 21),
    "trial_to_active":      (0, 3),
    "active_to_converted":  (7, 30),
    "active_to_lost":       (7, 45),
}

SIZE_WEIGHTS = [50, 35, 15]


def _pick_plan(channel):
    affinity = CHANNEL_PLAN_AFFINITY.get(channel, {p: 0.25 for p in PLAN_IDS})
    plans = list(affinity.keys())
    weights = list(affinity.values())
    return random.choices(plans, weights=weights, k=1)[0]


def _advance_stage(current_stage, channel, plan_id):
    base_rate = LEAD_STAGE_CONVERSION.get(current_stage, 0.0)
    modifier = CHANNEL_CONVERSION_MODIFIER.get(channel, 1.0)
    plan_tier = PLAN_MAP[plan_id]["tier"]
    tier_mod = 1.0 + (plan_tier - 1) * 0.05
    rate = clamp(base_rate * modifier * tier_mod, 0.0, 0.98)
    return random.random() < rate


def _days_in_stage(stage_key):
    lo, hi = STAGE_DAYS.get(stage_key, (1, 7))
    return random.randint(lo, hi)


def _trial_engagement_score(plan_id, converted):
    plan_tier = PLAN_MAP[plan_id]["tier"]
    if converted:
        base = random.uniform(0.55, 1.0)
    else:
        base = random.uniform(0.05, 0.55)
    return round(clamp(base * (0.8 + plan_tier * 0.05), 0.0, 1.0), 3)


def generate_leads(accounts=None):
    rows = []
    months_range = []
    cursor = month_start(SIM_START_DATE)
    while cursor <= SIM_END_DATE:
        months_range.append(cursor)
        cursor = add_months(cursor, 1)

    leads_per_month = TARGET_LEADS // len(months_range)
    remainder = TARGET_LEADS - leads_per_month * len(months_range)

    converted_account_ids = set()
    if accounts:
        converted_account_ids = {a["account_id"] for a in accounts}

    for i, month in enumerate(months_range):
        n = leads_per_month + (1 if i < remainder else 0)
        last_day = calendar.monthrange(month.year, month.month)[1]

        for _ in range(n):
            lead_id = "lead_" + uuid.uuid4().hex[:12]
            channel = random.choices(ACQUISITION_CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
            industry = random.choice(INDUSTRIES)
            region = random.choice(REGIONS)
            company_size = random.choices(COMPANY_SIZES, weights=SIZE_WEIGHTS, k=1)[0]
            plan_id = _pick_plan(channel)

            lead_date = date(month.year, month.month, random.randint(1, last_day))
            current_date = lead_date
            final_stage = "lead"
            qualified_date = None
            trial_start_date = None
            trial_active_date = None
            converted_date = None
            lost_date = None
            lost_stage = None
            trial_engagement = None
            days_to_convert = None
            account_id = None

            if _advance_stage("lead", channel, plan_id):
                final_stage = "qualified"
                current_date = current_date + timedelta(days=_days_in_stage("lead_to_qualified"))
                qualified_date = current_date
                if current_date > SIM_END_DATE:
                    final_stage = "lead"
                    qualified_date = None
                elif _advance_stage("qualified", channel, plan_id):
                    final_stage = "trial"
                    current_date = current_date + timedelta(days=_days_in_stage("qualified_to_trial"))
                    trial_start_date = current_date
                    if current_date > SIM_END_DATE:
                        final_stage = "qualified"
                        trial_start_date = None
                    elif _advance_stage("trial", channel, plan_id):
                        final_stage = "trial_active"
                        current_date = current_date + timedelta(days=_days_in_stage("trial_to_active"))
                        trial_active_date = current_date
                        if current_date > SIM_END_DATE:
                            final_stage = "trial"
                            trial_active_date = None
                        elif _advance_stage("trial_active", channel, plan_id):
                            final_stage = "converted"
                            current_date = current_date + timedelta(days=_days_in_stage("active_to_converted"))
                            if current_date <= SIM_END_DATE:
                                converted_date = current_date
                                days_to_convert = (converted_date - lead_date).days
                                trial_engagement = _trial_engagement_score(plan_id, True)
                                account_id = "acc_" + uuid.uuid4().hex[:12]
                            else:
                                final_stage = "trial_active"
                        else:
                            final_stage = "lost"
                            lost_stage = "trial_active"
                            current_date = current_date + timedelta(days=_days_in_stage("active_to_lost"))
                            if current_date <= SIM_END_DATE:
                                lost_date = current_date
                            trial_engagement = _trial_engagement_score(plan_id, False)
                    else:
                        final_stage = "lost"
                        lost_stage = "trial"
                        lost_date = current_date + timedelta(days=random.randint(3, 14))
                        if lost_date > SIM_END_DATE:
                            lost_date = None
                else:
                    final_stage = "lost"
                    lost_stage = "qualified"
                    lost_date = current_date + timedelta(days=random.randint(7, 30))
                    if lost_date > SIM_END_DATE:
                        lost_date = None
            else:
                final_stage = "lost"
                lost_stage = "lead"
                lost_date = current_date + timedelta(days=random.randint(1, 7))
                if lost_date > SIM_END_DATE:
                    lost_date = None

            mrr_at_conversion = None
            if final_stage == "converted" and converted_date:
                plan = PLAN_MAP[plan_id]
                if plan["seat_based"]:
                    seats = random.randint(plan["min_seats"], min(plan["min_seats"] * 3, plan["max_seats"]))
                    mrr_at_conversion = plan["monthly_price"] + seats * plan["price_per_seat"]
                else:
                    mrr_at_conversion = plan["monthly_price"]

            rows.append(dict(
                lead_id=lead_id,
                account_id=account_id,
                channel=channel,
                industry=industry,
                region=region,
                company_size=company_size,
                plan_id=plan_id,
                lead_date=lead_date.isoformat(),
                lead_month=month.isoformat(),
                qualified_date=qualified_date.isoformat() if qualified_date else None,
                trial_start_date=trial_start_date.isoformat() if trial_start_date else None,
                trial_active_date=trial_active_date.isoformat() if trial_active_date else None,
                converted_date=converted_date.isoformat() if converted_date else None,
                lost_date=lost_date.isoformat() if lost_date else None,
                final_stage=final_stage,
                lost_stage=lost_stage,
                days_to_convert=days_to_convert,
                trial_engagement_score=trial_engagement,
                mrr_at_conversion=round(mrr_at_conversion, 2) if mrr_at_conversion else None,
                is_converted=final_stage == "converted" and converted_date is not None,
                is_lost=final_stage == "lost",
            ))

    rows.sort(key=lambda r: r["lead_date"])
    print(f"[leads] Generated {len(rows)} lead records")
    return rows


def save_leads(rows, out_dir=OUTPUT_DIR):
    path = out_dir / "leads.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        print(f"[leads] Wrote {len(rows)} rows -> {path}")
    return path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    data = generate_leads()
    save_leads(data)
