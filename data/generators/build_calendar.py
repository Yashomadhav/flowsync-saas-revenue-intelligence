"""
FlowSync — Calendar Table Generator
Outputs: data/seeds/calendar.csv → dim_calendar (bronze)

Generates one row per day for the full simulation window plus 3 months forward.
Includes fiscal quarter, week-of-year, is_weekend, is_month_start/end, etc.
"""

from __future__ import annotations
import csv
from datetime import date, timedelta
from pathlib import Path
from config import SIM_START_DATE, SIM_END_DATE, OUTPUT_DIR


def generate_calendar(
    start: date = SIM_START_DATE,
    end: date = SIM_END_DATE,
    out_dir: Path = OUTPUT_DIR,
) -> list[dict]:
    rows: list[dict] = []
    current = start
    # extend 3 months beyond sim end for forward-looking analysis
    extended_end = date(end.year + (1 if end.month > 9 else 0), (end.month + 3 - 1) % 12 + 1, 1)

    while current <= extended_end:
        import calendar as cal_mod
        month_last_day = cal_mod.monthrange(current.year, current.month)[1]
        fiscal_quarter = ((current.month - 1) // 3) + 1  # Jan-Mar = Q1

        rows.append({
            "date_id":          current.strftime("%Y%m%d"),
            "full_date":        current.isoformat(),
            "year":             current.year,
            "quarter":          fiscal_quarter,
            "quarter_label":    f"Q{fiscal_quarter} {current.year}",
            "month":            current.month,
            "month_name":       current.strftime("%B"),
            "month_short":      current.strftime("%b"),
            "month_label":      current.strftime("%b %Y"),
            "week_of_year":     int(current.strftime("%W")),
            "day_of_week":      current.weekday(),          # 0=Mon, 6=Sun
            "day_name":         current.strftime("%A"),
            "day_of_month":     current.day,
            "day_of_year":      int(current.strftime("%j")),
            "is_weekend":       current.weekday() >= 5,
            "is_weekday":       current.weekday() < 5,
            "is_month_start":   current.day == 1,
            "is_month_end":     current.day == month_last_day,
            "is_quarter_start": current.day == 1 and current.month in (1, 4, 7, 10),
            "is_quarter_end":   current.day == month_last_day and current.month in (3, 6, 9, 12),
            "is_year_start":    current.day == 1 and current.month == 1,
            "is_year_end":      current.day == 31 and current.month == 12,
            "fiscal_year":      current.year,
            "fiscal_quarter":   fiscal_quarter,
            "yyyymm":           int(current.strftime("%Y%m")),
        })
        current += timedelta(days=1)

    return rows


def save_calendar(rows: list[dict], out_dir: Path = OUTPUT_DIR) -> Path:
    path = out_dir / "calendar.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[calendar] Wrote {len(rows)} rows → {path}")
    return path


if __name__ == "__main__":
    rows = generate_calendar()
    save_calendar(rows)
