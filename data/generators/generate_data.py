"""
FlowSync SaaS Revenue Intelligence — Synthetic Data Generator
=============================================================
Generates realistic SaaS data for 200 accounts over 24 months.
Produces: accounts, subscriptions, invoices, usage_events, tickets, leads

Usage:
    python data/generators/generate_data.py
    python data/generators/generate_data.py --accounts 500 --months 36
"""

import random
import uuid
import json
import argparse
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import sys
import os

# Try to import optional dependencies
try:
    from faker import Faker
    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False
    print("Warning: faker not installed. Using built-in data.")

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

RANDOM_SEED = int(os.getenv("SEED_RANDOM_SEED", "42"))
NUM_ACCOUNTS = int(os.getenv("SEED_ACCOUNTS", "200"))
NUM_MONTHS = int(os.getenv("SEED_MONTHS", "24"))

random.seed(RANDOM_SEED)
if HAS_FAKER:
    fake = Faker()
    Faker.seed(RANDOM_SEED)

# Reference data
INDUSTRIES = [
    "Technology", "Financial Services", "Healthcare", "Retail & E-commerce",
    "Manufacturing", "Professional Services", "Education", "Media & Entertainment",
    "Real Estate", "Logistics & Supply Chain", "Energy", "Non-Profit"
]

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]

COUNTRIES_BY_REGION = {
    "North America": ["United States", "Canada", "Mexico"],
    "Europe": ["United Kingdom", "Germany", "France", "Netherlands", "Sweden", "Spain"],
    "Asia Pacific": ["Australia", "Japan", "Singapore", "India", "South Korea"],
    "Latin America": ["Brazil", "Argentina", "Colombia", "Chile"],
    "Middle East & Africa": ["UAE", "South Africa", "Israel", "Saudi Arabia"]
}

COMPANY_SIZES = ["SMB", "Mid-Market", "Enterprise"]

COMPANY_SIZE_EMPLOYEE_RANGES = {
    "SMB": (5, 50),
    "Mid-Market": (51, 500),
    "Enterprise": (501, 10000)
}

ACQUISITION_CHANNELS = [
    "Organic Search", "Paid Search", "Content/Blog", "Referral",
    "Partner", "Direct/Outbound", "Product-Led"
]

CHANNEL_WEIGHTS = [0.20, 0.18, 0.15, 0.15, 0.12, 0.12, 0.08]

PLANS = [
    {"plan_id": "starter",    "plan_name": "Starter",    "mrr": 99,   "seats": 5,   "weight": 0.35},
    {"plan_id": "growth",     "plan_name": "Growth",     "mrr": 299,  "seats": 25,  "weight": 0.30},
    {"plan_id": "business",   "plan_name": "Business",   "mrr": 799,  "seats": 100, "weight": 0.22},
    {"plan_id": "enterprise", "plan_name": "Enterprise", "mrr": 2499, "seats": 999, "weight": 0.13},
]

PLAN_IDS = [p["plan_id"] for p in PLANS]
PLAN_WEIGHTS = [p["weight"] for p in PLANS]

FEATURES = [
    "workflow_builder", "automation_rules", "integrations", "analytics_dashboard",
    "team_collaboration", "api_access", "custom_reports", "approval_flows",
    "data_export", "webhooks", "sso_login", "audit_logs", "bulk_operations",
    "template_library", "mobile_app"
]

TICKET_CATEGORIES = ["Billing", "Technical", "Feature Request", "Onboarding", "Integration", "Performance"]
TICKET_PRIORITIES = ["low", "medium", "high", "critical"]
TICKET_PRIORITY_WEIGHTS = [0.35, 0.40, 0.18, 0.07]

LEAD_SOURCES = ["Website Form", "Demo Request", "Webinar", "Trade Show", "Cold Outreach", "Referral Link"]

# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────

def gen_id() -> str:
    return str(uuid.uuid4())

def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))

def rand_company_name() -> str:
    if HAS_FAKER:
        return fake.company()
    prefixes = ["Acme", "Apex", "Nova", "Zenith", "Vertex", "Nexus", "Orbit", "Pulse", "Flux", "Core"]
    suffixes = ["Corp", "Inc", "Solutions", "Technologies", "Systems", "Group", "Labs", "Works", "Co", "Ltd"]
    return f"{random.choice(prefixes)} {random.choice(suffixes)}"

def rand_person_name() -> str:
    if HAS_FAKER:
        return fake.name()
    first = ["James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Ashley", "John", "Amanda"]
    last = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Taylor"]
    return f"{random.choice(first)} {random.choice(last)}"

def rand_email(name: str, company: str) -> str:
    name_part = name.lower().replace(" ", ".").replace("'", "")
    company_part = company.lower().replace(" ", "").replace(",", "").replace(".", "")[:12]
    domains = ["com", "io", "co", "net", "org"]
    return f"{name_part}@{company_part}.{random.choice(domains)}"

def rand_website(company: str) -> str:
    company_part = company.lower().replace(" ", "").replace(",", "").replace(".", "")[:15]
    return f"https://www.{company_part}.com"

def get_plan(plan_id: str) -> Dict:
    return next(p for p in PLANS if p["plan_id"] == plan_id)

def months_between(d1: date, d2: date) -> int:
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)

def first_of_month(d: date) -> date:
    return d.replace(day=1)

def add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    return d.replace(year=year, month=month, day=1)

# ─────────────────────────────────────────────────────────────────────────────
# Account Generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_accounts(num_accounts: int, start_date: date) -> List[Dict]:
    accounts = []
    for _ in range(num_accounts):
        region = random.choice(REGIONS)
        country = random.choice(COUNTRIES_BY_REGION[region])
        size = random.choices(COMPANY_SIZES, weights=[0.45, 0.35, 0.20])[0]
        emp_min, emp_max = COMPANY_SIZE_EMPLOYEE_RANGES[size]
        company_name = rand_company_name()
        created_at = rand_date(start_date - timedelta(days=365), start_date + timedelta(days=NUM_MONTHS * 30 - 60))

        accounts.append({
            "_id": gen_id(),
            "account_id": gen_id(),
            "company_name": company_name,
            "industry": random.choice(INDUSTRIES),
            "region": region,
            "country": country,
            "company_size": size,
            "employee_count": str(random.randint(emp_min, emp_max)),
            "founded_year": str(random.randint(1990, 2020)),
            "website": rand_website(company_name),
            "acquisition_channel": random.choices(ACQUISITION_CHANNELS, weights=CHANNEL_WEIGHTS)[0],
            "created_at": created_at.isoformat(),
            "updated_at": (created_at + timedelta(days=random.randint(1, 30))).isoformat(),
        })
    return accounts

# ─────────────────────────────────────────────────────────────────────────────
# Subscription Generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_subscriptions(accounts: List[Dict], end_date: date) -> List[Dict]:
    subscriptions = []
    for account in accounts:
        account_created = date.fromisoformat(account["created_at"])
        plan = random.choices(PLANS, weights=PLAN_WEIGHTS)[0]

        # Determine if trial
        has_trial = random.random() < 0.65
        trial_start = account_created if has_trial else None
        trial_end = (trial_start + timedelta(days=random.randint(7, 30))) if has_trial else None

        # Subscription start (after trial or at account creation)
        sub_start = trial_end if trial_end else account_created
        if sub_start > end_date:
            sub_start = end_date - timedelta(days=30)

        # Determine churn
        churn_probability = {
            "starter": 0.25,
            "growth": 0.18,
            "business": 0.12,
            "enterprise": 0.06
        }[plan["plan_id"]]

        is_churned = random.random() < churn_probability
        cancelled_at = None
        sub_end = None
        status = "active"

        if is_churned:
            months_active = random.randint(2, min(18, NUM_MONTHS))
            cancel_date = sub_start + timedelta(days=months_active * 30)
            if cancel_date < end_date:
                cancelled_at = cancel_date.isoformat()
                sub_end = cancel_date.isoformat()
                status = "cancelled"

        # Seats
        seats_licensed = plan["seats"]
        if plan["plan_id"] == "enterprise":
            seats_licensed = random.randint(100, 500)
        seat_utilization = random.uniform(0.15, 0.95)
        seats_used = max(1, int(seats_licensed * seat_utilization))

        # MRR with some variance
        mrr_variance = random.uniform(0.9, 1.1)
        mrr = round(plan["mrr"] * mrr_variance, 2)
        if plan["plan_id"] == "enterprise":
            mrr = round(random.uniform(1500, 8000), 2)

        billing_cycle = random.choices(["monthly", "annual"], weights=[0.45, 0.55])[0]
        if billing_cycle == "annual":
            mrr = round(mrr * 0.85, 2)  # Annual discount

        subscriptions.append({
            "_id": gen_id(),
            "subscription_id": gen_id(),
            "account_id": account["account_id"],
            "plan_id": plan["plan_id"],
            "plan_name": plan["plan_name"],
            "status": status,
            "mrr_amount": str(mrr),
            "arr_amount": str(round(mrr * 12, 2)),
            "billing_cycle": billing_cycle,
            "seats_licensed": str(seats_licensed),
            "seats_used": str(seats_used),
            "trial_start_date": trial_start.isoformat() if trial_start else "",
            "trial_end_date": trial_end.isoformat() if trial_end else "",
            "start_date": sub_start.isoformat(),
            "end_date": sub_end or "",
            "cancelled_at": cancelled_at or "",
            "created_at": account_created.isoformat(),
            "updated_at": (sub_start + timedelta(days=random.randint(1, 10))).isoformat(),
        })

    return subscriptions

# ─────────────────────────────────────────────────────────────────────────────
# Invoice Generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_invoices(subscriptions: List[Dict], end_date: date) -> List[Dict]:
    invoices = []
    for sub in subscriptions:
        if not sub["start_date"]:
            continue
        sub_start = date.fromisoformat(sub["start_date"])
        sub_end_str = sub["end_date"]
        sub_end = date.fromisoformat(sub_end_str) if sub_end_str else end_date

        billing_cycle = sub["billing_cycle"]
        mrr = float(sub["mrr_amount"])
        invoice_amount = mrr if billing_cycle == "monthly" else mrr * 12
        interval_months = 1 if billing_cycle == "monthly" else 12

        current = sub_start
        while current < sub_end and current < end_date:
            invoice_date = current
            due_date = invoice_date + timedelta(days=30)

            # Payment outcome
            fail_prob = 0.04  # 4% failure rate
            is_failed = random.random() < fail_prob
            is_pending = current > end_date - timedelta(days=30)

            if is_pending:
                status = "pending"
                paid_date = ""
                failed_date = ""
                failure_reason = ""
            elif is_failed:
                status = "failed"
                paid_date = ""
                failed_date = (invoice_date + timedelta(days=random.randint(1, 5))).isoformat()
                failure_reason = random.choice([
                    "insufficient_funds", "card_expired", "card_declined",
                    "bank_declined", "do_not_honor"
                ])
            else:
                status = "paid"
                paid_date = (invoice_date + timedelta(days=random.randint(0, 5))).isoformat()
                failed_date = ""
                failure_reason = ""

            invoices.append({
                "_id": gen_id(),
                "invoice_id": gen_id(),
                "account_id": sub["account_id"],
                "subscription_id": sub["subscription_id"],
                "amount": str(round(invoice_amount, 2)),
                "currency": "USD",
                "status": status,
                "due_date": due_date.isoformat(),
                "paid_date": paid_date,
                "failed_date": failed_date,
                "failure_reason": failure_reason,
                "invoice_date": invoice_date.isoformat(),
                "created_at": invoice_date.isoformat(),
            })

            current = add_months(current, interval_months)

    return invoices

# ─────────────────────────────────────────────────────────────────────────────
# Usage Events Generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_usage_events(accounts: List[Dict], subscriptions: List[Dict], end_date: date) -> List[Dict]:
    events = []
    sub_by_account = {s["account_id"]: s for s in subscriptions}

    for account in accounts:
        sub = sub_by_account.get(account["account_id"])
        if not sub:
            continue

        sub_start = date.fromisoformat(sub["start_date"])
        sub_end_str = sub["end_date"]
        sub_end = date.fromisoformat(sub_end_str) if sub_end_str else end_date

        seats_used = int(sub["seats_used"])
        plan_id = sub["plan_id"]

        # Usage intensity by plan
        base_sessions_per_user_per_month = {
            "starter": random.randint(8, 20),
            "growth": random.randint(15, 35),
            "business": random.randint(20, 50),
            "enterprise": random.randint(30, 80),
        }[plan_id]

        # Feature adoption (more features for higher plans)
        num_features = {
            "starter": random.randint(2, 5),
            "growth": random.randint(4, 8),
            "business": random.randint(6, 12),
            "enterprise": random.randint(8, 15),
        }[plan_id]
        account_features = random.sample(FEATURES, min(num_features, len(FEATURES)))

        # Generate user IDs
        user_ids = [gen_id() for _ in range(seats_used)]

        # Generate events month by month
        current_month = first_of_month(sub_start)
        while current_month < sub_end and current_month < end_date:
            # Usage decay for churned accounts
            months_to_churn = months_between(current_month, sub_end) if sub["status"] == "cancelled" else 999
            decay_factor = max(0.1, 1.0 - (0.15 * max(0, 3 - months_to_churn)))

            monthly_sessions = int(base_sessions_per_user_per_month * seats_used * decay_factor)
            monthly_sessions = max(0, monthly_sessions + random.randint(-5, 5))

            for _ in range(monthly_sessions):
                event_day = rand_date(current_month, min(add_months(current_month, 1) - timedelta(days=1), sub_end, end_date))
                user_id = random.choice(user_ids)
                feature = random.choice(account_features)

                events.append({
                    "_id": gen_id(),
                    "event_id": gen_id(),
                    "account_id": account["account_id"],
                    "user_id": user_id,
                    "feature_name": feature,
                    "event_type": random.choice(["page_view", "action", "api_call", "export", "create", "update"]),
                    "session_id": gen_id(),
                    "duration_seconds": str(random.randint(30, 3600)),
                    "event_date": event_day.isoformat(),
                    "created_at": event_day.isoformat(),
                })

            current_month = add_months(current_month, 1)

    return events

# ─────────────────────────────────────────────────────────────────────────────
# Support Tickets Generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_tickets(accounts: List[Dict], subscriptions: List[Dict], end_date: date) -> List[Dict]:
    tickets = []
    sub_by_account = {s["account_id"]: s for s in subscriptions}

    ticket_subjects = {
        "Billing": ["Invoice discrepancy", "Upgrade request", "Refund request", "Payment failed", "Plan change"],
        "Technical": ["Login issues", "Integration broken", "Performance slow", "Data not syncing", "API error"],
        "Feature Request": ["Need bulk export", "Custom fields", "Better reporting", "Mobile app", "Slack integration"],
        "Onboarding": ["Setup help", "Training request", "Data migration", "Configuration help", "Best practices"],
        "Integration": ["Salesforce sync", "Zapier connection", "API authentication", "Webhook setup", "OAuth issue"],
        "Performance": ["Dashboard slow", "Export timeout", "Search not working", "Report generation slow", "Lag issues"],
    }

    for account in accounts:
        sub = sub_by_account.get(account["account_id"])
        if not sub:
            continue

        sub_start = date.fromisoformat(sub["start_date"])
        sub_end_str = sub["end_date"]
        sub_end = date.fromisoformat(sub_end_str) if sub_end_str else end_date

        # Ticket volume by plan (enterprise gets more support)
        tickets_per_month = {
            "starter": random.uniform(0.3, 1.0),
            "growth": random.uniform(0.5, 1.5),
            "business": random.uniform(1.0, 3.0),
            "enterprise": random.uniform(2.0, 6.0),
        }[sub["plan_id"]]

        months_active = months_between(sub_start, min(sub_end, end_date))
        total_tickets = max(0, int(tickets_per_month * months_active + random.gauss(0, 1)))

        for _ in range(total_tickets):
            created_at = rand_date(sub_start, min(sub_end, end_date))
            category = random.choice(TICKET_CATEGORIES)
            priority = random.choices(TICKET_PRIORITIES, weights=TICKET_PRIORITY_WEIGHTS)[0]

            # Resolution time by priority
            resolution_hours = {
                "low": random.randint(24, 168),
                "medium": random.randint(4, 48),
                "high": random.randint(1, 24),
                "critical": random.randint(1, 8),
            }[priority]

            is_resolved = random.random() < 0.82
            resolved_at = ""
            if is_resolved:
                resolved_dt = datetime.combine(created_at, datetime.min.time()) + timedelta(hours=resolution_hours)
                resolved_at = resolved_dt.isoformat()

            first_response_hours = random.randint(1, min(resolution_hours, 12))
            first_response_at = (datetime.combine(created_at, datetime.min.time()) + timedelta(hours=first_response_hours)).isoformat()

            csat = ""
            if is_resolved and random.random() < 0.60:
                csat = str(round(random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.08, 0.15, 0.35, 0.37])[0], 1))

            tickets.append({
                "_id": gen_id(),
                "ticket_id": gen_id(),
                "account_id": account["account_id"],
                "user_id": gen_id(),
                "subject": random.choice(ticket_subjects[category]),
                "category": category,
                "priority": priority,
                "status": "resolved" if is_resolved else random.choice(["open", "in_progress"]),
                "csat_score": csat,
                "created_at": created_at.isoformat(),
                "resolved_at": resolved_at,
                "first_response_at": first_response_at,
            })

    return tickets

# ─────────────────────────────────────────────────────────────────────────────
# Leads Generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_leads(accounts: List[Dict], start_date: date, end_date: date) -> List[Dict]:
    leads = []
    account_ids = [a["account_id"] for a in accounts]
    account_map = {a["account_id"]: a for a in accounts}

    # Generate leads for converted accounts
    for account in accounts:
        channel = account["acquisition_channel"]
        company_name = account["company_name"]
        contact_name = rand_person_name()
        created_at = date.fromisoformat(account["created_at"]) - timedelta(days=random.randint(7, 90))
        if created_at < start_date:
            created_at = start_date

        has_trial = random.random() < 0.70
        trial_start = created_at + timedelta(days=random.randint(0, 3)) if has_trial else None
        trial_end = (trial_start + timedelta(days=random.randint(7, 30))) if trial_start else None
        converted_at = (trial_end + timedelta(days=random.randint(0, 14))) if trial_end else (created_at + timedelta(days=random.randint(7, 45)))

        leads.append({
            "_id": gen_id(),
            "lead_id": gen_id(),
            "company_name": company_name,
            "contact_name": contact_name,
            "contact_email": rand_email(contact_name, company_name),
            "industry": account["industry"],
            "company_size": account["company_size"],
            "acquisition_channel": channel,
            "lead_source": random.choice(LEAD_SOURCES),
            "status": "converted",
            "trial_start_date": trial_start.isoformat() if trial_start else "",
            "trial_end_date": trial_end.isoformat() if trial_end else "",
            "converted_at": converted_at.isoformat(),
            "account_id": account["account_id"],
            "estimated_mrr": str(random.choice([99, 299, 799, 2499])),
            "created_at": created_at.isoformat(),
            "updated_at": converted_at.isoformat(),
        })

    # Generate lost leads (1.5x the converted count)
    num_lost = int(len(accounts) * 1.5)
    for _ in range(num_lost):
        channel = random.choices(ACQUISITION_CHANNELS, weights=CHANNEL_WEIGHTS)[0]
        company_name = rand_company_name()
        contact_name = rand_person_name()
        created_at = rand_date(start_date, end_date - timedelta(days=30))

        has_trial = random.random() < 0.45
        trial_start = created_at + timedelta(days=random.randint(0, 5)) if has_trial else None
        trial_end = (trial_start + timedelta(days=random.randint(7, 30))) if trial_start else None

        leads.append({
            "_id": gen_id(),
            "lead_id": gen_id(),
            "company_name": company_name,
            "contact_name": contact_name,
            "contact_email": rand_email(contact_name, company_name),
            "industry": random.choice(INDUSTRIES),
            "company_size": random.choices(COMPANY_SIZES, weights=[0.45, 0.35, 0.20])[0],
            "acquisition_channel": channel,
            "lead_source": random.choice(LEAD_SOURCES),
            "status": random.choices(["lost", "qualified", "new"], weights=[0.60, 0.25, 0.15])[0],
            "trial_start_date": trial_start.isoformat() if trial_start else "",
            "trial_end_date": trial_end.isoformat() if trial_end else "",
            "converted_at": "",
            "account_id": "",
            "estimated_mrr": str(random.choice([99, 299, 799, 2499])),
            "created_at": created_at.isoformat(),
            "updated_at": (created_at + timedelta(days=random.randint(1, 30))).isoformat(),
        })

    return leads

# ─────────────────────────────────────────────────────────────────────────────
# Main Generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_all(num_accounts: int = NUM_ACCOUNTS, num_months: int = NUM_MONTHS) -> Dict[str, List[Dict]]:
    end_date = date.today().replace(day=1)
    start_date = add_months(end_date, -num_months)

    print(f"🚀 FlowSync Data Generator")
    print(f"   Accounts: {num_accounts}")
    print(f"   Period: {start_date} → {end_date}")
    print(f"   Random seed: {RANDOM_SEED}")
    print()

    print("📊 Generating accounts...")
    accounts = generate_accounts(num_accounts, start_date)
    print(f"   ✓ {len(accounts)} accounts")

    print("📋 Generating subscriptions...")
    subscriptions = generate_subscriptions(accounts, end_date)
    print(f"   ✓ {len(subscriptions)} subscriptions")

    print("💳 Generating invoices...")
    invoices = generate_invoices(subscriptions, end_date)
    print(f"   ✓ {len(invoices)} invoices")

    print("📈 Generating usage events...")
    usage_events = generate_usage_events(accounts, subscriptions, end_date)
    print(f"   ✓ {len(usage_events)} usage events")

    print("🎫 Generating support tickets...")
    tickets = generate_tickets(accounts, subscriptions, end_date)
    print(f"   ✓ {len(tickets)} tickets")

    print("🎯 Generating leads...")
    leads = generate_leads(accounts, start_date, end_date)
    print(f"   ✓ {len(leads)} leads")

    return {
        "accounts": accounts,
        "subscriptions": subscriptions,
        "invoices": invoices,
        "usage_events": usage_events,
        "tickets": tickets,
        "leads": leads,
    }

def save_to_json(data: Dict[str, List[Dict]], output_dir: str = "data/seeds"):
    os.makedirs(output_dir, exist_ok=True)
    for entity, records in data.items():
        filepath = os.path.join(output_dir, f"{entity}.json")
        with open(filepath, "w") as f:
            json.dump(records, f, indent=2, default=str)
        print(f"   💾 Saved {len(records)} {entity} → {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FlowSync Synthetic Data Generator")
    parser.add_argument("--accounts", type=int, default=NUM_ACCOUNTS)
    parser.add_argument("--months", type=int, default=NUM_MONTHS)
    parser.add_argument("--output", type=str, default="data/seeds")
    parser.add_argument("--json", action="store_true", help="Save to JSON files")
    args = parser.parse_args()

    data = generate_all(args.accounts, args.months)

    if args.json:
        print("\n💾 Saving to JSON...")
        save_to_json(data, args.output)

    print("\n✅ Data generation complete!")
    total = sum(len(v) for v in data.values())
    print(f"   Total records: {total:,}")
