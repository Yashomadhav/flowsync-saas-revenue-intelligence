"use client";

import React from "react";
import { formatCohortPeriod, formatMonth, getRetentionColor, getNRRColor } from "@/lib/formatters";
import type { CohortRetentionRow, CohortRevenueRow } from "@/types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Customer Retention Cohort Heatmap
// ---------------------------------------------------------------------------
interface CohortRetentionHeatmapProps {
  data: CohortRetentionRow[];
  maxPeriods?: number;
}

export function CohortRetentionHeatmap({ data, maxPeriods = 12 }: CohortRetentionHeatmapProps) {
  // Group by cohort_month
  const cohorts = Array.from(new Set(data.map((r) => r.cohort_month))).sort();
  const periods = Array.from({ length: maxPeriods + 1 }, (_, i) => i);

  const lookup = new Map<string, CohortRetentionRow>();
  data.forEach((r) => lookup.set(`${r.cohort_month}-${r.period_number}`, r));

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="text-left py-1.5 px-2 text-muted-foreground font-medium whitespace-nowrap w-20">
              Cohort
            </th>
            <th className="text-center py-1.5 px-1 text-muted-foreground font-medium whitespace-nowrap w-12">
              Size
            </th>
            {periods.map((p) => (
              <th key={p} className="text-center py-1.5 px-1 text-muted-foreground font-medium whitespace-nowrap min-w-[44px]">
                {formatCohortPeriod(p)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cohorts.map((cohort) => {
            const cohortData = data.find((r) => r.cohort_month === cohort);
            const size = cohortData?.cohort_size ?? 0;
            return (
              <tr key={cohort} className="border-t border-border/30">
                <td className="py-1 px-2 text-muted-foreground whitespace-nowrap font-medium">
                  {formatMonth(cohort)}
                </td>
                <td className="py-1 px-1 text-center text-muted-foreground">{size}</td>
                {periods.map((p) => {
                  const row = lookup.get(`${cohort}-${p}`);
                  const rate = row?.customer_retention_rate ?? null;
                  return (
                    <td key={p} className="py-1 px-0.5">
                      {rate !== null ? (
                        <div
                          className={cn(
                            "rounded text-center py-1 px-0.5 font-medium text-white text-[10px] cursor-default transition-opacity hover:opacity-80",
                            getRetentionColor(rate)
                          )}
                          title={`${cohort} M${p}: ${rate.toFixed(1)}%`}
                        >
                          {rate.toFixed(0)}%
                        </div>
                      ) : (
                        <div className="rounded bg-muted/20 py-1 px-0.5 text-center text-[10px] text-muted-foreground/30">
                          —
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Revenue Retention Cohort Heatmap (NRR)
// ---------------------------------------------------------------------------
interface CohortRevenueHeatmapProps {
  data: CohortRevenueRow[];
  maxPeriods?: number;
}

export function CohortRevenueHeatmap({ data, maxPeriods = 12 }: CohortRevenueHeatmapProps) {
  const cohorts = Array.from(new Set(data.map((r) => r.cohort_month))).sort();
  const periods = Array.from({ length: maxPeriods + 1 }, (_, i) => i);

  const lookup = new Map<string, CohortRevenueRow>();
  data.forEach((r) => lookup.set(`${r.cohort_month}-${r.period_number}`, r));

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="text-left py-1.5 px-2 text-muted-foreground font-medium whitespace-nowrap w-20">
              Cohort
            </th>
            <th className="text-center py-1.5 px-1 text-muted-foreground font-medium whitespace-nowrap w-12">
              Size
            </th>
            {periods.map((p) => (
              <th key={p} className="text-center py-1.5 px-1 text-muted-foreground font-medium whitespace-nowrap min-w-[44px]">
                {formatCohortPeriod(p)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cohorts.map((cohort) => {
            const cohortData = data.find((r) => r.cohort_month === cohort);
            const size = cohortData?.cohort_size ?? 0;
            return (
              <tr key={cohort} className="border-t border-border/30">
                <td className="py-1 px-2 text-muted-foreground whitespace-nowrap font-medium">
                  {formatMonth(cohort)}
                </td>
                <td className="py-1 px-1 text-center text-muted-foreground">{size}</td>
                {periods.map((p) => {
                  const row = lookup.get(`${cohort}-${p}`);
                  const nrr = row ? row.nrr : null;
                  return (
                    <td key={p} className="py-1 px-0.5">
                      {nrr !== null ? (
                        <div
                          className={cn(
                            "rounded text-center py-1 px-0.5 font-medium text-white text-[10px] cursor-default transition-opacity hover:opacity-80",
                            getNRRColor(nrr)
                          )}
                          title={`${cohort} M${p}: NRR ${nrr.toFixed(1)}%`}
                        >
                          {nrr.toFixed(0)}%
                        </div>
                      ) : (
                        <div className="rounded bg-muted/20 py-1 px-0.5 text-center text-[10px] text-muted-foreground/30">
                          —
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
