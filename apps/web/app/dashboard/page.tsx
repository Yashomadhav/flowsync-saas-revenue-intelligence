"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  DollarSign, TrendingUp, TrendingDown, Users, Activity,
  ArrowUpRight, ArrowDownRight, AlertTriangle, Zap,
} from "lucide-react";
import { DashboardHeader, PageHeader } from "@/components/layout/DashboardHeader";
import { KPICard, KPICardSkeleton } from "@/components/dashboard/KPICard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { MRRTrendChart } from "@/components/charts/MRRTrendChart";
import { WaterfallChart } from "@/components/charts/WaterfallChart";
import { executiveApi } from "@/lib/api";
import { formatMRR, formatARR, formatPercent, formatRetentionRate, formatDelta, PLAN_COLORS, RISK_COLORS } from "@/lib/formatters";
import type { ExecutiveSummary, MRRTrendPoint, WaterfallData, RevenueByPlan, RevenueByRegion, TopAccount } from "@/types";
import {
  MOCK_EXECUTIVE_SUMMARY, MOCK_MRR_TREND, MOCK_WATERFALL,
  MOCK_REVENUE_BY_PLAN, MOCK_REVENUE_BY_REGION,
  MOCK_TOP_EXPANDING, MOCK_TOP_CHURN_RISK,
} from "@/lib/mock-data";
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import { cn } from "@/lib/utils";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.07, duration: 0.4 } }),
};

export default function ExecutiveOverviewPage() {
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
  const [trend, setTrend] = useState<MRRTrendPoint[]>([]);
  const [waterfall, setWaterfall] = useState<WaterfallData | null>(null);
  const [byPlan, setByPlan] = useState<RevenueByPlan[]>([]);
  const [byRegion, setByRegion] = useState<RevenueByRegion[]>([]);
  const [topExpanding, setTopExpanding] = useState<TopAccount[]>([]);
  const [topRisk, setTopRisk] = useState<TopAccount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, t, w, p, r, e, rk] = await Promise.all([
          executiveApi.getSummary(),
          executiveApi.getMRRTrend(),
          executiveApi.getWaterfall(),
          executiveApi.getRevenueByPlan(),
          executiveApi.getRevenueByRegion(),
          executiveApi.getTopExpanding(),
          executiveApi.getTopChurnRisk(),
        ]);
        setSummary(s);
        setTrend(t);
        setWaterfall(w);
        setByPlan(p);
        setByRegion(r);
        setTopExpanding(e);
        setTopRisk(rk);
      } catch {
        setSummary(MOCK_EXECUTIVE_SUMMARY as any);
        setTrend(MOCK_MRR_TREND as any);
        setWaterfall(MOCK_WATERFALL as any);
        setByPlan(MOCK_REVENUE_BY_PLAN as any);
        setByRegion(MOCK_REVENUE_BY_REGION as any);
        setTopExpanding(MOCK_TOP_EXPANDING as any);
        setTopRisk(MOCK_TOP_CHURN_RISK as any);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const mrrDelta = summary
    ? ((summary.total_mrr - summary.prev_mrr) / summary.prev_mrr) * 100
    : 0;

  return (
    <>
      <DashboardHeader
        title="Executive Overview"
        description="FlowSync revenue intelligence — real-time SaaS metrics"
      />
      <div className="p-6 space-y-6">
        <PageHeader
          title="Executive Overview"
          description="Key revenue metrics and business health at a glance"
          badge="Live"
        />

        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {loading ? (
            Array.from({ length: 5 }).map((_, i) => <KPICardSkeleton key={i} />)
          ) : (
            <>
              <KPICard
                title="Monthly Recurring Revenue"
                value={summary?.total_mrr ?? 0}
                format="currency"
                delta={mrrDelta}
                icon={DollarSign}
                iconColor="text-brand-400"
                index={0}
              />
              <KPICard
                title="Annual Recurring Revenue"
                value={summary?.arr ?? 0}
                format="currency"
                icon={TrendingUp}
                iconColor="text-emerald-400"
                subtitle={`${formatMRR(summary?.total_mrr ?? 0)} MRR × 12`}
                index={1}
              />
              <KPICard
                title="Net Revenue Retention"
                value={formatRetentionRate(summary?.nrr ?? 100)}
                delta={summary ? summary.nrr - 100 : 0}
                icon={Activity}
                iconColor="text-violet-400"
                index={2}
              />
              <KPICard
                title="Logo Churn Rate"
                value={formatPercent(summary?.logo_churn_rate ?? 0)}
                delta={summary?.logo_churn_rate ? -summary.logo_churn_rate : 0}
                invertDelta
                icon={TrendingDown}
                iconColor="text-red-400"
                index={3}
              />
              <KPICard
                title="Active Accounts"
                value={summary?.active_accounts ?? 0}
                format="number"
                delta={summary ? ((summary.active_accounts - summary.prev_active_accounts) / summary.prev_active_accounts) * 100 : 0}
                icon={Users}
                iconColor="text-blue-400"
                index={4}
              />
            </>
          )}
        </div>

        {/* MRR Trend + Waterfall */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <Card className="xl:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">MRR & ARR Trend</CardTitle>
              <CardDescription className="text-xs">24-month recurring revenue trajectory</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[300px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <MRRTrendChart data={trend} height={300} />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Revenue Waterfall</CardTitle>
              <CardDescription className="text-xs">MRR bridge — current month movements</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[280px] animate-pulse bg-muted rounded-lg" />
              ) : waterfall ? (
                <WaterfallChart data={waterfall.waterfall} height={280} />
              ) : null}
            </CardContent>
          </Card>
        </div>

        {/* Revenue by Plan + Region */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Revenue by Plan</CardTitle>
              <CardDescription className="text-xs">MRR distribution across subscription tiers</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[240px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <div className="flex items-center gap-6">
                  <ResponsiveContainer width={180} height={180}>
                    <PieChart>
                      <Pie
                        data={byPlan}
                        dataKey="total_mrr"
                        nameKey="plan_name"
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={2}
                      >
                        {byPlan.map((entry, i) => (
                          <Cell
                            key={entry.plan_name}
                            fill={PLAN_COLORS[entry.plan_name as keyof typeof PLAN_COLORS] ?? "#6b7280"}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(v: number) => formatMRR(v)}
                        contentStyle={{
                          background: "hsl(var(--card))",
                          border: "1px solid hsl(var(--border))",
                          borderRadius: 8,
                          fontSize: 11,
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex-1 space-y-2">
                    {byPlan.map((p) => (
                      <div key={p.plan_name} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <div
                            className="h-2 w-2 rounded-full"
                            style={{ backgroundColor: PLAN_COLORS[p.plan_name as keyof typeof PLAN_COLORS] ?? "#6b7280" }}
                          />
                          <span className="capitalize text-muted-foreground">{p.plan_name}</span>
                        </div>
                        <div className="text-right">
                          <span className="font-medium text-foreground">{formatMRR(p.total_mrr)}</span>
                          <span className="text-muted-foreground ml-1">({p.account_count})</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Revenue by Region</CardTitle>
              <CardDescription className="text-xs">Geographic MRR distribution</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[240px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={byRegion} layout="vertical" margin={{ top: 0, right: 20, left: 60, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} horizontal={false} />
                    <XAxis
                      type="number"
                      tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      type="category"
                      dataKey="region"
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                      width={60}
                    />
                    <Tooltip
                      formatter={(v: number) => formatMRR(v)}
                      contentStyle={{
                        background: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: 8,
                        fontSize: 11,
                      }}
                    />
                    <Bar dataKey="total_mrr" name="MRR" fill="#3b82f6" radius={[0, 4, 4, 0]} opacity={0.85} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Top Expanding + Top Churn Risk */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Top Expanding */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <ArrowUpRight className="h-4 w-4 text-emerald-400" />
                Top Expanding Accounts
              </CardTitle>
              <CardDescription className="text-xs">Highest MRR growth this month</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {loading
                  ? Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="h-10 animate-pulse bg-muted rounded-lg" />
                    ))
                  : topExpanding.slice(0, 6).map((acct, i) => (
                      <motion.div
                        key={acct.account_id}
                        custom={i}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="flex items-center justify-between py-1.5 border-b border-border/30 last:border-0"
                      >
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-foreground truncate">{acct.company_name}</p>
                          <p className="text-[10px] text-muted-foreground capitalize">{acct.plan_name} · {acct.region}</p>
                        </div>
                        <div className="text-right shrink-0 ml-2">
                          <p className="text-xs font-semibold text-foreground">{formatMRR(acct.current_mrr)}</p>
                          {acct.expansion_mrr && (
                            <p className="text-[10px] text-emerald-400">+{formatMRR(acct.expansion_mrr)}</p>
                          )}
                        </div>
                      </motion.div>
                    ))}
              </div>
            </CardContent>
          </Card>

          {/* Top Churn Risk */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-red-400" />
                Top Churn Risk Accounts
              </CardTitle>
              <CardDescription className="text-xs">Accounts requiring immediate attention</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {loading
                  ? Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="h-10 animate-pulse bg-muted rounded-lg" />
                    ))
                  : topRisk.slice(0, 6).map((acct, i) => (
                      <motion.div
                        key={acct.account_id}
                        custom={i}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="flex items-center justify-between py-1.5 border-b border-border/30 last:border-0"
                      >
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-foreground truncate">{acct.company_name}</p>
                          <p className="text-[10px] text-muted-foreground capitalize">{acct.plan_name} · {acct.region}</p>
                        </div>
                        <div className="text-right shrink-0 ml-2">
                          <p className="text-xs font-semibold text-foreground">{formatMRR(acct.current_mrr)}</p>
                          <div className="flex items-center justify-end gap-1 mt-0.5">
                            <span
                              className={cn(
                                "text-[10px] font-medium px-1.5 py-0.5 rounded-full",
                                acct.risk_level === "critical"
                                  ? "bg-red-500/10 text-red-400"
                                  : "bg-amber-500/10 text-amber-400"
                              )}
                            >
                              {acct.risk_level}
                            </span>
                            {acct.risk_flag_count && (
                              <span className="text-[10px] text-muted-foreground">{acct.risk_flag_count} flags</span>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Net New MRR Summary */}
        {summary && (
          <Card className="bg-gradient-to-r from-brand-500/5 via-transparent to-transparent border-brand-500/20">
            <CardContent className="pt-5">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                {[
                  { label: "New MRR", value: summary.new_mrr, color: "#10b981" },
                  { label: "Expansion", value: summary.expansion_mrr, color: "#3b82f6" },
                  { label: "Reactivation", value: summary.reactivation_mrr, color: "#8b5cf6" },
                  { label: "Contraction", value: -summary.contraction_mrr, color: "#f59e0b" },
                  { label: "Churn", value: -summary.churned_mrr, color: "#ef4444" },
                  { label: "Net New MRR", value: summary.net_new_mrr, color: summary.net_new_mrr >= 0 ? "#10b981" : "#ef4444" },
                ].map((item) => (
                  <div key={item.label} className="text-center">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">{item.label}</p>
                    <p className="text-sm font-bold" style={{ color: item.color }}>
                      {item.value >= 0 ? "+" : ""}{formatMRR(item.value)}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
}
