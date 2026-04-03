"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  TrendingUp, TrendingDown, Users, GitBranch,
  HeartPulse, BarChart3, ArrowUpRight, ArrowDownRight,
} from "lucide-react";
import { StaggerContainer, StaggerChild } from "./SectionWrapper";
import { AnimatedCounter } from "./AnimatedCounter";

const METRICS = [
  {
    icon: TrendingUp,
    iconBg: "bg-violet-500/10",
    iconColor: "text-violet-400",
    borderColor: "border-violet-500/15",
    glowColor: "from-violet-600/8",
    title: "MRR & ARR Tracking",
    description:
      "Know your Monthly and Annual Recurring Revenue to the dollar. Track new, expansion, contraction, churn, and reactivation movements every month.",
    stat: "$847K",
    statLabel: "Current MRR",
    statDelta: "+12.4%",
    statDeltaPositive: true,
    detail: "Net New MRR = New + Expansion + Reactivation − Contraction − Churn",
  },
  {
    icon: TrendingDown,
    iconBg: "bg-amber-500/10",
    iconColor: "text-amber-400",
    borderColor: "border-amber-500/15",
    glowColor: "from-amber-600/8",
    title: "Churn Analysis",
    description:
      "Separate logo churn from revenue churn. Identify which plans, segments, and cohorts are churning — and why — before it becomes a crisis.",
    stat: "2.1%",
    statLabel: "Logo Churn Rate",
    statDelta: "−0.4pp",
    statDeltaPositive: true,
    detail: "Revenue Churn = (Churned MRR + Contraction) / Starting MRR",
  },
  {
    icon: Users,
    iconBg: "bg-emerald-500/10",
    iconColor: "text-emerald-400",
    borderColor: "border-emerald-500/15",
    glowColor: "from-emerald-600/8",
    title: "Cohort Retention",
    description:
      "See exactly which customer cohorts retain best at 3, 6, and 12 months. Compare retention by plan, company size, industry, and acquisition channel.",
    stat: "118%",
    statLabel: "Net Revenue Retention",
    statDelta: "+3.2pp",
    statDeltaPositive: true,
    detail: "NRR = (Starting MRR + Expansion − Contraction − Churn) / Starting MRR",
  },
  {
    icon: GitBranch,
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-400",
    borderColor: "border-blue-500/15",
    glowColor: "from-blue-600/8",
    title: "Funnel Conversion",
    description:
      "Track every step from lead to trial to paid. Measure conversion rates by channel, sales cycle duration, and trial engagement to optimize growth.",
    stat: "40.4%",
    statLabel: "Trial-to-Paid Rate",
    statDelta: "+5.1pp",
    statDeltaPositive: true,
    detail: "Overall Conversion = Paid / Total Leads × 100",
  },
  {
    icon: HeartPulse,
    iconBg: "bg-rose-500/10",
    iconColor: "text-rose-400",
    borderColor: "border-rose-500/15",
    glowColor: "from-rose-600/8",
    title: "Customer Health Scoring",
    description:
      "Composite health score from usage frequency, seat utilization, feature adoption, support burden, CSAT, and payment history — updated monthly.",
    stat: "82",
    statLabel: "Avg Health Score",
    statDelta: "14 at risk",
    statDeltaPositive: false,
    detail: "Risk flags: usage drop >40%, no login 14d, 2+ unresolved tickets",
  },
];

// ─── Metric card ──────────────────────────────────────────────────────────────
function MetricCard({
  icon: Icon,
  iconBg,
  iconColor,
  borderColor,
  glowColor,
  title,
  description,
  stat,
  statLabel,
  statDelta,
  statDeltaPositive,
  detail,
}: (typeof METRICS)[0]) {
  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`relative group bg-slate-900/60 backdrop-blur-sm border ${borderColor} rounded-2xl p-6 overflow-hidden cursor-default`}
    >
      {/* Hover glow */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${glowColor} to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl`}
      />

      {/* Top row: icon + stat */}
      <div className="relative flex items-start justify-between mb-4">
        <div className={`${iconBg} rounded-xl p-2.5`}>
          <Icon className={`h-5 w-5 ${iconColor}`} strokeWidth={2} />
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-white tracking-tight">{stat}</p>
          <p className="text-[10px] text-slate-500 font-medium">{statLabel}</p>
          <div
            className={`flex items-center justify-end gap-0.5 text-[10px] font-semibold mt-0.5 ${
              statDeltaPositive ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {statDeltaPositive ? (
              <ArrowUpRight className="h-3 w-3" />
            ) : (
              <ArrowDownRight className="h-3 w-3" />
            )}
            {statDelta}
          </div>
        </div>
      </div>

      {/* Title */}
      <h3 className="relative text-base font-semibold text-white mb-2 tracking-tight">
        {title}
      </h3>

      {/* Description */}
      <p className="relative text-sm text-slate-400 leading-relaxed mb-4">
        {description}
      </p>

      {/* Formula / detail */}
      <div className="relative bg-slate-950/60 border border-white/[0.05] rounded-lg px-3 py-2">
        <p className="text-[10px] text-slate-500 font-mono leading-relaxed">{detail}</p>
      </div>
    </motion.div>
  );
}

// ─── Animated stats row ───────────────────────────────────────────────────────
const STATS = [
  { value: 847, prefix: "$", suffix: "K", label: "Monthly Recurring Revenue", decimals: 0 },
  { value: 118.4, prefix: "", suffix: "%", label: "Net Revenue Retention", decimals: 1 },
  { value: 300, prefix: "", suffix: "+", label: "Tracked Accounts", decimals: 0 },
  { value: 40.4, prefix: "", suffix: "%", label: "Trial-to-Paid Conversion", decimals: 1 },
];

// ─── Section ──────────────────────────────────────────────────────────────────
export function WhyItMatters() {
  return (
    <section id="why" className="relative py-28 bg-slate-950 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-violet-700/5 rounded-full blur-[120px]" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <StaggerContainer className="text-center mb-16">
          <StaggerChild>
            <div className="inline-flex items-center gap-2 bg-slate-800/60 border border-white/[0.06] rounded-full px-4 py-1.5 mb-5">
              <BarChart3 className="h-3.5 w-3.5 text-violet-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Core Metrics
              </span>
            </div>
          </StaggerChild>
          <StaggerChild>
            <h2 className="text-4xl sm:text-5xl font-bold text-white tracking-tight mb-5">
              Every metric that{" "}
              <span className="bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
                drives SaaS growth
              </span>
            </h2>
          </StaggerChild>
          <StaggerChild>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
              FlowSync Revenue Intelligence answers the questions that matter most —
              from board-level ARR to account-level churn risk signals.
            </p>
          </StaggerChild>
        </StaggerContainer>

        {/* Animated stats bar */}
        <StaggerContainer
          className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-white/[0.04] rounded-2xl overflow-hidden border border-white/[0.06] mb-16"
          staggerDelay={0.08}
        >
          {STATS.map((s) => (
            <StaggerChild key={s.label}>
              <div className="bg-slate-900/80 px-6 py-6 text-center hover:bg-slate-900/95 transition-colors duration-200">
                <p className="text-3xl font-bold text-white tracking-tight mb-1">
                  <AnimatedCounter
                    value={s.value}
                    prefix={s.prefix}
                    suffix={s.suffix}
                    decimals={s.decimals}
                    duration={2000}
                  />
                </p>
                <p className="text-xs text-slate-500 font-medium">{s.label}</p>
              </div>
            </StaggerChild>
          ))}
        </StaggerContainer>

        {/* Metric cards grid */}
        <StaggerContainer
          className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5"
          staggerDelay={0.1}
        >
          {METRICS.map((metric) => (
            <StaggerChild key={metric.title}>
              <MetricCard {...metric} />
            </StaggerChild>
          ))}

          {/* Sixth card: summary CTA */}
          <StaggerChild>
            <motion.div
              whileHover={{ y: -4, scale: 1.01 }}
              transition={{ duration: 0.25 }}
              className="relative bg-gradient-to-br from-violet-600/20 via-indigo-600/15 to-blue-600/10 border border-violet-500/20 rounded-2xl p-6 flex flex-col justify-between overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-violet-600/5 to-transparent" />
              <div className="relative">
                <div className="bg-white/10 rounded-xl p-2.5 w-fit mb-4">
                  <BarChart3 className="h-5 w-5 text-white" strokeWidth={2} />
                </div>
                <h3 className="text-base font-semibold text-white mb-2 tracking-tight">
                  5 Dashboard Pages
                </h3>
                <p className="text-sm text-slate-300 leading-relaxed mb-6">
                  Executive Overview, Revenue Movements, Cohort Retention, Customer
                  Health, and Funnel & Growth — all in one platform.
                </p>
              </div>
              <div className="relative grid grid-cols-2 gap-2">
                {[
                  "Executive Overview",
                  "Revenue Movements",
                  "Cohort Retention",
                  "Customer Health",
                  "Funnel & Growth",
                  "+ More",
                ].map((page) => (
                  <div
                    key={page}
                    className="bg-white/10 rounded-lg px-2.5 py-1.5 text-[10px] font-medium text-slate-200 text-center"
                  >
                    {page}
                  </div>
                ))}
              </div>
            </motion.div>
          </StaggerChild>
        </StaggerContainer>
      </div>
    </section>
  );
}
