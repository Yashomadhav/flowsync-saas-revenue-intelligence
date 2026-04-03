"use client";

import React, { useEffect, useState } from "react";
import { Users, TrendingDown, Activity, BarChart2 } from "lucide-react";
import { DashboardHeader, PageHeader } from "@/components/layout/DashboardHeader";
import { KPICard, KPICardSkeleton } from "@/components/dashboard/KPICard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { CohortRetentionHeatmap, CohortRevenueHeatmap } from "@/components/charts/CohortHeatmap";
import { cohortsApi } from "@/lib/api";
import { formatPercent, formatRetentionRate, CHART_PALETTE } from "@/lib/formatters";
import type {
  CohortRetentionRow, CohortRevenueRow, LogoChurnTrend, RetentionBySegment,
} from "@/types";
import {
  MOCK_COHORT_RETENTION, MOCK_COHORT_REVENUE, MOCK_LOGO_CHURN_TREND,
  MOCK_RETENTION_BY_PLAN, MOCK_RETENTION_BY_SIZE,
} from "@/lib/mock-data";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  BarChart, Bar, Cell,
} from "recharts";

export default function CohortRetentionPage() {
  const [customerCohorts, setCustomerCohorts] = useState<CohortRetentionRow[]>([]);
  const [revenueCohorts, setRevenueCohorts] = useState<CohortRevenueRow[]>([]);
  const [churnTrend, setChurnTrend] = useState<LogoChurnTrend[]>([]);
  const [retByPlan, setRetByPlan] = useState<RetentionBySegment[]>([]);
  const [retBySize, setRetBySize] = useState<RetentionBySegment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [cc, rc, ct, rp, rs] = await Promise.all([
          cohortsApi.getCustomerRetention(),
          cohortsApi.getRevenueRetention(),
          cohortsApi.getLogoChurnTrend(),
          cohortsApi.getRetentionByPlan(),
          cohortsApi.getRetentionBySize(),
        ]);
        setCustomerCohorts(cc);
        setRevenueCohorts(rc);
        setChurnTrend(ct);
        setRetByPlan(rp);
        setRetBySize(rs);
      } catch {
        setCustomerCohorts(MOCK_COHORT_RETENTION);
        setRevenueCohorts(MOCK_COHORT_REVENUE);
        setChurnTrend(MOCK_LOGO_CHURN_TREND);
        setRetByPlan(MOCK_RETENTION_BY_PLAN);
        setRetBySize(MOCK_RETENTION_BY_SIZE);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Compute summary stats from latest churn trend
  const latestChurn = churnTrend[churnTrend.length - 1];
  // period_number is 0-indexed: period 11 = the 12th month (1-year mark)
  const avgNRR = revenueCohorts.length
    ? revenueCohorts.filter((r) => r.period_number === 11).reduce((s, r) => s + r.nrr, 0) /
      Math.max(1, revenueCohorts.filter((r) => r.period_number === 11).length)
    : 0;
  const avgRetention12 = customerCohorts.length
    ? customerCohorts.filter((r) => r.period_number === 11).reduce((s, r) => s + r.customer_retention_rate, 0) /
      Math.max(1, customerCohorts.filter((r) => r.period_number === 11).length)
    : 0;

  return (
    <>
      <DashboardHeader
        title="Cohort Retention"
        description="Customer and revenue retention cohort analysis"
      />
      <div className="p-6 space-y-6">
        <PageHeader
          title="Cohort Retention"
          description="Analyze how customer cohorts retain over time"
        />

        {/* KPI Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => <KPICardSkeleton key={i} />)
          ) : (
            <>
              <KPICard
                title="Logo Churn Rate"
                value={formatPercent(latestChurn?.logo_churn_rate ?? 0)}
                delta={latestChurn ? -latestChurn.logo_churn_rate : 0}
                invertDelta
                icon={TrendingDown}
                iconColor="text-red-400"
                index={0}
              />
              <KPICard
                title="Revenue Churn Rate"
                value={formatPercent(latestChurn?.revenue_churn_rate ?? 0)}
                delta={latestChurn ? -latestChurn.revenue_churn_rate : 0}
                invertDelta
                icon={TrendingDown}
                iconColor="text-amber-400"
                index={1}
              />
              <KPICard
                title="Avg 12-Month Retention"
                value={formatPercent(avgRetention12)}
                icon={Users}
                iconColor="text-blue-400"
                index={2}
              />
              <KPICard
                title="Avg 12-Month NRR"
                value={formatRetentionRate(avgNRR)}
                icon={Activity}
                iconColor="text-violet-400"
                index={3}
              />
            </>
          )}
        </div>

        {/* Customer Cohort Heatmap */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Customer Retention Cohort Heatmap</CardTitle>
            <CardDescription className="text-xs">
              % of customers from each cohort still active at each period — green = high retention
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-[320px] animate-pulse bg-muted rounded-lg" />
            ) : (
              <CohortRetentionHeatmap data={customerCohorts} maxPeriods={12} />
            )}
          </CardContent>
        </Card>

        {/* Revenue Cohort Heatmap */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Revenue Retention (NRR) Cohort Heatmap</CardTitle>
            <CardDescription className="text-xs">
              Net Revenue Retention by cohort — values above 100% indicate expansion revenue
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-[320px] animate-pulse bg-muted rounded-lg" />
            ) : (
              <CohortRevenueHeatmap data={revenueCohorts} maxPeriods={12} />
            )}
          </CardContent>
        </Card>

        {/* Logo Churn Trend + Retention by Plan */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Logo & Revenue Churn Trend</CardTitle>
              <CardDescription className="text-xs">Monthly churn rates over time</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[240px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={churnTrend} margin={{ top: 5, right: 20, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
                    <XAxis
                      dataKey="month"
                      tickFormatter={(v: string) => v.slice(0, 7)}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tickFormatter={(v: number) => `${v.toFixed(1)}%`}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                      width={45}
                    />
                    <Tooltip
                      formatter={(v: number) => `${v.toFixed(2)}%`}
                      contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }}
                    />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line type="monotone" dataKey="logo_churn_rate" name="Logo Churn" stroke="#ef4444" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="revenue_churn_rate" name="Revenue Churn" stroke="#f59e0b" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Retention by Plan</CardTitle>
              <CardDescription className="text-xs">Average customer retention rate by subscription plan</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[240px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={retByPlan} margin={{ top: 5, right: 20, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
                    <XAxis
                      dataKey="plan_name"
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tickFormatter={(v: number) => `${v.toFixed(0)}%`}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                      width={40}
                      domain={[0, 100]}
                    />
                    <Tooltip
                      formatter={(v: number) => `${v.toFixed(1)}%`}
                      contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }}
                    />
                    <Bar dataKey="avg_customer_retention" name="Avg Retention" radius={[4, 4, 0, 0]}>
                      {retByPlan.map((_, i) => (
                        <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} opacity={0.85} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Retention by Company Size */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Retention by Company Size</CardTitle>
            <CardDescription className="text-xs">
              Customer retention, revenue retention, and NRR segmented by company size
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-[240px] animate-pulse bg-muted rounded-lg" />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Segment</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Accounts</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Avg Customer Retention</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Avg Revenue Retention</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Avg NRR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {retBySize.map((row: RetentionBySegment, i: number) => (
                      <tr key={i} className="border-b border-border/20 hover:bg-muted/30 transition-colors">
                        <td className="py-2 px-3 font-medium text-foreground capitalize">{row.company_size ?? "—"}</td>
                        <td className="py-2 px-3 text-right text-muted-foreground">{row.cohort_accounts}</td>
                        <td className="py-2 px-3 text-right">
                          <span className={row.avg_customer_retention >= 80 ? "text-emerald-400 font-semibold" : row.avg_customer_retention >= 60 ? "text-amber-400" : "text-red-400"}>
                            {row.avg_customer_retention.toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right">
                          <span className={row.avg_revenue_retention >= 80 ? "text-emerald-400 font-semibold" : row.avg_revenue_retention >= 60 ? "text-amber-400" : "text-red-400"}>
                            {row.avg_revenue_retention.toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right">
                          <span className={row.avg_nrr >= 100 ? "text-emerald-400 font-semibold" : "text-red-400"}>
                            {row.avg_nrr.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
