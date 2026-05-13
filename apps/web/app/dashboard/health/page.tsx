"use client";

import React, { useEffect, useState } from "react";
import { AlertTriangle, Shield, Activity, Users, XCircle, CheckCircle } from "lucide-react";
import { DashboardHeader, PageHeader } from "@/components/layout/DashboardHeader";
import { KPICard, KPICardSkeleton } from "@/components/dashboard/KPICard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { healthApi } from "@/lib/api";
import { formatMRR, formatPercent, formatScore, RISK_COLORS } from "@/lib/formatters";
import type {
  HealthScoreBucket, RiskQuadrantAccount, SupportBurden, HealthSummaryStats,
} from "@/types";
import {
  MOCK_HEALTH_DISTRIBUTION, MOCK_RISK_QUADRANT, MOCK_SUPPORT_BURDEN, MOCK_HEALTH_STATS,
} from "@/lib/mock-data";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
  ScatterChart, Scatter, ZAxis, ReferenceLine,
} from "recharts";
import { cn } from "@/lib/utils";

const RISK_BADGE: Record<string, string> = {
  healthy: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  at_risk: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  critical: "bg-red-500/10 text-red-400 border border-red-500/20",
};

const RISK_DOT: Record<string, string> = {
  healthy: "#10b981",
  at_risk: "#f59e0b",
  critical: "#ef4444",
};

const FLAG_LABELS: Array<{ key: keyof RiskQuadrantAccount; label: string }> = [
  { key: "flag_usage_drop", label: "Usage Drop" },
  { key: "flag_no_login", label: "No Login 14d" },
  { key: "flag_open_tickets", label: "Open Tickets" },
  { key: "flag_payment_failure", label: "Payment Fail" },
  { key: "flag_low_csat", label: "Low CSAT" },
  { key: "flag_low_seat_util", label: "Low Seat Util" },
];

export default function CustomerHealthPage() {
  const [distribution, setDistribution] = useState<HealthScoreBucket[]>([]);
  const [quadrant, setQuadrant] = useState<RiskQuadrantAccount[]>([]);
  const [support, setSupport] = useState<SupportBurden[]>([]);
  const [stats, setStats] = useState<HealthSummaryStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [d, q, s, st] = await Promise.all([
          healthApi.getScoreDistribution(),
          healthApi.getRiskQuadrant(),
          healthApi.getSupportBurden(),
          healthApi.getSummaryStats(),
        ]);
        setDistribution(d);
        setQuadrant(q);
        setSupport(s);
        setStats(st);
      } catch {
        setDistribution(MOCK_HEALTH_DISTRIBUTION as any);
        setQuadrant(MOCK_RISK_QUADRANT as any);
        setSupport(MOCK_SUPPORT_BURDEN as any);
        setStats(MOCK_HEALTH_STATS as any);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const riskyAccounts = quadrant.filter((a) => a.risk_level !== "healthy");
  const criticalAccounts = quadrant.filter((a) => a.risk_level === "critical");

  // Scatter data: x=usage_score, y=health_score, z=current_mrr
  const scatterData = quadrant.map((a) => ({
    x: a.usage_score,
    y: a.health_score,
    z: a.current_mrr,
    name: a.company_name,
    risk: a.risk_level,
    mrr: a.current_mrr,
  }));

  return (
    <>
      <DashboardHeader
        title="Customer Health & Churn Risk"
        description="Health scores, risk flags, and support burden analysis"
      />
      <div className="p-6 space-y-6">
        <PageHeader
          title="Customer Health & Churn Risk"
          description="Identify at-risk accounts before they churn"
          badge={criticalAccounts.length > 0 ? `${criticalAccounts.length} Critical` : undefined}
        />

        {/* KPI Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => <KPICardSkeleton key={i} />)
          ) : (
            <>
              <KPICard
                title="Avg Health Score"
                value={formatScore(stats?.avg_health_score ?? 0)}
                icon={Activity}
                iconColor={stats && stats.avg_health_score >= 75 ? "text-emerald-400" : stats && stats.avg_health_score >= 50 ? "text-amber-400" : "text-red-400"}
                index={0}
              />
              <KPICard
                title="At-Risk Accounts"
                value={stats?.at_risk_count ?? 0}
                format="number"
                icon={AlertTriangle}
                iconColor="text-amber-400"
                subtitle={`${formatMRR(stats?.at_risk_mrr ?? 0)} at risk`}
                index={1}
              />
              <KPICard
                title="Critical Accounts"
                value={stats?.critical_count ?? 0}
                format="number"
                icon={XCircle}
                iconColor="text-red-400"
                index={2}
              />
              <KPICard
                title="Healthy Accounts"
                value={stats?.healthy_count ?? 0}
                format="number"
                icon={Shield}
                iconColor="text-emerald-400"
                subtitle={`${stats ? formatPercent((stats.healthy_count / stats.total_accounts) * 100) : "—"} of total`}
                index={3}
              />
            </>
          )}
        </div>

        {/* Health Score Distribution + Risk Quadrant */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Health Score Distribution</CardTitle>
              <CardDescription className="text-xs">Account count by health score bucket (0–100)</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[240px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={distribution} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
                    <XAxis dataKey="score_bucket" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} width={35} />
                    <Tooltip
                      contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }}
                      formatter={(v: number, _: string, props: any) => [v, `Accounts (avg: ${props.payload.avg_score?.toFixed(0)})`]}
                    />
                    <Bar dataKey="account_count" name="Accounts" radius={[4, 4, 0, 0]}>
                      {distribution.map((entry, i) => {
                        const score = entry.avg_score;
                        const color = score >= 75 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
                        return <Cell key={i} fill={color} opacity={0.85} />;
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Churn Risk Quadrant</CardTitle>
              <CardDescription className="text-xs">Usage score vs health score — bubble size = MRR</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-[240px] animate-pulse bg-muted rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <ScatterChart margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} />
                    <XAxis type="number" dataKey="x" name="Usage Score" domain={[0, 100]} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} label={{ value: "Usage Score", position: "insideBottom", offset: -5, fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis type="number" dataKey="y" name="Health Score" domain={[0, 100]} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} width={35} label={{ value: "Health", angle: -90, position: "insideLeft", fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                    <ZAxis type="number" dataKey="z" range={[20, 200]} />
                    <ReferenceLine x={50} stroke="hsl(var(--border))" strokeDasharray="4 2" />
                    <ReferenceLine y={50} stroke="hsl(var(--border))" strokeDasharray="4 2" />
                    <Tooltip
                      cursor={{ strokeDasharray: "3 3" }}
                      contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 11 }}
                      formatter={(v: number, name: string) => name === "z" ? formatMRR(v) : v.toFixed(0)}
                    />
                    {["healthy", "at_risk", "critical"].map((risk) => (
                      <Scatter
                        key={risk}
                        name={risk}
                        data={scatterData.filter((d) => d.risk === risk)}
                        fill={RISK_DOT[risk]}
                        opacity={0.7}
                      />
                    ))}
                  </ScatterChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Risky Accounts Table */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              At-Risk & Critical Accounts
            </CardTitle>
            <CardDescription className="text-xs">
              {riskyAccounts.length} accounts with active risk flags — sorted by MRR at risk
            </CardDescription>
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
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">MRR</th>
                      <th className="text-center py-2 px-3 text-muted-foreground font-medium">Health</th>
                      <th className="text-center py-2 px-3 text-muted-foreground font-medium">Risk</th>
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Risk Flags</th>
                    </tr>
                  </thead>
                  <tbody>
                    {riskyAccounts
                      .sort((a, b) => b.current_mrr - a.current_mrr)
                      .slice(0, 20)
                      .map((acct: RiskQuadrantAccount, i: number) => (
                        <tr key={`${acct.account_id}-${i}`} className="border-b border-border/20 hover:bg-muted/30 transition-colors">
                          <td className="py-2 px-3">
                            <p className="font-medium text-foreground">{acct.company_name}</p>
                            <p className="text-[10px] text-muted-foreground">{acct.company_size} · {acct.region}</p>
                          </td>
                          <td className="py-2 px-3 text-muted-foreground capitalize">{acct.plan_name}</td>
                          <td className="py-2 px-3 text-right font-semibold text-foreground">{formatMRR(acct.current_mrr)}</td>
                          <td className="py-2 px-3 text-center">
                            <span className={cn("font-bold text-sm", acct.health_score >= 75 ? "text-emerald-400" : acct.health_score >= 50 ? "text-amber-400" : "text-red-400")}>
                              {acct.health_score.toFixed(0)}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center">
                            <span className={cn("px-2 py-0.5 rounded-full text-[10px] font-medium capitalize", RISK_BADGE[acct.risk_level])}>
                              {acct.risk_level.replace("_", " ")}
                            </span>
                          </td>
                          <td className="py-2 px-3">
                            <div className="flex flex-wrap gap-1">
                              {FLAG_LABELS.filter((f) => acct[f.key] === true).map((f) => (
                                <span key={f.key} className="px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 text-[9px] font-medium border border-red-500/20">
                                  {f.label}
                                </span>
                              ))}
                            </div>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Support Burden */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Support Burden by Account</CardTitle>
            <CardDescription className="text-xs">Accounts with highest support ticket volume and open issues</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-10 animate-pulse bg-muted rounded-lg" />)}</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Company</th>
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Plan</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Total Tickets</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">High Priority</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Open</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Avg CSAT</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Avg Resolve (h)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {support.slice(0, 15).map((s: SupportBurden, i: number) => (
                      <tr key={`${s.account_id}-${i}`} className="border-b border-border/20 hover:bg-muted/30 transition-colors">
                        <td className="py-2 px-3 font-medium text-foreground">{s.company_name}</td>
                        <td className="py-2 px-3 text-muted-foreground capitalize">{s.plan_name}</td>
                        <td className="py-2 px-3 text-right text-foreground">{s.total_tickets}</td>
                        <td className="py-2 px-3 text-right">
                          <span className={s.high_priority_tickets > 2 ? "text-red-400 font-semibold" : "text-muted-foreground"}>
                            {s.high_priority_tickets}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right">
                          <span className={s.open_tickets > 0 ? "text-amber-400 font-semibold" : "text-muted-foreground"}>
                            {s.open_tickets}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right">
                          <span className={s.avg_csat < 3 ? "text-red-400 font-semibold" : s.avg_csat < 4 ? "text-amber-400" : "text-emerald-400"}>
                            {s.avg_csat.toFixed(1)}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right text-muted-foreground">{s.avg_resolution_hours.toFixed(0)}h</td>
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
