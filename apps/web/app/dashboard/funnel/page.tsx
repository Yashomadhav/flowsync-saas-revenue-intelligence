"use client";

import React, { useEffect, useState } from "react";
import { Target, TrendingUp, Clock, Zap } from "lucide-react";
import { DashboardHeader, PageHeader } from "@/components/layout/DashboardHeader";
import { KPICard, KPICardSkeleton } from "@/components/dashboard/KPICard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FunnelViz, ConversionByChannelChart } from "@/components/charts/FunnelChart";
import { funnelApi } from "@/lib/api";
import { formatMRR, formatPercent, CHART_PALETTE } from "@/lib/formatters";
import type {
  FunnelConversion, ConversionByChannel, SalesCycle, ExpansionBySegment,
} from "@/types";
import {
  MOCK_FUNNEL, MOCK_CONVERSION_BY_CHANNEL, MOCK_SALES_CYCLE, MOCK_EXPANSION_BY_SEGMENT,
} from "@/lib/mock-data";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from "recharts";

export default function FunnelGrowthPage() {
  const [funnel, setFunnel] = useState<FunnelConversion | null>(null);
  const [byChannel, setByChannel] = useState<ConversionByChannel[]>([]);
  const [salesCycle, setSalesCycle] = useState<SalesCycle[]>([]);
  const [expansion, setExpansion] = useState<ExpansionBySegment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [f, c, s, e] = await Promise.all([
          funnelApi.getConversion(),
          funnelApi.getConversionByChannel(),
          funnelApi.getSalesCycle(),
          funnelApi.getExpansionBySegment(),
        ]);
        setFunnel(f);
        setByChannel(c);
        setSalesCycle(s);
        setExpansion(e);
      } catch {
        setFunnel(MOCK_FUNNEL as any);
        setByChannel(MOCK_CONVERSION_BY_CHANNEL as any);
        setSalesCycle(MOCK_SALES_CYCLE as any);
        setExpansion(MOCK_EXPANSION_BY_SEGMENT as any);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Aggregate expansion by company_size for bar chart
  const expansionBySize = expansion.reduce<Record<string, number>>(
    (acc: Record<string, number>, e: ExpansionBySegment) => {
      acc[e.company_size] = (acc[e.company_size] ?? 0) + e.total_expansion_mrr;
      return acc;
    }, {}
  );
  const expansionChartData = (Object.entries(expansionBySize) as [string, number][]).map(([size, mrr]) => ({
    segment: size,
    expansion_mrr: mrr,
  }));

  // Sales cycle by channel (deduplicate, take avg)
  type CycleAcc = Record<string, { total: number; count: number }>;
  const salesByChannel = salesCycle.reduce<CycleAcc>(
    (acc: CycleAcc, s: SalesCycle) => {
      const key = s.channel;
      const existing: { total: number; count: number } = acc[key] ?? { total: 0, count: 0 };
      acc[key] = { total: existing.total + s.avg_days, count: existing.count + 1 };
      return acc;
    }, {}
  );
  const salesCycleChartData = (Object.entries(salesByChannel) as [string, { total: number; count: number }][]).map(([channel, val]) => ({
    channel,
    avg_days: val.total / val.count,
  }));

  const totalExpansionMRR = expansion.reduce((s: number, e: ExpansionBySegment) => s + e.total_expansion_mrr, 0);

  return (
    <>
      <DashboardHeader
        title="Funnel & Growth"
        description="Lead-to-paid conversion, sales cycle, and expansion revenue"
      />
      <div className="p-6 space-y-6">
        <PageHeader
          title="Funnel & Growth"
          description="Track conversion from lead to trial to paid customer"
        />

        {/* KPI Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => <KPICardSkeleton key={i} />)
          ) : (
            <>
              <KPICard
                title="Lead → Trial Rate"
                value={formatPercent(funnel ? funnel.lead_to_trial_rate : 0)}
                icon={Target}
                iconColor="text-blue-400"
                index={0}
              />
              <KPICard
                title="Trial → Paid Rate"
                value={formatPercent(funnel ? funnel.trial_to_paid_rate : 0)}
                icon={Zap}
                iconColor="text-emerald-400"
                index={1}
              />
              <KPICard
                title="Avg Sales Cycle"
                value={`${funnel?.avg_days_to_convert?.toFixed(0) ?? "—"}d`}
                icon={Clock}
                iconColor="text-amber-400"
                index={2}
              />
              <KPICard
                title="Total Expansion MRR"
                value={totalExpansionMRR}
                format="currency"
                icon={TrendingUp}
                iconColor="text-violet-400"
                index={3}
              />
            </>
          )}
        </div>

        {/* Funnel Visualization + Channel Conversion */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Lead → Trial → Paid Funnel</CardTitle>
              <CardDescription className="text-xs">Overall conversion funnel with stage-by-stage drop-off rates</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[260px] animate-pulse bg-muted rounded-lg" />
              ) : funnel ? (
                <FunnelViz data={funnel} />
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Trial → Paid Rate by Channel</CardTitle>
              <CardDescription className="text-xs">Conversion rate from trial to paid per acquisition channel</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[260px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <ConversionByChannelChart data={byChannel} height={260} />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sales Cycle + Expansion by Segment */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Sales Cycle Duration by Channel</CardTitle>
              <CardDescription className="text-xs">Average days from lead to paid conversion per channel</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[220px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={salesCycleChartData} margin={{ top: 5, right: 20, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
                    <XAxis
                      dataKey="channel"
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tickFormatter={(v: number) => `${v.toFixed(0)}d`}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                      width={40}
                    />
                    <Tooltip
                      formatter={(v: number) => [`${v.toFixed(0)} days`, "Avg Sales Cycle"]}
                      contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }}
                    />
                    <Bar dataKey="avg_days" name="Avg Days" radius={[4, 4, 0, 0]}>
                      {salesCycleChartData.map((_, i) => (
                        <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} opacity={0.85} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Expansion MRR by Company Size</CardTitle>
              <CardDescription className="text-xs">Revenue expansion broken down by company size segment</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[220px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={expansionChartData} margin={{ top: 5, right: 20, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
                    <XAxis
                      dataKey="segment"
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      axisLine={false}
                      tickLine={false}
                      width={50}
                    />
                    <Tooltip
                      formatter={(v: number) => [formatMRR(v), "Expansion MRR"]}
                      contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }}
                    />
                    <Bar dataKey="expansion_mrr" name="Expansion MRR" radius={[4, 4, 0, 0]}>
                      {expansionChartData.map((_, i) => (
                        <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} opacity={0.85} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Channel Performance Summary Table */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Channel Performance Summary</CardTitle>
            <CardDescription className="text-xs">Key conversion metrics per acquisition channel</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-8 animate-pulse bg-muted rounded-lg" />)}</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Channel</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Leads</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Trial Starts</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Paid</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Trial→Paid</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Avg Days</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Avg 1st MRR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {byChannel.map((c: ConversionByChannel, i: number) => (
                      <tr key={i} className="border-b border-border/20 hover:bg-muted/30 transition-colors">
                        <td className="py-2 px-3 font-medium text-foreground">{c.channel}</td>
                        <td className="py-2 px-3 text-right text-muted-foreground">{c.total_leads.toLocaleString()}</td>
                        <td className="py-2 px-3 text-right text-muted-foreground">{c.trial_starts.toLocaleString()}</td>
                        <td className="py-2 px-3 text-right text-muted-foreground">{c.paid_conversions.toLocaleString()}</td>
                        <td className="py-2 px-3 text-right">
                          <span className={
                            c.trial_to_paid_rate >= 40 ? "text-emerald-400 font-semibold" :
                            c.trial_to_paid_rate >= 20 ? "text-amber-400" : "text-red-400"
                          }>
                            {formatPercent(c.trial_to_paid_rate)}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right text-muted-foreground">{c.avg_days_to_convert.toFixed(0)}d</td>
                        <td className="py-2 px-3 text-right font-medium text-foreground">{formatMRR(c.avg_first_month_mrr)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Expansion Detail Table */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Expansion Revenue Detail</CardTitle>
            <CardDescription className="text-xs">Expansion MRR breakdown by segment, channel, and plan</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-8 animate-pulse bg-muted rounded-lg" />)}</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Company Size</th>
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Channel</th>
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Plan</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Expanding Accounts</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Total Expansion MRR</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Avg per Account</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expansion
                      .sort((a: ExpansionBySegment, b: ExpansionBySegment) => b.total_expansion_mrr - a.total_expansion_mrr)
                      .slice(0, 15)
                      .map((e: ExpansionBySegment, i: number) => (
                        <tr key={i} className="border-b border-border/20 hover:bg-muted/30 transition-colors">
                          <td className="py-2 px-3 text-foreground capitalize">{e.company_size}</td>
                          <td className="py-2 px-3 text-muted-foreground text-[10px]">{e.acquisition_channel}</td>
                          <td className="py-2 px-3 text-muted-foreground capitalize">{e.plan_name}</td>
                          <td className="py-2 px-3 text-right text-muted-foreground">{e.expanding_accounts}</td>
                          <td className="py-2 px-3 text-right font-semibold text-emerald-400">{formatMRR(e.total_expansion_mrr)}</td>
                          <td className="py-2 px-3 text-right text-muted-foreground">{formatMRR(e.avg_expansion_per_account)}</td>
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
