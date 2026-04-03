"""
FlowSync - Usage Events Generator
Outputs: data/seeds/usage_events.csv -> raw_usage_events (bronze)
Generates product usage events per account per month.
Usage frequency correlates with health score; drops 30-60% before churn.
Capped at TARGET_USAGE_EVENTS total rows for performance.
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
    PLAN_MAP, FEATURE_IDS, TARGET_USAGE_EVENTS,
    add_months, month_start, clamp,
)

random.seed(RANDOM_SEED)

EVENT_TYPES = [
    "login", "workflow_run", "report_view", "api_call",
    "integration_sync", "dashboard_view", "export", "invite_user",
    "feature_enable", "support_chat", "settings_update", "data_import",
]
EVENT_WEIGHTS = [20, 18, 12, 10, 10, 10, 7, 4, 4, 2, 2, 1]

# Reduced base events per user per month (was 15-200, now 3-20)
# This keeps total events near TARGET_USAGE_EVENTS for 300 accounts × 24 months
BASE_EVENTS_PER_USER = {
    1: (3, 8),
    2: (5, 12),
    3: (8, 18),
    4: (10, 20),
}

FEATURES_BY_TIER = {
    1: ["feat_core_workflows", "feat_basic_analytics", "feat_email_support"],
    2: ["feat_core_workflows", "feat_advanced_analytics", "feat_integrations", "feat_priority_support"],
    3: ["feat_core_workflows", "feat_advanced_analytics", "feat_integrations",
        "feat_api_access", "feat_custom_workflows", "feat_sso"],
    4: ["feat_core_workflows", "feat_advanced_analytics", "feat_integrations",
        "feat_api_access", "feat_custom_workflows", "feat_sso",
        "feat_dedicated_csm", "feat_custom_reporting", "feat_audit_logs"],
}


def _active_users(seats, health_score):
    utilization = clamp(health_score / 100 * random.uniform(0.6, 1.1), 0.15, 1.0)
    return max(1, int(seats * utilization))


def _event_count(plan_tier, active_users, health_score, months_to_churn):
    lo, hi = BASE_EVENTS_PER_USER[plan_tier]
    base = random.randint(lo, hi) * max(1, min(active_users, 5))  # cap user multiplier at 5
    health_mod = clamp(health_score / 75, 0.3, 1.4)
    base = int(base * health_mod)
    if months_to_churn == 0:
        base = int(base * random.uniform(0.3, 0.55))
    elif months_to_churn == 1:
        base = int(base * random.uniform(0.55, 0.75))
    return max(1, base)


def _find_active_sub(acct_subs, cursor):
    for s in acct_subs:
        s_start_str = s.get("start_date")
        s_end_str = s.get("end_date")
        if not s_start_str:
            continue
        s_start = date.fromisoformat(s_start_str)
        s_end = date.fromisoformat(s_end_str) if s_end_str else SIM_END_DATE
        if s_start <= cursor <= s_end:
            return s
    return None


def generate_usage_events(accounts, subscriptions):
    sub_by_account: dict[str, list] = {}
    for s in subscriptions:
        aid = s["account_id"]
        if aid not in sub_by_account:
            sub_by_account[aid] = []
        sub_by_account[aid].append(s)

    for aid in sub_by_account:
        sub_by_account[aid].sort(key=lambda x: x.get("start_date") or "")

    rows: list[dict] = []
    cap = TARGET_USAGE_EVENTS

    for acct in accounts:
        if len(rows) >= cap:
            break

        account_id = acct["account_id"]
        health_base = float(acct["health_score_baseline"])
        acct_created = date.fromisoformat(acct["created_at"])

        acct_subs = sub_by_account.get(account_id, [])
        if not acct_subs:
            continue

        churned_subs = [s for s in acct_subs if s.get("churned_at")]
        churn_date = date.fromisoformat(churned_subs[0]["churned_at"]) if churned_subs else None

        cursor = month_start(max(acct_created, SIM_START_DATE))

        while cursor <= SIM_END_DATE:
            if len(rows) >= cap:
                break
            if churn_date and cursor > churn_date:
                break

            active_sub = _find_active_sub(acct_subs, cursor)
            if not active_sub:
                cursor = add_months(cursor, 1)
                continue

            plan_id = active_sub["plan_id"]
            plan = PLAN_MAP[plan_id]
            plan_tier = plan["tier"]
            seats = int(active_sub["seats"])

            health_score = clamp(health_base + random.uniform(-3, 3), 10, 100)

            months_to_churn = None
            if churn_date:
                diff = (churn_date.year - cursor.year) * 12 + (churn_date.month - cursor.month)
                months_to_churn = diff if diff >= 0 else None

            active_users = _active_users(seats, health_score)
            n_events = _event_count(plan_tier, active_users, health_score, months_to_churn)
            # Don't exceed cap
            n_events = min(n_events, cap - len(rows))
            if n_events <= 0:
                break

            available_features = FEATURES_BY_TIER.get(plan_tier, FEATURES_BY_TIER[1])
            last_day = calendar.monthrange(cursor.year, cursor.month)[1]

            # Batch ALL random calls for this month — much faster than per-event calls
            event_types_b = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=n_events)
            feature_ids_b = random.choices(available_features, k=n_events)
            user_nums_b = random.choices(range(1, max(2, active_users + 1)), k=n_events)
            durations_b = random.choices(range(2, 91), k=n_events)
            raw_days_b = random.choices(range(1, last_day + 1), k=n_events)

            sub_id = active_sub["subscription_id"]
            seat_util = round(active_users / max(1, seats) * 100, 1)
            health_rounded = round(health_score, 1)
            cursor_iso = cursor.isoformat()
            yr, mo = cursor.year, cursor.month

            for i in range(n_events):
                d = date(yr, mo, raw_days_b[i])
                # Bias toward weekdays
                if d.weekday() >= 5 and random.random() < 0.7:
                    shift = d.weekday() - 4
                    d = d - timedelta(days=shift)
                user_id = f"usr_{account_id[-8:]}_{user_nums_b[i]:03d}"
                rows.append({
                    "event_id": "evt_" + uuid.uuid4().hex[:12],
                    "account_id": account_id,
                    "subscription_id": sub_id,
                    "user_id": user_id,
                    "plan_id": plan_id,
                    "event_type": event_types_b[i],
                    "feature_id": feature_ids_b[i],
                    "event_date": d.isoformat(),
                    "event_month": cursor_iso,
                    "active_users_this_month": active_users,
                    "seats": seats,
                    "seat_utilization_pct": seat_util,
                    "health_score_at_event": health_rounded,
                    "session_duration_minutes": durations_b[i],
                    "is_weekend": d.weekday() >= 5,
                })

            cursor = add_months(cursor, 1)

    rows.sort(key=lambda r: r["event_date"])
    print(f"[usage_events] Generated {len(rows)} event records")
    return rows


def save_usage_events(rows, out_dir=OUTPUT_DIR):
    path = out_dir / "usage_events.csv"
    if not rows:
        print("[usage_events] No rows to write")
        return path
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[usage_events] Wrote {len(rows)} rows -> {path}")
    return path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generate_accounts import generate_accounts
    from generate_subscriptions import generate_subscriptions
    accts = generate_accounts()
    subs = generate_subscriptions(accts)
    data = generate_usage_events(accts, subs)
    save_usage_events(data)
