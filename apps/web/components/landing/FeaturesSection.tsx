"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, TrendingUp, Users, HeartPulse,
  GitBranch, ArrowRight, CheckCircle2, Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StaggerContainer, StaggerChild } from "./SectionWrapper";

const FEATURES = [
  {
    id: "executive",
    icon: LayoutDashboard,
    label: "Executive Overview",
    href: "/dashboard",
    color: "violet",
    accentClass: "text-violet-400",
    bgClass: "bg-violet-500/10",
    borderClass: "border-violet-500/20",
    activeBg: "bg-violet-500/15",
    gradientClass: "from-violet-600/20 to-violet-600/5",
    headline: "Board-Ready Revenue Snapshot",
    description:
      "A single pane of glass for your most critical SaaS metrics. MRR, ARR, NRR, churn rate, and active accounts — all with trend indicators and period-over-period deltas.",
    bullets: [
      "KPI cards: MRR, ARR, NRR, Logo Churn, Active Accounts",
      "MRR trend line chart (12-month rolling)",
      "Revenue waterfall: new → expansion → contraction → churn",
      "Revenue breakdown by plan, region, and company size",
      "Top expanding accounts & top churn-risk accounts",
    ],
    preview: {
      kpis: [
        { l: "MRR", v: "$847K", c: "text-violet-400", delta: "+12.4%" },
        { l: "ARR", v: "$10.2M", c: "text-indigo-400", delta: "+12.4%" },
        { l: "NRR", v: "118%", c: "text-emerald-400", delta: "+3.2pp" },
        { l: "Churn", v: "2.1%", c: "text-amber-400", delta: "−0.4pp" },
      ],
      chartBars: [42, 55, 48, 62, 58, 72, 68, 80, 75, 88, 84, 100],
      chartColor: "from-violet-600/70 to-violet-400/40",
    },
  },
  {
    id: "revenue",
    icon: TrendingUp,
    label: "Revenue Movements",
    href: "/dashboard/revenue",
    color: "indigo",
    accentClass: "text-indigo-400",
    bgClass: "bg-indigo-500/10",
    borderClass: "border-indigo-500/20",
    activeBg: "bg-indigo-500/15",
    gradientClass: "from-indigo-600/20 to-indigo-600/5",
    headline: "MRR Bridge & Movement Analysis",
    description:
      "Decompose every dollar of MRR change. See exactly how new customers, expansions, contractions, churn, and reactivations combine to drive net new MRR each month.",
    bullets: [
      "MRR bridge waterfall chart by movement type",
      "Account-level movement table with drill-down",
      "New MRR by acquisition channel",
      "Expansion MRR by customer segment",
      "Invoice failure & payment trend analysis",
    ],
    preview: {
      kpis: [
        { l: "New MRR", v: "+$48K", c: "text-emerald-400", delta: "new" },
        { l: "Expansion", v: "+$31K", c: "text-blue-400", delta: "upsell" },
        { l: "Churn", v: "−$18K", c: "text-red-400", delta: "lost" },
        { l: "Net New", v: "+$61K", c: "text-indigo-400", delta: "net" },
      ],
      chartBars: [60, 45, 70, 55, 80, 65, 90, 75, 85, 95, 88, 100],
      chartColor: "from-indigo-600/70 to-indigo-400/40",
    },
  },
  {
    id: "cohorts",
    icon: Users,
    label: "Cohort Retention",
    href: "/dashboard/cohorts",
    color: "emerald",
    accentClass: "text-emerald-400",
    bgClass: "bg-emerald-500/10",
    borderClass: "border-emerald-500/20",
    activeBg: "bg-emerald-500/15",
    gradientClass: "from-emerald-600/20 to-emerald-600/5",
    headline: "Cohort Heatmaps & Retention Curves",
    description:
      "Visualize how customer cohorts retain over time. Identify which acquisition months, plans, and segments produce the stickiest customers — and which churn fastest.",
    bullets: [
      "Customer retention cohort heatmap (logo-based)",
      "Revenue retention cohort heatmap (MRR-based)",
      "Logo churn trend over 24 months",
      "NRR by cohort and acquisition channel",
      "Retention segmented by plan, company size, industry",
    ],
    preview: {
      kpis: [
        { l: "M+3 Ret.", v: "91%", c: "text-emerald-400", delta: "logo" },
        { l: "M+6 Ret.", v: "84%", c: "text-teal-400", delta: "logo" },
        { l: "M+12 Ret.", v: "76%", c: "text-cyan-400", delta: "logo" },
        { l: "GRR", v: "94%", c: "text-green-400", delta: "gross" },
      ],
      chartBars: [100, 94, 91, 88, 85, 84, 82, 80, 79, 77, 76, 75],
      chartColor: "from-emerald-600/70 to-emerald-400/40",
    },
  },
  {
    id: "health",
    icon: HeartPulse,
    label: "Customer Health",
    href: "/dashboard/health",
    color: "rose",
    accentClass: "text-rose-400",
    bgClass: "bg-rose-500/10",
    borderClass: "border-rose-500/20",
    activeBg: "bg-rose-500/15",
    gradientClass: "from-rose-600/20 to-rose-600/5",
    headline: "Health Scores & Churn Risk Signals",
    description:
      "Composite health scoring across 7 dimensions: usage frequency, seat utilization, feature adoption, support burden, CSAT, payment history, and tenure stability.",
    bullets: [
      "Health score distribution histogram",
      "Churn risk quadrant (health vs. MRR)",
      "Usage drop trend detection (>40% MoM)",
      "Support burden by account (ticket volume & priority)",
      "At-risk accounts table with risk reason flags",
    ],
    preview: {
      kpis: [
        { l: "Avg Score", v: "82/100", c: "text-emerald-400", delta: "health" },
        { l: "At Risk", v: "14", c: "text-amber-400", delta: "accts" },
        { l: "Critical", v: "3", c: "text-red-400", delta: "accts" },
        { l: "MRR Risk", v: "$124K", c: "text-rose-400", delta: "at risk" },
      ],
      chartBars: [5, 8, 12, 18, 25, 30, 28, 22, 18, 14, 10, 6],
      chartColor: "from-rose-600/70 to-rose-400/40",
    },
  },
  {
    id: "funnel",
    icon: GitBranch,
    label: "Funnel & Growth",
    href: "/dashboard/funnel",
    color: "blue",
    accentClass: "text-blue-400",
    bgClass: "bg-blue-500/10",
    borderClass: "border-blue-500/20",
    activeBg: "bg-blue-500/15",
    gradientClass: "from-blue-600/20 to-blue-600/5",
    headline: "Lead-to-Paid Funnel & Growth Drivers",
    description:
      "Track every stage of the customer acquisition funnel. Measure conversion rates by channel, sales cycle duration, trial engagement, and expansion revenue by segment.",
    bullets: [
      "Lead → Trial → Paid funnel visualization",
      "Conversion rate by acquisition channel",
      "Sales cycle duration (avg, median, min, max)",
      "Trial usage engagement vs. paid conversion rate",
      "Expansion MRR by segment and source",
    ],
    preview: {
      kpis: [
        { l: "Leads", v: "1,200", c: "text-blue-400", delta: "total" },
        { l: "Trials", v: "400", c: "text-indigo-400", delta: "33.3%" },
        { l: "Paid", v: "162", c: "text-violet-400", delta: "40.4%" },
        { l: "Overall", v: "13.4%", c: "text-emerald-400", delta: "conv." },
      ],
      chartBars: [100, 100, 100, 33, 33, 33, 13, 13, 13, 13, 13, 13],
      chartColor: "from-blue-600/70 to-blue-400/40",
    },
  },
];

// ─── Dashboard preview panel ───────────────────────────────────────────────────
function PreviewPanel({ feature }: { feature: (typeof FEATURES)[0] }) {
  const { preview, gradientClass } = feature;
  const { chartColor } = preview;

  return (
    <div className={`relative bg-gradient-to-br ${gradientClass} border border-white/[0.07] rounded-2xl overflow-hidden`}>
      {/* Browser chrome */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-slate-950/60 border-b border-white/[0.05]">
        <div className="flex gap-1.5">
          <div className="h-2 w-2 rounded-full bg-red-500/60" />
          <div className="h-2 w-2 rounded-full bg-amber-500/60" />
          <div className="h-2 w-2 rounded-full bg-emerald-500/60" />
        </div>
        <div className="flex-1 mx-2 bg-slate-800/50 rounded px-2 py-0.5 text-[9px] text-slate-500 font-mono text-center">
          flowsync.app{feature.href}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* KPI row */}
        <div className="grid grid-cols-4 gap-2 mb-3">
          {preview.kpis.map((k) => (
            <div key={k.l} className="bg-slate-900/70 border border-white/[0.05] rounded-lg p-2 text-center">
              <p className="text-[8px] text-slate-500 mb-0.5">{k.l}</p>
              <p className={`text-xs font-bold ${k.c}`}>{k.v}</p>
            </div>
          ))}
        </div>

        {/* Chart */}
        <div className="bg-slate-900/70 border border-white/[0.05] rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[9px] text-slate-500 font-semibold uppercase tracking-wider">
              {feature.label} Chart
            </p>
            <div className={`text-[9px] font-semibold ${feature.accentClass}`}>Live</div>
          </div>
          <div className="flex items-end gap-0.5 h-16">
            {preview.chartBars.map((h, i) => (
              <motion.div
                key={i}
                initial={{ height: 0 }}
                animate={{ height: `${h}%` }}
                transition={{ delay: i * 0.04, duration: 0.35, ease: "easeOut" }}
                className={`flex-1 rounded-sm bg-gradient-to-t ${chartColor}`}
              />
            ))}
          </div>
        </div>

        {/* Feature bullets preview */}
        <div className="mt-3 space-y-1.5">
          {feature.bullets.slice(0, 3).map((b) => (
            <div key={b} className="flex items-start gap-2">
              <CheckCircle2 className={`h-3 w-3 mt-0.5 flex-shrink-0 ${feature.accentClass}`} />
              <span className="text-[10px] text-slate-400 leading-tight">{b}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Section ──────────────────────────────────────────────────────────────────
export function FeaturesSection() {
  const [active, setActive] = useState(0);
  const activeFeature = FEATURES[active];

  return (
    <section id="features" className="relative py-28 bg-[#050510] overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[1000px] h-[400px] bg-indigo-700/5 rounded-full blur-[140px]" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <StaggerContainer className="text-center mb-14">
          <StaggerChild>
            <div className="inline-flex items-center gap-2 bg-slate-800/60 border border-white/[0.06] rounded-full px-4 py-1.5 mb-5">
              <Layers className="h-3.5 w-3.5 text-indigo-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                5 Dashboard Pages
              </span>
            </div>
          </StaggerChild>
          <StaggerChild>
            <h2 className="text-4xl sm:text-5xl font-bold text-white tracking-tight mb-5">
              Every view your{" "}
              <span className="bg-gradient-to-r from-indigo-400 to-blue-400 bg-clip-text text-transparent">
                team needs
              </span>
            </h2>
          </StaggerChild>
          <StaggerChild>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
              From executive board summaries to account-level churn risk signals —
              five purpose-built analytics pages covering every dimension of SaaS revenue.
            </p>
          </StaggerChild>
        </StaggerContainer>

        {/* Tab navigation */}
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            const isActive = i === active;
            return (
              <button
                key={f.id}
                onClick={() => setActive(i)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 border ${
                  isActive
                    ? `${f.activeBg} ${f.borderClass} ${f.accentClass}`
                    : "bg-slate-900/40 border-white/[0.06] text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Icon className="h-4 w-4" />
                {f.label}
              </button>
            );
          })}
        </div>

        {/* Feature detail */}
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -16 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="grid lg:grid-cols-2 gap-8 items-start"
          >
            {/* Left: text */}
            <div className="flex flex-col justify-center">
              <div className={`${activeFeature.bgClass} rounded-xl p-3 w-fit mb-5`}>
                {React.createElement(activeFeature.icon, {
                  className: `h-6 w-6 ${activeFeature.accentClass}`,
                  strokeWidth: 2,
                })}
              </div>

              <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mb-4">
                {activeFeature.headline}
              </h3>
              <p className="text-base text-slate-400 leading-relaxed mb-7">
                {activeFeature.description}
              </p>

              <ul className="space-y-3 mb-8">
                {activeFeature.bullets.map((b) => (
                  <li key={b} className="flex items-start gap-3">
                    <CheckCircle2
                      className={`h-4 w-4 mt-0.5 flex-shrink-0 ${activeFeature.accentClass}`}
                    />
                    <span className="text-sm text-slate-300">{b}</span>
                  </li>
                ))}
              </ul>

              <Link href={activeFeature.href}>
                <Button
                  className={`w-fit bg-gradient-to-r ${
                    activeFeature.color === "violet"
                      ? "from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 shadow-violet-500/20"
                      : activeFeature.color === "indigo"
                      ? "from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 shadow-indigo-500/20"
                      : activeFeature.color === "emerald"
                      ? "from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-emerald-500/20"
                      : activeFeature.color === "rose"
                      ? "from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 shadow-rose-500/20"
                      : "from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-blue-500/20"
                  } text-white border-0 shadow-lg gap-2 group`}
                >
                  Open {activeFeature.label}
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                </Button>
              </Link>
            </div>

            {/* Right: preview */}
            <PreviewPanel feature={activeFeature} />
          </motion.div>
        </AnimatePresence>

        {/* Bottom: all pages grid */}
        <div className="mt-16 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            return (
              <Link key={f.id} href={f.href}>
                <motion.div
                  whileHover={{ y: -3, scale: 1.02 }}
                  transition={{ duration: 0.2 }}
                  className={`group bg-slate-900/50 border ${f.borderClass} rounded-xl p-4 text-center cursor-pointer hover:${f.activeBg} transition-all duration-200`}
                >
                  <div className={`${f.bgClass} rounded-lg p-2 w-fit mx-auto mb-2.5`}>
                    <Icon className={`h-4 w-4 ${f.accentClass}`} />
                  </div>
                  <p className="text-xs font-semibold text-slate-300 group-hover:text-white transition-colors leading-tight">
                    {f.label}
                  </p>
                </motion.div>
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
}
