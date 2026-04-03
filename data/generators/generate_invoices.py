"""
FlowSync - Invoices Generator
Outputs: data/seeds/invoices.csv -> raw_invoices (bronze)

Generates one invoice per subscription per billing period.
- Monthly subs: one invoice per month
- Annual subs: one invoice per year (full annual amount)
- Realistic payment failure rate (~5-8%)
- Failed payments may retry and succeed or remain failed
- Includes dunning attempts
"""

from __future__ import annotations
import csv
import uuid
import random
from datetime import date, timedelta
from pathlib import Path

from config import (
    RANDOM_SEED, OUTPUT_DIR, SIM_START_DATE, SIM_END_DATE,
    PLAN_MAP, add_months, month_start,
)

random.seed(RANDOM_SEED)

PAYMENT_METHODS = ["credit_card", "ach", "wire", "paypal"]
PAYMENT_METHOD_WEIGHTS = [55, 25, 15, 5]

FAILURE_REASONS = [
    "insufficient_funds",
    "card_expired",
    "card_declined",
    "bank_error",
    "dispute",
    "fraud_block",
]

BASE_FAILURE_RATE = 0.055   # 5.5% base failure rate
RETRY_SUCCESS_RATE = 0.65   # 65% of failed payments succeed on retry


def _invoice_amount(plan_id, billing_cycle, seats):
    p = PLAN_MAP[plan_id]
    if billing_cycle == "annual":
        base = p["annual_price"]
    else:
        base = p["monthly_price"]
    if p["seat_based"]:
        per_seat = p["price_per_seat"]
        if billing_cycle == "annual":
            base += seats * per_seat * 12
        else:
            base += seats * per_seat
    return round(base, 2)


def generate_invoices(subscriptions):
    rows = []

    for sub in subscriptions:
        account_id = sub["account_id"]
        plan_id = sub["plan_id"]
        billing = sub["billing_cycle"]
        seats = int(sub["seats"])
        status = sub["status"]
        start_str = sub["start_date"]
        end_str = sub["end_date"]
        churned_str = sub["churned_at"]

        if not start_str:
            continue

        sub_start = date.fromisoformat(start_str)
        sub_end = date.fromisoformat(end_str) if end_str else SIM_END_DATE
        churn_date = date.fromisoformat(churned_str) if churned_str else None

        amount = _invoice_amount(plan_id, billing, seats)
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS, k=1)[0]

        # Accounts with higher churn propensity have higher failure rates
        acct_failure_rate = BASE_FAILURE_RATE * random.uniform(0.5, 2.5)
        acct_failure_rate = min(acct_failure_rate, 0.20)

        if billing == "annual":
            # One invoice per year
            cursor = month_start(sub_start)
            while cursor <= min(sub_end, SIM_END_DATE):
                invoice_date = cursor
                due_date = invoice_date + timedelta(days=30)
                period_end = add_months(cursor, 12) - timedelta(days=1)

                is_failed = random.random() < acct_failure_rate
                if is_failed:
                    retry_success = random.random() < RETRY_SUCCESS_RATE
                    retry_date = invoice_date + timedelta(days=random.randint(3, 7))
                    inv_status = "paid" if retry_success else "failed"
                    paid_at = retry_date.isoformat() if retry_success else None
                    failure_reason = random.choice(FAILURE_REASONS)
                    dunning_count = random.randint(1, 3) if not retry_success else 1
                else:
                    inv_status = "paid"
                    paid_at = (invoice_date + timedelta(days=random.randint(0, 5))).isoformat()
                    failure_reason = None
                    dunning_count = 0

                rows.append(dict(
                    invoice_id="inv_" + uuid.uuid4().hex[:12],
                    account_id=account_id,
                    subscription_id=sub["subscription_id"],
                    plan_id=plan_id,
                    billing_cycle=billing,
                    invoice_date=invoice_date.isoformat(),
                    due_date=due_date.isoformat(),
                    period_start=cursor.isoformat(),
                    period_end=period_end.isoformat(),
                    amount=amount,
                    mrr_equivalent=round(amount / 12, 2),
                    currency="USD",
                    status=inv_status,
                    payment_method=payment_method,
                    paid_at=paid_at,
                    failure_reason=failure_reason,
                    dunning_count=dunning_count,
                    is_failed=is_failed and inv_status == "failed",
                    seats=seats,
                ))
                cursor = add_months(cursor, 12)

        else:
            # Monthly: one invoice per month
            cursor = month_start(sub_start)
            while cursor <= min(sub_end, SIM_END_DATE):
                if churn_date and cursor > churn_date:
                    break

                invoice_date = cursor
                due_date = invoice_date + timedelta(days=15)
                period_end = add_months(cursor, 1) - timedelta(days=1)

                is_failed = random.random() < acct_failure_rate
                if is_failed:
                    retry_success = random.random() < RETRY_SUCCESS_RATE
                    retry_date = invoice_date + timedelta(days=random.randint(2, 5))
                    inv_status = "paid" if retry_success else "failed"
                    paid_at = retry_date.isoformat() if retry_success else None
                    failure_reason = random.choice(FAILURE_REASONS)
                    dunning_count = random.randint(1, 3) if not retry_success else 1
                else:
                    inv_status = "paid"
                    paid_at = (invoice_date + timedelta(days=random.randint(0, 3))).isoformat()
                    failure_reason = None
                    dunning_count = 0

                rows.append(dict(
                    invoice_id="inv_" + uuid.uuid4().hex[:12],
                    account_id=account_id,
                    subscription_id=sub["subscription_id"],
                    plan_id=plan_id,
                    billing_cycle=billing,
                    invoice_date=invoice_date.isoformat(),
                    due_date=due_date.isoformat(),
                    period_start=cursor.isoformat(),
                    period_end=period_end.isoformat(),
                    amount=amount,
                    mrr_equivalent=amount,
                    currency="USD",
                    status=inv_status,
                    payment_method=payment_method,
                    paid_at=paid_at,
                    failure_reason=failure_reason,
                    dunning_count=dunning_count,
                    is_failed=is_failed and inv_status == "failed",
                    seats=seats,
                ))
                cursor = add_months(cursor, 1)

    rows.sort(key=lambda r: r["invoice_date"])
    print(f"[invoices] Generated {len(rows)} invoice records")
    return rows


def save_invoices(rows, out_dir=OUTPUT_DIR):
    path = out_dir / "invoices.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[invoices] Wrote {len(rows)} rows -> {path}")
    return path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generate_accounts import generate_accounts
    from generate_subscriptions import generate_subscriptions
    accts = generate_accounts()
    subs = generate_subscriptions(accts)
    data = generate_invoices(subs)
    save_invoices(data)
