"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle2,
  Lightbulb, ArrowUpRight, ArrowDownRight, Zap,
} from "lucide-react";
import { StaggerContainer, StaggerChild } from "./SectionWrapper";

const INSIGHTS = [
  {
    type: "positive",
    icon: TrendingUp,
    iconColor: "text-emerald-400",
    iconBg: "bg-emerald-500/10",
    borderColor: "border-emerald-500/15",
    tag: "Revenue Growth",
    tagColor: "text-emerald-400 bg-emerald-500/10",
    headline: "Enterprise plan driving 61% of MRR",
    body: "Enterprise accounts ($2,499+/mo) represent only 18% of your customer base but contribute 61% of total MRR. Expansion MRR from this segment grew 34% last quarter — your highest-value growth lever.",
    metric: "+34%",
    metricLabel: "Enterprise expansion MRR",
    metricPositive: true,
    source: "mart_exec_revenue_summary",
  },
  {
    type: "warning",
    icon: AlertTriangle,
    iconColor: "text-amber-400",
    iconBg: "bg-amber-500/10",
    borderColor: "border-amber-500/15",
    tag: "Churn Risk",
    tagColor: "text-amber-400 bg-amber-500/10",
    headline: "14 accounts show 3+ simultaneous risk flags",
    body: "Usage dropped >40% MoM, seat utilization below 25%, and 2+ unresolved high-priority tickets — all in the same accounts. Combined MRR at risk: $124K. Immediate CSM intervention recommended.",
    metric: "$124K",
    metricLabel: "MRR at risk",
    metricPositive: false,
    source: "fct_account_monthly_health",
  },
  {
    type: "positive",
    icon: CheckCircle2,
    iconColor: "text-blue-400",
    iconBg: "bg-blue-500/10",
    borderColor: "border-blue-500/15",
    tag: "Cohort Retention",
    tagColor: "text-blue-400 bg-blue-500/10",
    headline: "Organic channel cohorts retain 12pp better at M+12",
    body: "Customers acquired through organic search retain at 84% at 12 months vs. 72% for paid channels. Organic cohorts also show 22% higher NRR, suggesting better product-market fit alignment.",
    metric: "+12pp",
    metricLabel: "M+12 retention vs. paid",
    metricPositive: true,
    source: "fct_customer_cohorts",
  },
  {
    type: "negative",
    icon: TrendingDown,
    iconColor: "text-rose-400",
    iconBg: "bg-rose-500/10",
    borderColor: "border-rose-500/15",
    tag: "Funnel Leak",
    tagColor: "text-rose-400 bg-rose-500/10",
    headline: "Cold outbound trials convert at only 18% vs. 52% for referrals",
    body: "Trial-to-paid conversion for cold outbound is 18.2% — less than half the 52.4% rate for referral-sourced trials. Referral trials also engage 3.2x more features during the trial period.",
    metric: "−34pp",
    metricLabel: "vs. referral conversion",
    metricPositive: false,
    source: "fct_sales_conversion",
  },
  {
    type: "positive",
    icon: Zap,
    iconColor: "text-violet-400",
    iconBg: "bg-violet-500/10",
    borderColor: "border-violet-500/15",
    tag: "Product Signal",
    tagColor: "text-violet-400 bg-violet-500/10",
    headline: "Feature adoption breadth predicts 6-month retention",
    body: "Accounts using 5+ features in month 1 retain at 91% at 6 months. Accounts using 1-2 features retain at only 58%. Feature adoption breadth is the single strongest predictor of long-term retention.",
    metric: "91% vs 58%",
    metricLabel: "M+6 retention by feature adoption",
    metricPositive: true,
    source: "fct_account_monthly_health",
  },
  {
    type: "warning",
    icon: AlertTriangle,
    iconColor: "text-orange-400",
    iconBg: "bg-orange-500/10",
    borderColor: "border-orange-500/15",
    tag: "Payment Health",
    tagColor: "text-orange-400 bg-orange-500/10",
    headline: "5.2% invoice failure rate concentrated in Starter plan",
    body: "Invoice failures are 3.4x more common in Starter plan accounts. Accounts with 2+ payment failures in a 90-day window churn at 4.1x the baseline rate. Proactive dunning automation could recover ~$18K/month.",
    metric: "5.2%",
    metricLabel: "Invoice failure rate",
    metricPositive: false,
    source: "stg_invoices",
  },
];

// ─── Insight card ─────────────────────────────────────────────────────────────
function InsightCard({ insight, index }: { insight: (typeof INSIGHTS)[0]; index: number }) {
  const Icon = insight.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay: index * 0.08, ease: "easeOut" }}
      whileHover={{ y: -4 }}
      className={`relative bg-slate-900/60 backdrop-blur-sm border ${insight.borderColor} rounded-2xl p-6 overflow-hidden group cursor-default`}
    >
      {/* Subtle hover glow */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-white/[0.02] to-transparent rounded-2xl" />

      {/* Top row */}
      <div className="relative flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`${insight.iconBg} rounded-xl p-2.5`}>
            <Icon className={`h-4 w-4 ${insight.iconColor}`} strokeWidth={2} />
          </div>
          <span className={`text-[10px] font-semibold px-2.5 py-1 rounded-full ${insight.tagColor}`}>
            {insight.tag}
          </span>
        </div>
        <div className="text-right">
          <p className={`text-lg font-bold ${insight.metricPositive ? "text-emerald-400" : "text-rose-400"}`}>
            {insight.metric}
          </p>
          <div className={`flex items-center justify-end gap-0.5 text-[9px] font-medium ${insight.metricPositive ? "text-emerald-500" : "text-rose-500"}`}>
            {insight.metricPositive ? (
              <ArrowUpRight className="h-3 w-3" />
            ) : (
              <ArrowDownRight className="h-3 w-3" />
            )}
            {insight.metricLabel}
          </div>
        </div>
      </div>

      {/* Headline */}
      <h3 className="relative text-sm font-semibold text-white mb-2.5 leading-snug">
        {insight.headline}
      </h3>

      {/* Body */}
      <p className="relative text-xs text-slate-400 leading-relaxed mb-4">
        {insight.body}
      </p>

      {/* Source tag */}
      <div className="relative flex items-center gap-1.5">
        <div className="h-px flex-1 bg-white/[0.05]" />
        <span className="text-[9px] font-mono text-slate-600 bg-slate-950/60 px-2 py-0.5 rounded">
          {insight.source}
        </span>
      </div>
    </motion.div>
  );
}

// ─── Section ──────────────────────────────────────────────────────────────────
export function InsightsSection() {
  return (
    <section id="insights" className="relative py-28 bg-[#050510] overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-violet-700/4 rounded-full blur-[160px]" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <StaggerContainer className="text-center mb-16">
          <StaggerChild>
            <div className="inline-flex items-center gap-2 bg-slate-800/60 border border-white/[0.06] rounded-full px-4 py-1.5 mb-5">
              <Lightbulb className="h-3.5 w-3.5 text-amber-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Business Insights
              </span>
            </div>
          </StaggerChild>
          <StaggerChild>
            <h2 className="text-4xl sm:text-5xl font-bold text-white tracking-tight mb-5">
              Answers to the questions{" "}
              <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
                that matter
              </span>
            </h2>
          </StaggerChild>
          <StaggerChild>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
              FlowSync Revenue Intelligence surfaces the insights buried in your data —
              from board-level revenue trends to account-level churn signals.
            </p>
          </StaggerChild>
        </StaggerContainer>

        {/* Insights grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {INSIGHTS.map((insight, i) => (
            <InsightCard key={insight.headline} insight={insight} index={i} />
          ))}
        </div>

        {/* Bottom callout */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-12 bg-gradient-to-r from-slate-900/80 via-slate-900/60 to-slate-900/80 border border-white/[0.06] rounded-2xl p-8 text-center"
        >
          <p className="text-sm text-slate-500 mb-2 font-medium">
            All insights derived from synthetic data generated by
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {[
              "300 accounts",
              "24 months history",
              "50,000+ usage events",
              "2,500+ support tickets",
              "1,200 leads",
              "18 dbt models",
            ].map((item) => (
              <span
                key={item}
                className="text-xs font-semibold text-slate-300 bg-slate-800/60 border border-white/[0.06] rounded-full px-3 py-1"
              >
                {item}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
