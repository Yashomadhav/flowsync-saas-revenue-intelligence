"use client";

import React, { useEffect, useState } from "react";
import { TrendingDown, TrendingUp, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { DashboardHeader, PageHeader } from "@/components/layout/DashboardHeader";
import { KPICard, KPICardSkeleton } from "@/components/dashboard/KPICard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { MRRBridgeChart } from "@/components/charts/MRRBridgeChart";
import { WaterfallChart } from "@/components/charts/WaterfallChart";
import { revenueApi, executiveApi } from "@/lib/api";
import { formatMRR, CHART_PALETTE } from "@/lib/formatters";
import type {
  MRRBridgePoint, AccountMovement, WaterfallData, NewMRRByChannel, PaymentTrend,
} from "@/types";
import {
  MOCK_MRR_BRIDGE, MOCK_ACCOUNT_MOVEMENTS, MOCK_WATERFALL,
  MOCK_NEW_MRR_BY_CHANNEL, MOCK_PAYMENT_TRENDS,
} from "@/lib/mock-data";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
  LineChart, Line, Legend,
} from "recharts";
import { cn } from "@/lib/utils";

const MOVEMENT_BADGE: Record<string, string> = {
  new: "bg-emerald-500/10 text-emerald-400",
  expansion: "bg-blue-500/10 text-blue-400",
  reactivation: "bg-violet-500/10 text-violet-400",
  contraction: "bg-amber-500/10 text-amber-400",
  churn: "bg-red-500/10 text-red-400",
  existing: "bg-muted text-muted-foreground",
};

const MOVEMENT_LABELS: Record<string, string> = {
  new: "New", expansion: "Expansion", reactivation: "Reactivation",
  contraction: "Contraction", churn: "Churn", existing: "Existing",
};

// Aggregate NewMRRByChannel[] by channel for bar chart
function aggregateByChannel(data: NewMRRByChannel[]) {
  const map = new Map<string, { channel: string; total_mrr: number; accounts: number }>();
  data.forEach((d) => {
    const key = d.acquisition_channel;
    const existing = map.get(key) ?? { channel: key, total_mrr: 0, accounts: 0 };
    map.set(key, {
      channel: key,
      total_mrr: existing.total_mrr + d.new_mrr,
      accounts: existing.accounts + d.new_accounts,
    });
  });
  return Array.from(map.values()).sort((a, b) => b.total_mrr - a.total_mrr);
}

export default function RevenueMovementsPage() {
  const [bridge, setBridge] = useState<MRRBridgePoint[]>([]);
  const [movements, setMovements] = useState<AccountMovement[]>([]);
  const [waterfall, setWaterfall] = useState<WaterfallData | null>(null);
  const [byChannel, setByChannel] = useState<NewMRRByChannel[]>([]);
  const [paymentTrends, setPaymentTrends] = useState<PaymentTrend[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [b, mResp, w, c, p] = await Promise.all([
          revenueApi.getMRRBridge(),
          revenueApi.getAccountMovements(),
          executiveApi.getWaterfall(),
          revenueApi.getNewMRRByChannel(),
          revenueApi.getPaymentTrends(),
        ]);
        setBridge(b);
        setMovements(mResp.data);
        setWaterfall(w);
        setByChannel(c);
        setPaymentTrends(p);
      } catch {
        setBridge(MOCK_MRR_BRIDGE as any);
        setMovements(MOCK_ACCOUNT_MOVEMENTS as any);
        setWaterfall(MOCK_WATERFALL as any);
        setByChannel(MOCK_NEW_MRR_BY_CHANNEL as any);
        setPaymentTrends(MOCK_PAYMENT_TRENDS as any);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const latest = bridge[bridge.length - 1];
  const channelAgg = aggregateByChannel(byChannel);

  return (
    <>
      <DashboardHeader
        title="Revenue Movements"
        description="MRR bridge, account-level movements, and payment trends"
      />
      <div className="p-6 space-y-6">
        <PageHeader
          title="Revenue Movements"
          description="Understand where MRR is coming from and where it's going"
        />

        {/* KPI Row */}
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {loading ? (
            Array.from({ length: 5 }).map((_, i) => <KPICardSkeleton key={i} />)
          ) : (
            <>
              <KPICard title="New MRR" value={latest?.new_mrr ?? 0} format="currency" icon={ArrowUpRight} iconColor="text-emerald-400" index={0} />
              <KPICard title="Expansion MRR" value={latest?.expansion_mrr ?? 0} format="currency" icon={TrendingUp} iconColor="text-blue-400" index={1} />
              <KPICard title="Reactivation MRR" value={latest?.reactivation_mrr ?? 0} format="currency" icon={TrendingUp} iconColor="text-violet-400" index={2} />
              <KPICard title="Contraction MRR" value={latest?.contraction_mrr ?? 0} format="currency" icon={TrendingDown} iconColor="text-amber-400" invertDelta index={3} />
              <KPICard title="Churned MRR" value={latest?.churned_mrr ?? 0} format="currency" icon={ArrowDownRight} iconColor="text-red-400" invertDelta index={4} />
            </>
          )}
        </div>

        {/* MRR Bridge Chart */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">MRR Bridge by Month</CardTitle>
            <CardDescription className="text-xs">Monthly breakdown of new, expansion, reactivation, contraction, and churn MRR</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? <div className="h-[300px] animate-pulse bg-muted rounded-lg" /> : <MRRBridgeChart data={bridge} height={300} />}
          </CardContent>
        </Card>

        {/* Waterfall + Channel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Current Month Waterfall</CardTitle>
              <CardDescription className="text-xs">MRR movement breakdown for the current period</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[280px] animate-pulse bg-muted rounded-lg" />
              ) : waterfall ? (
                <WaterfallChart data={waterfall.waterfall} height={280} />
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">New MRR by Acquisition Channel</CardTitle>
              <CardDescription className="text-xs">Cumulative new revenue contribution by channel</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[280px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={channelAgg} layout="vertical" margin={{ top: 5, right: 20, left: 100, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} horizontal={false} />
                    <XAxis type="number" tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="channel" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} width={100} />
                    <Tooltip formatter={(v: number) => formatMRR(v)} contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }} />
                    <Bar dataKey="total_mrr" name="New MRR" radius={[0, 4, 4, 0]}>
                      {channelAgg.map((_, i) => (
                        <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} opacity={0.85} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Payment Trends */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Invoice & Payment Trends</CardTitle>
            <CardDescription className="text-xs">Monthly invoice success vs failure rates</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-[240px] animate-pulse bg-muted rounded-lg" />
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={paymentTrends} margin={{ top: 5, right: 20, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
                  <XAxis dataKey="month" tickFormatter={(v: string) => v.slice(0, 7)} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="left" tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} width={55} />
                  <YAxis yAxisId="right" orientation="right" tickFormatter={(v: number) => `${v.toFixed(0)}%`} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} width={40} />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line yAxisId="left" type="monotone" dataKey="paid_amount" name="Paid" stroke="#10b981" strokeWidth={2} dot={false} />
                  <Line yAxisId="left" type="monotone" dataKey="failed_amount" name="Failed" stroke="#ef4444" strokeWidth={2} dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="failure_rate_pct" name="Failure %" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Account Movement Table */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Account-Level Movements</CardTitle>
            <CardDescription className="text-xs">Individual account MRR changes — {movements.length} accounts</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-10 animate-pulse bg-muted rounded-lg" />)}</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Company</th>
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Plan</th>
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Channel</th>
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Movement</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Prev MRR</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Curr MRR</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Δ MRR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {movements.slice(0, 20).map((m: AccountMovement, i: number) => (
                      <tr key={`${m.account_id}-${i}`} className="border-b border-border/20 hover:bg-muted/30 transition-colors">
                        <td className="py-2 px-3 font-medium text-foreground">{m.company_name}</td>
                        <td className="py-2 px-3 text-muted-foreground capitalize">{m.plan_name}</td>
                        <td className="py-2 px-3 text-muted-foreground text-[10px]">{m.acquisition_channel}</td>
                        <td className="py-2 px-3">
                          <span className={cn("px-2 py-0.5 rounded-full text-[10px] font-medium capitalize", MOVEMENT_BADGE[m.movement_type] ?? "bg-muted text-muted-foreground")}>
                            {MOVEMENT_LABELS[m.movement_type] ?? m.movement_type}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right text-muted-foreground">{m.previous_mrr ? formatMRR(m.previous_mrr) : "—"}</td>
                        <td className="py-2 px-3 text-right font-medium text-foreground">{m.current_mrr ? formatMRR(m.current_mrr) : "—"}</td>
                        <td className={cn("py-2 px-3 text-right font-semibold", m.mrr_delta > 0 ? "text-emerald-400" : m.mrr_delta < 0 ? "text-red-400" : "text-muted-foreground")}>
                          {m.mrr_delta > 0 ? "+" : ""}{formatMRR(m.mrr_delta)}
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
