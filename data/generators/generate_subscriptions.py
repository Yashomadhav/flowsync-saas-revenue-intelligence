"""
FlowSync - Subscriptions Generator
Outputs: data/seeds/subscriptions.csv -> raw_subscriptions (bronze)
Simulates full lifecycle: new, expansion, contraction, churn, reactivation.
Annual plans normalized to monthly MRR (annual_price / 12).
"""

from __future__ import annotations
import csv
import uuid
import random
from datetime import date
from pathlib import Path

from config import (
    RANDOM_SEED, OUTPUT_DIR, SIM_START_DATE, SIM_END_DATE,
    PLAN_MAP, BILLING_CYCLES,
    MONTHLY_EXPANSION_RATE, MONTHLY_CONTRACTION_RATE, MONTHLY_REACTIVATION_RATE,
    add_months, month_start, clamp,
)

random.seed(RANDOM_SEED)

BILLING_WEIGHTS = [65, 35]

UPGRADE_PATH = {
    "plan_starter": "plan_growth",
    "plan_growth": "plan_pro",
    "plan_pro": "plan_enterprise",
    "plan_enterprise": None,
}
DOWNGRADE_PATH = {
    "plan_starter": None,
    "plan_growth": "plan_starter",
    "plan_pro": "plan_growth",
    "plan_enterprise": "plan_pro",
}


def _mrr(plan_id, billing, seats):
    p = PLAN_MAP[plan_id]
    base = p["annual_price"] / 12 if billing == "annual" else p["monthly_price"]
    if p["seat_based"]:
        base += seats * p["price_per_seat"]
    return round(base, 2)


def _billing():
    return random.choices(BILLING_CYCLES, weights=BILLING_WEIGHTS, k=1)[0]


def _seats(plan_id, acct_seats):
    p = PLAN_MAP[plan_id]
    if not p["seat_based"]:
        return acct_seats
    lo = p["min_seats"]
    hi = min(p["max_seats"], max(lo + 1, acct_seats))
    return random.randint(lo, hi)


def _rec(account_id, plan_id, billing, seats, mrr, status,
         start, end, churned_at, reactivated_at,
         movement_type, prev_plan, prev_mrr, mrr_delta):
    sid = "sub_" + uuid.uuid4().hex[:12]
    s = start.isoformat() if start else None
    e = end.isoformat() if end else None
    ca = churned_at.isoformat() if churned_at else None
    ra = reactivated_at.isoformat() if reactivated_at else None
    rec = dict(
        subscription_id=sid,
        account_id=account_id,
        plan_id=plan_id,
        billing_cycle=billing,
        seats=seats,
        mrr=mrr,
        arr=round(mrr * 12, 2),
        status=status,
        start_date=s,
        end_date=e,
        churned_at=ca,
        reactivated_at=ra,
        movement_type=movement_type,
        prev_plan_id=prev_plan,
        prev_mrr=prev_mrr,
        mrr_delta=round(mrr_delta, 2),
        created_at=s,
    )
    return rec


def generate_subscriptions(accounts):
    rows = []

    for acct in accounts:
        account_id = acct["account_id"]
        plan_id = acct["initial_plan_id"]
        churn_prop = float(acct["churn_propensity"])
        acct_seats = int(acct["seats_purchased"])
        acct_created = date.fromisoformat(acct["created_at"])

        sub_start = max(acct_created, SIM_START_DATE)
        billing = _billing()
        seats = _seats(plan_id, acct_seats)
        mrr = _mrr(plan_id, billing, seats)

        cur_plan = plan_id
        cur_billing = billing
        cur_seats = seats
        cur_mrr = mrr
        cur_start = sub_start
        is_churned = False
        churn_date = None

        cursor = month_start(sub_start)

        while cursor <= SIM_END_DATE:

            if not is_churned:
                eff = clamp(churn_prop * random.uniform(0.5, 1.8), 0.003, 0.18)
                if random.random() < eff:
                    churn_date = cursor.replace(day=random.randint(1, 28))
                    rows.append(_rec(
                        account_id, cur_plan, cur_billing, cur_seats, cur_mrr,
                        "churned", cur_start, churn_date, churn_date, None,
                        "churn", None, None, -cur_mrr,
                    ))
                    is_churned = True
                    cursor = add_months(cursor, 1)
                    continue

            if is_churned:
                months_gone = (cursor.year - churn_date.year) * 12 + (cursor.month - churn_date.month)
                if months_gone >= 1 and random.random() < MONTHLY_REACTIVATION_RATE:
                    np = random.choice([cur_plan, "plan_starter", "plan_growth"])
                    nb = _billing()
                    ns = _seats(np, acct_seats)
                    nm = _mrr(np, nb, ns)
                    rd = cursor.replace(day=random.randint(1, 15))
                    rows.append(_rec(
                        account_id, np, nb, ns, nm,
                        "active", rd, None, None, rd,
                        "reactivation", cur_plan, cur_mrr, nm,
                    ))
                    is_churned = False
                    cur_plan = np
                    cur_billing = nb
                    cur_seats = ns
                    cur_mrr = nm
                    cur_start = rd
                    churn_date = None
                cursor = add_months(cursor, 1)
                continue

            if random.random() < MONTHLY_EXPANSION_RATE:
                up = UPGRADE_PATH.get(cur_plan)
                if up:
                    old_mrr = cur_mrr
                    old_plan = cur_plan
                    cur_plan = up
                    cur_seats = _seats(cur_plan, acct_seats)
                    cur_mrr = _mrr(cur_plan, cur_billing, cur_seats)
                    ev = cursor.replace(day=random.randint(1, 20))
                    rows.append(_rec(
                        account_id, cur_plan, cur_billing, cur_seats, cur_mrr,
                        "active", ev, None, None, None,
                        "expansion", old_plan, old_mrr, cur_mrr - old_mrr,
                    ))
                    cur_start = ev
                else:
                    pcfg = PLAN_MAP[cur_plan]
                    if pcfg["seat_based"] and cur_seats < pcfg["max_seats"]:
                        old_mrr = cur_mrr
                        add_s = random.randint(1, max(1, cur_seats // 5))
                        cur_seats = min(cur_seats + add_s, pcfg["max_seats"])
                        cur_mrr = _mrr(cur_plan, cur_billing, cur_seats)
                        ev = cursor.replace(day=random.randint(1, 20))
                        rows.append(_rec(
                            account_id, cur_plan, cur_billing, cur_seats, cur_mrr,
                            "active", ev, None, None, None,
                            "expansion", cur_plan, old_mrr, cur_mrr - old_mrr,
                        ))
                        cur_start = ev

            elif random.random() < MONTHLY_CONTRACTION_RATE:
                down = DOWNGRADE_PATH.get(cur_plan)
                if down:
                    old_mrr = cur_mrr
                    old_plan = cur_plan
                    cur_plan = down
                    cur_seats = _seats(cur_plan, acct_seats)
                    cur_mrr = _mrr(cur_plan, cur_billing, cur_seats)
                    ev = cursor.replace(day=random.randint(1, 20))
                    rows.append(_rec(
                        account_id, cur_plan, cur_billing, cur_seats, cur_mrr,
                        "active", ev, None, None, None,
                        "contraction", old_plan, old_mrr, cur_mrr - old_mrr,
                    ))
                    cur_start = ev

            cursor = add_months(cursor, 1)

        if not is_churned:
            mt = "new" if cur_start == sub_start else "active"
            md = cur_mrr if cur_start == sub_start else 0
            rows.append(_rec(
                account_id, cur_plan, cur_billing, cur_seats, cur_mrr,
                "active", cur_start, None, None, None,
                mt, None, None, md,
            ))

    rows.sort(key=lambda r: r["start_date"] or "")
    print(f"[subscriptions] Generated {len(rows)} records")
    return rows


def save_subscriptions(rows, out_dir=OUTPUT_DIR):
    path = out_dir / "subscriptions.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[subscriptions] Wrote {len(rows)} rows -> {path}")
    return path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generate_accounts import generate_accounts
    accts = generate_accounts()
    data = generate_subscriptions(accts)
    save_subscriptions(data)
