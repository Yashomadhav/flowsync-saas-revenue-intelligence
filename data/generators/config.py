"""
FlowSync Revenue Intelligence — Shared Configuration & Constants
All generator modules import from here for consistency.
"""

from __future__ import annotations
import os
from pathlib import Path
from datetime import date, timedelta
import random

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED: int = int(os.getenv("FLOWSYNC_SEED", "42"))
random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent  # data/
OUTPUT_DIR = ROOT_DIR / "seeds"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Date range — 24 months of history
# ---------------------------------------------------------------------------
SIM_END_DATE: date = date.today().replace(day=1) - timedelta(days=1)  # last day of prev month
SIM_START_DATE: date = (SIM_END_DATE.replace(day=1) - timedelta(days=365 * 2)).replace(day=1)
MONTHS_OF_HISTORY: int = 24

# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------
PLANS = [
    {
        "plan_id": "plan_starter",
        "plan_name": "Starter",
        "monthly_price": 99.0,
        "annual_price": 990.0,       # 10 months
        "seat_based": False,
        "price_per_seat": 0.0,
        "min_seats": 1,
        "max_seats": 5,
        "features": ["core_workflows", "basic_analytics", "email_support"],
        "tier": 1,
    },
    {
        "plan_id": "plan_growth",
        "plan_name": "Growth",
        "monthly_price": 299.0,
        "annual_price": 2990.0,
        "seat_based": False,
        "price_per_seat": 0.0,
        "min_seats": 1,
        "max_seats": 25,
        "features": ["core_workflows", "advanced_analytics", "integrations", "priority_support"],
        "tier": 2,
    },
    {
        "plan_id": "plan_pro",
        "plan_name": "Pro",
        "monthly_price": 799.0,
        "annual_price": 7990.0,
        "seat_based": True,
        "price_per_seat": 29.0,
        "min_seats": 5,
        "max_seats": 100,
        "features": ["core_workflows", "advanced_analytics", "integrations", "api_access",
                     "custom_workflows", "priority_support", "sso"],
        "tier": 3,
    },
    {
        "plan_id": "plan_enterprise",
        "plan_name": "Enterprise",
        "monthly_price": 2499.0,
        "annual_price": 24990.0,
        "seat_based": True,
        "price_per_seat": 49.0,
        "min_seats": 10,
        "max_seats": 1000,
        "features": ["core_workflows", "advanced_analytics", "integrations", "api_access",
                     "custom_workflows", "priority_support", "sso", "dedicated_csm",
                     "custom_reporting", "audit_logs", "saml"],
        "tier": 4,
    },
]

PLAN_IDS = [p["plan_id"] for p in PLANS]
PLAN_MAP = {p["plan_id"]: p for p in PLANS}

# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------
FEATURES = [
    {"feature_id": "feat_core_workflows",     "feature_name": "Core Workflows",      "category": "automation"},
    {"feature_id": "feat_basic_analytics",    "feature_name": "Basic Analytics",     "category": "analytics"},
    {"feature_id": "feat_advanced_analytics", "feature_name": "Advanced Analytics",  "category": "analytics"},
    {"feature_id": "feat_integrations",       "feature_name": "Integrations",        "category": "connectivity"},
    {"feature_id": "feat_api_access",         "feature_name": "API Access",          "category": "developer"},
    {"feature_id": "feat_custom_workflows",   "feature_name": "Custom Workflows",    "category": "automation"},
    {"feature_id": "feat_sso",                "feature_name": "SSO / SAML",          "category": "security"},
    {"feature_id": "feat_dedicated_csm",      "feature_name": "Dedicated CSM",       "category": "success"},
    {"feature_id": "feat_custom_reporting",   "feature_name": "Custom Reporting",    "category": "analytics"},
    {"feature_id": "feat_audit_logs",         "feature_name": "Audit Logs",          "category": "security"},
    {"feature_id": "feat_email_support",      "feature_name": "Email Support",       "category": "support"},
    {"feature_id": "feat_priority_support",   "feature_name": "Priority Support",    "category": "support"},
]

FEATURE_IDS = [f["feature_id"] for f in FEATURES]

# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------
INDUSTRIES = [
    "SaaS", "FinTech", "HealthTech", "E-commerce", "Manufacturing",
    "Retail", "Education", "Media & Entertainment", "Logistics", "Professional Services",
]

REGIONS = ["North America", "Europe", "APAC", "LATAM", "Middle East & Africa"]

COMPANY_SIZES = ["SMB", "Mid-Market", "Enterprise"]

ACQUISITION_CHANNELS = [
    "Organic Search", "Paid Search", "Referral", "Partner", "Outbound Sales",
    "Product-Led Growth", "Content Marketing", "Event / Conference",
]

BILLING_CYCLES = ["monthly", "annual"]

# ---------------------------------------------------------------------------
# Volume targets
# ---------------------------------------------------------------------------
TARGET_ACCOUNTS = 300          # total accounts created over history
TARGET_LEADS = 1200            # total leads in funnel
TARGET_USAGE_EVENTS = 50_000   # total usage events
TARGET_TICKETS = 2_500         # total support tickets

# ---------------------------------------------------------------------------
# Churn / expansion probabilities (monthly)
# ---------------------------------------------------------------------------
MONTHLY_CHURN_RATE = 0.025          # 2.5% base monthly churn
MONTHLY_EXPANSION_RATE = 0.08       # 8% of active accounts expand
MONTHLY_CONTRACTION_RATE = 0.04     # 4% of active accounts contract
MONTHLY_REACTIVATION_RATE = 0.10    # 10% of churned accounts reactivate

# ---------------------------------------------------------------------------
# Health score weights
# ---------------------------------------------------------------------------
HEALTH_WEIGHTS = {
    "usage_frequency": 0.25,
    "seat_utilization": 0.20,
    "feature_adoption": 0.15,
    "support_burden": 0.15,
    "csat": 0.10,
    "payment_health": 0.10,
    "tenure_stability": 0.05,
}

# ---------------------------------------------------------------------------
# Lead funnel stages
# ---------------------------------------------------------------------------
LEAD_STAGES = ["lead", "qualified", "trial", "trial_active", "converted", "lost"]

LEAD_STAGE_CONVERSION = {
    "lead":         0.55,   # 55% become qualified
    "qualified":    0.60,   # 60% start trial
    "trial":        0.85,   # 85% activate trial
    "trial_active": 0.42,   # 42% convert to paid
    "converted":    1.0,
    "lost":         0.0,
}

# ---------------------------------------------------------------------------
# Support ticket config
# ---------------------------------------------------------------------------
TICKET_PRIORITIES = ["low", "medium", "high", "critical"]
TICKET_CATEGORIES = [
    "billing", "technical", "feature_request", "onboarding",
    "integration", "performance", "security", "general",
]
TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def weighted_choice(choices: list, weights: list):
    """Pick one item from choices using weights."""
    return random.choices(choices, weights=weights, k=1)[0]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def add_months(d: date, n: int) -> date:
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    import calendar
    day = min(d.day, calendar.monthrange(year, month)[1])
    return d.replace(year=year, month=month, day=day)


def month_start(d: date) -> date:
    return d.replace(day=1)


def month_end(d: date) -> date:
    import calendar
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])
