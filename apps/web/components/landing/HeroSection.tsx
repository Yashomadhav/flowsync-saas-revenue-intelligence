"use client";

import React, { useEffect, useRef } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import {
  ArrowRight, TrendingUp, TrendingDown, Activity,
  DollarSign, Users, Shield, Zap, Database,
} from "lucide-react";
import { Button } from "@/components/ui/button";

// Dynamically import R3F canvas — no SSR
const AnalyticsSphere = dynamic(
  () => import("@/components/three/AnalyticsSphere").then((m) => m.AnalyticsSphere),
  { ssr: false, loading: () => <div className="w-full h-full" /> }
);

// ─── Subtle dot-grid background ───────────────────────────────────────────────
function DotGrid() {
  return (
    <div
      className="absolute inset-0 opacity-[0.035]"
      style={{
        backgroundImage: `radial-gradient(circle, rgba(255,255,255,0.8) 1px, transparent 1px)`,
        backgroundSize: "32px 32px",
      }}
    />
  );
}

// ─── Floating KPI badge ────────────────────────────────────────────────────────
interface KPIBadgeProps {
  label: string;
  value: string;
  sub: string;
  color: string;
  dotColor: string;
  delay: number;
  className?: string;
}

function KPIBadge({ label, value, sub, color, dotColor, delay, className }: KPIBadgeProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85, y: 12 }}
      animate={{ opacity: 1, scale: 1, y: [0, -10, 0] }}
      transition={{
        opacity: { delay, duration: 0.5 },
        scale: { delay, duration: 0.5 },
        y: { delay: delay + 0.5, duration: 4.5, repeat: Infinity, ease: "easeInOut" },
      }}
      className={`absolute hidden lg:block ${className}`}
    >
      <div className="bg-slate-900/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-3.5 shadow-2xl shadow-black/40 w-48">
        <div className="flex items-center gap-2 mb-2">
          <div className={`h-1.5 w-1.5 rounded-full ${dotColor} animate-pulse`} />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            {label}
          </span>
        </div>
        <p className="text-xl font-bold text-white tracking-tight">{value}</p>
        <p className={`text-[11px] mt-0.5 font-medium ${color}`}>{sub}</p>
      </div>
    </motion.div>
  );
}

// ─── Mini dashboard preview ────────────────────────────────────────────────────
function DashboardPreview() {
  const bars = [42, 58, 51, 67, 63, 74, 70, 83, 79, 91, 87, 100];

  return (
    <motion.div
      initial={{ opacity: 0, y: 48, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 1.1, delay: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="relative mt-12 lg:mt-0"
    >
      {/* Outer glow */}
      <div className="absolute -inset-6 bg-gradient-to-r from-violet-600/15 via-indigo-600/15 to-blue-600/15 rounded-3xl blur-3xl" />

      {/* Browser frame */}
      <div className="relative bg-slate-900/95 backdrop-blur-xl border border-white/[0.08] rounded-2xl overflow-hidden shadow-[0_32px_80px_rgba(0,0,0,0.6)]">
        {/* Chrome bar */}
        <div className="flex items-center gap-2 px-4 py-3 bg-slate-950/70 border-b border-white/[0.05]">
          <div className="flex gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
            <div className="h-2.5 w-2.5 rounded-full bg-amber-500/70" />
            <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/70" />
          </div>
          <div className="flex-1 mx-3 bg-slate-800/60 rounded-md px-3 py-1 text-[10px] text-slate-500 text-center font-mono">
            flowsync.app/dashboard
          </div>
          <div className="h-4 w-4 rounded bg-slate-800/60" />
        </div>

        {/* Dashboard content */}
        <div className="p-4 bg-slate-950/60">
          {/* KPI row */}
          <div className="grid grid-cols-4 gap-2.5 mb-4">
            {[
              { l: "MRR", v: "$847K", c: "from-violet-500/20 to-violet-600/5", b: "border-violet-500/20", t: "text-violet-400" },
              { l: "ARR", v: "$10.2M", c: "from-indigo-500/20 to-indigo-600/5", b: "border-indigo-500/20", t: "text-indigo-400" },
              { l: "NRR", v: "118%", c: "from-emerald-500/20 to-emerald-600/5", b: "border-emerald-500/20", t: "text-emerald-400" },
              { l: "Churn", v: "2.1%", c: "from-amber-500/20 to-amber-600/5", b: "border-amber-500/20", t: "text-amber-400" },
            ].map((k) => (
              <div key={k.l} className={`bg-gradient-to-br ${k.c} border ${k.b} rounded-xl p-2.5`}>
                <p className={`text-[9px] font-semibold uppercase tracking-wider ${k.t} mb-1`}>{k.l}</p>
                <p className="text-sm font-bold text-white">{k.v}</p>
              </div>
            ))}
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-3 gap-2.5">
            {/* MRR trend */}
            <div className="col-span-2 bg-slate-900/60 border border-white/[0.05] rounded-xl p-3">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] font-semibold text-slate-500 uppercase tracking-wider">MRR Trend</p>
                <span className="text-[9px] text-emerald-400 font-medium">+12.4%</span>
              </div>
              <div className="flex items-end gap-0.5 h-14">
                {bars.map((h, i) => (
                  <motion.div
                    key={i}
                    initial={{ height: 0 }}
                    animate={{ height: `${h}%` }}
                    transition={{ delay: 1.2 + i * 0.05, duration: 0.4, ease: "easeOut" }}
                    className="flex-1 rounded-sm bg-gradient-to-t from-violet-600/70 to-violet-400/50"
                  />
                ))}
              </div>
            </div>

            {/* Revenue by plan */}
            <div className="bg-slate-900/60 border border-white/[0.05] rounded-xl p-3">
              <p className="text-[9px] font-semibold text-slate-500 uppercase tracking-wider mb-2">By Plan</p>
              <div className="space-y-2">
                {[
                  { l: "Enterprise", w: "78%", c: "bg-violet-500" },
                  { l: "Business", w: "56%", c: "bg-indigo-500" },
                  { l: "Growth", w: "34%", c: "bg-blue-500" },
                  { l: "Starter", w: "18%", c: "bg-slate-600" },
                ].map((p) => (
                  <div key={p.l} className="flex items-center gap-1.5">
                    <span className="text-[8px] text-slate-500 w-11 truncate">{p.l}</span>
                    <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: p.w }}
                        transition={{ delay: 1.5, duration: 0.6, ease: "easeOut" }}
                        className={`h-full ${p.c} rounded-full`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom row */}
          <div className="grid grid-cols-3 gap-2.5 mt-2.5">
            {[
              { label: "Health Score", value: "82/100", color: "text-emerald-400" },
              { label: "At-Risk Accounts", value: "14", color: "text-amber-400" },
              { label: "Trial → Paid", value: "40.4%", color: "text-blue-400" },
            ].map((s) => (
              <div key={s.label} className="bg-slate-900/60 border border-white/[0.05] rounded-xl p-2.5 text-center">
                <p className="text-[8px] text-slate-500 mb-1">{s.label}</p>
                <p className={`text-xs font-bold ${s.color}`}>{s.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Hero section ──────────────────────────────────────────────────────────────
export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden bg-slate-950">
      {/* Layered gradient background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-[#0a0a1a] to-slate-950" />
        {/* Violet bloom top-left */}
        <div className="absolute -top-40 -left-40 w-[700px] h-[700px] bg-violet-700/8 rounded-full blur-[140px]" />
        {/* Indigo bloom center */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[900px] h-[600px] bg-indigo-700/6 rounded-full blur-[160px]" />
        {/* Blue bloom bottom-right */}
        <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] bg-blue-700/8 rounded-full blur-[120px]" />
      </div>

      <DotGrid />

      {/* Floating KPI badges */}
      <KPIBadge
        label="MRR" value="$847,320" sub="↑ +12.4% month-over-month"
        color="text-emerald-400" dotColor="bg-emerald-400"
        delay={1.4} className="left-[2%] top-[22%]"
      />
      <KPIBadge
        label="NRR" value="118.4%" sub="Net Revenue Retention"
        color="text-violet-400" dotColor="bg-violet-400"
        delay={1.7} className="right-[2%] top-[18%]"
      />
      <KPIBadge
        label="Churn Risk" value="14 accounts" sub="$124k MRR at risk"
        color="text-amber-400" dotColor="bg-amber-400"
        delay={2.0} className="right-[2%] bottom-[22%]"
      />
      <KPIBadge
        label="ARR" value="$10.17M" sub="Annual Recurring Revenue"
        color="text-blue-400" dotColor="bg-blue-400"
        delay={1.9} className="left-[2%] bottom-[22%]"
      />

      {/* Main content */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">

          {/* ── Left: Text content ── */}
          <div className="flex flex-col items-start">
            {/* Eyebrow badge */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.1 }}
              className="inline-flex items-center gap-2 bg-violet-500/10 border border-violet-500/20 rounded-full px-4 py-1.5 mb-7"
            >
              <div className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" />
              <span className="text-xs font-semibold text-violet-300 tracking-wide">
                Full-Stack SaaS Revenue Intelligence
              </span>
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="text-5xl sm:text-6xl xl:text-7xl font-bold text-white leading-[1.04] tracking-tight mb-6"
            >
              Revenue
              <br />
              <span className="bg-gradient-to-r from-violet-400 via-indigo-400 to-blue-400 bg-clip-text text-transparent">
                Intelligence
              </span>
              <br />
              Built for Scale
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.3 }}
              className="text-lg text-slate-400 max-w-lg mb-9 leading-relaxed"
            >
              End-to-end BI platform for{" "}
              <span className="text-slate-200 font-medium">FlowSync</span> — track MRR
              movements, cohort retention, customer health scores, and funnel conversion
              with enterprise-grade analytics and a{" "}
              <span className="text-slate-200 font-medium">medallion data architecture</span>.
            </motion.p>

            {/* CTA buttons */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="flex flex-col sm:flex-row gap-3 mb-12"
            >
              <Link href="/dashboard">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white border-0 shadow-2xl shadow-violet-500/25 px-8 h-12 text-sm font-semibold gap-2 group"
                >
                  Open Dashboard
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                </Button>
              </Link>
              <a href="#why">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-white/10 text-slate-300 hover:bg-white/5 hover:text-white h-12 px-8 text-sm font-semibold gap-2 bg-transparent"
                >
                  <Activity className="h-4 w-4" />
                  Explore Metrics
                </Button>
              </a>
            </motion.div>

            {/* Tech trust row */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="flex flex-wrap gap-x-6 gap-y-2"
            >
              {[
                { icon: Database, label: "PostgreSQL + dbt" },
                { icon: Zap, label: "FastAPI Backend" },
                { icon: Shield, label: "Docker + CI/CD" },
                { icon: TrendingUp, label: "Recharts + R3F" },
              ].map(({ icon: Icon, label }) => (
                <div key={label} className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Icon className="h-3.5 w-3.5 text-slate-600" />
                  <span>{label}</span>
                </div>
              ))}
            </motion.div>
          </div>

          {/* ── Right: 3D sphere + dashboard preview ── */}
          <div className="relative flex flex-col items-center">
            {/* 3D Sphere */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1.0, delay: 0.5, ease: "easeOut" }}
              className="w-full h-[340px] lg:h-[420px] relative"
            >
              {/* Glow behind sphere */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-64 h-64 bg-violet-600/15 rounded-full blur-[80px]" />
              </div>
              <AnalyticsSphere />
            </motion.div>

            {/* Dashboard preview below sphere */}
            <div className="w-full max-w-lg">
              <DashboardPreview />
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2.0, duration: 0.8 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        >
          <span className="text-[10px] text-slate-600 uppercase tracking-widest font-medium">
            Scroll to explore
          </span>
          <motion.div
            animate={{ y: [0, 6, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            className="w-px h-8 bg-gradient-to-b from-slate-600 to-transparent"
          />
        </motion.div>
      </div>
    </section>
  );
}
