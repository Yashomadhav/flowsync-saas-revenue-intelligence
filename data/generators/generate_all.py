"""
FlowSync - Master Data Generation Script
Orchestrates all generators in dependency order and writes CSVs to data/seeds/.
Optionally loads into PostgreSQL when --load flag is passed.

Usage:
    python generate_all.py                  # Generate CSVs only
    python generate_all.py --load           # Generate + load into Postgres
    python generate_all.py --load --no-truncate  # Append mode
    python generate_all.py --seed 99        # Custom random seed
"""

from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path

GENERATORS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GENERATORS_DIR))

OUTPUT_DIR = GENERATORS_DIR.parent / "seeds"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def banner(msg: str) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  {msg}")
    print("=" * width)


def step(label: str, fn, *args, **kwargs):
    print(f"\n[GEN] {label}...")
    t0 = time.time()
    result = fn(*args, **kwargs)
    elapsed = time.time() - t0
    print(f"[GEN] {label} done in {elapsed:.1f}s")
    return result


def run(custom_seed: int | None = None, load: bool = False, no_truncate: bool = False):
    banner("FlowSync Synthetic Data Generator")
    print(f"  Output dir : {OUTPUT_DIR}")
    print(f"  Load to DB : {load}")

    if custom_seed is not None:
        import config as cfg
        cfg.RANDOM_SEED = custom_seed
        print(f"  Random seed: {custom_seed}")

    total_start = time.time()

    # ── Step 1: Reference tables ──────────────────────────────────────────
    banner("Step 1/9 — Plans")
    from generate_plans import generate_plans, save_plans
    plans = step("generate_plans", generate_plans)
    step("save_plans", save_plans, plans, OUTPUT_DIR)

    banner("Step 2/9 — Features")
    from generate_features import generate_features, save_features
    features = step("generate_features", generate_features)
    step("save_features", save_features, features, OUTPUT_DIR)

    banner("Step 3/9 — Calendar")
    from build_calendar import generate_calendar, save_calendar
    calendar = step("generate_calendar", generate_calendar)
    step("save_calendar", save_calendar, calendar, OUTPUT_DIR)

    # ── Step 2: Core entities ─────────────────────────────────────────────
    banner("Step 4/9 — Accounts")
    from generate_accounts import generate_accounts, save_accounts
    accounts = step("generate_accounts", generate_accounts)
    step("save_accounts", save_accounts, accounts, OUTPUT_DIR)

    banner("Step 5/9 — Subscriptions")
    from generate_subscriptions import generate_subscriptions, save_subscriptions
    subscriptions = step("generate_subscriptions", generate_subscriptions, accounts)
    step("save_subscriptions", save_subscriptions, subscriptions, OUTPUT_DIR)

    banner("Step 6/9 — Invoices")
    from generate_invoices import generate_invoices, save_invoices
    invoices = step("generate_invoices", generate_invoices, subscriptions)
    step("save_invoices", save_invoices, invoices, OUTPUT_DIR)

    # ── Step 3: Event tables ──────────────────────────────────────────────
    banner("Step 7/9 — Usage Events")
    from generate_usage_events import generate_usage_events, save_usage_events
    usage_events = step("generate_usage_events", generate_usage_events, accounts, subscriptions)
    step("save_usage_events", save_usage_events, usage_events, OUTPUT_DIR)

    banner("Step 8/9 — Support Tickets")
    from generate_support_tickets import generate_support_tickets, save_support_tickets
    tickets = step("generate_support_tickets", generate_support_tickets, accounts, subscriptions)
    step("save_support_tickets", save_support_tickets, tickets, OUTPUT_DIR)

    banner("Step 9/9 — Leads")
    from generate_leads import generate_leads, save_leads
    leads = step("generate_leads", generate_leads, accounts)
    step("save_leads", save_leads, leads, OUTPUT_DIR)

    # ── Summary ───────────────────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    banner("Generation Complete")
    print(f"  Plans          : {len(plans):>8,}")
    print(f"  Features       : {len(features):>8,}")
    print(f"  Calendar rows  : {len(calendar):>8,}")
    print(f"  Accounts       : {len(accounts):>8,}")
    print(f"  Subscriptions  : {len(subscriptions):>8,}")
    print(f"  Invoices       : {len(invoices):>8,}")
    print(f"  Usage events   : {len(usage_events):>8,}")
    print(f"  Support tickets: {len(tickets):>8,}")
    print(f"  Leads          : {len(leads):>8,}")
    print(f"\n  Total time     : {total_elapsed:.1f}s")
    print(f"  Output dir     : {OUTPUT_DIR}")

    # ── Optional: Load to PostgreSQL ──────────────────────────────────────
    if load:
        banner("Loading CSVs into PostgreSQL")
        try:
            from load_raw_to_postgres import load_all
            load_all(seeds_dir=OUTPUT_DIR, truncate=not no_truncate)
        except SystemExit:
            print("[loader] psycopg2 not available — skipping DB load")
        except Exception as exc:
            print(f"[loader] ERROR: {exc}")
            print("[loader] CSVs are still available in data/seeds/")

    banner("Done")
    return {
        "plans": plans,
        "features": features,
        "calendar": calendar,
        "accounts": accounts,
        "subscriptions": subscriptions,
        "invoices": invoices,
        "usage_events": usage_events,
        "tickets": tickets,
        "leads": leads,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FlowSync synthetic data generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Load generated CSVs into PostgreSQL after generation",
    )
    parser.add_argument(
        "--no-truncate",
        action="store_true",
        help="Skip TRUNCATE before loading (append mode)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override random seed (default: 42 from config.py)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override output directory for CSV files",
    )
    args = parser.parse_args()

    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run(
        custom_seed=args.seed,
        load=args.load,
        no_truncate=args.no_truncate,
    )
