"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Monitor, Server, Database, GitBranch, Cloud,
  ArrowRight, ChevronDown, Code2, Layers3,
} from "lucide-react";
import { StaggerContainer, StaggerChild } from "./SectionWrapper";

const LAYERS = [
  {
    id: "frontend",
    icon: Monitor,
    label: "Frontend",
    sublabel: "Next.js 14 App Router",
    color: "violet",
    accentClass: "text-violet-400",
    bgClass: "bg-violet-500/10",
    borderClass: "border-violet-500/20",
    dotColor: "bg-violet-400",
    tech: [
      { name: "Next.js 14", desc: "App Router, SSR, RSC" },
      { name: "TypeScript", desc: "Strict type safety" },
      { name: "Tailwind CSS", desc: "Utility-first styling" },
      { name: "shadcn/ui", desc: "Radix UI components" },
      { name: "Framer Motion", desc: "Scroll animations" },
      { name: "React Three Fiber", desc: "3D WebGL canvas" },
      { name: "Recharts", desc: "Interactive charts" },
    ],
    description:
      "Server-side rendered Next.js app with App Router. Landing page uses React Three Fiber for 3D elements and Framer Motion for scroll-triggered animations. Dashboard pages use Recharts for all data visualizations.",
  },
  {
    id: "api",
    icon: Server,
    label: "API Layer",
    sublabel: "FastAPI + Python",
    color: "indigo",
    accentClass: "text-indigo-400",
    bgClass: "bg-indigo-500/10",
    borderClass: "border-indigo-500/20",
    dotColor: "bg-indigo-400",
    tech: [
      { name: "FastAPI", desc: "Async REST API" },
      { name: "SQLAlchemy 2.0", desc: "ORM + raw SQL" },
      { name: "Pydantic v2", desc: "Schema validation" },
      { name: "Uvicorn", desc: "ASGI server" },
      { name: "structlog", desc: "Structured logging" },
      { name: "CORS middleware", desc: "Cross-origin support" },
    ],
    description:
      "25+ REST endpoints across 5 domain routers: executive, revenue, cohorts, health, and funnel. Each router queries the PostgreSQL gold layer and returns typed Pydantic schemas.",
  },
  {
    id: "database",
    icon: Database,
    label: "Data Warehouse",
    sublabel: "PostgreSQL + Medallion",
    color: "blue",
    accentClass: "text-blue-400",
    bgClass: "bg-blue-500/10",
    borderClass: "border-blue-500/20",
    dotColor: "bg-blue-400",
    tech: [
      { name: "Bronze Layer", desc: "raw_accounts, raw_subscriptions, raw_invoices, raw_usage_events, raw_tickets, raw_leads" },
      { name: "Silver Layer", desc: "stg_accounts, stg_subscriptions, stg_invoices, stg_usage_events, stg_tickets, stg_leads" },
      { name: "Gold Layer", desc: "fct_mrr_movements, fct_account_monthly_health, fct_customer_cohorts, fct_sales_conversion, mart_exec_revenue_summary, mart_customer_success_summary" },
    ],
    description:
      "Star schema with medallion architecture. Bronze holds raw CSV-loaded data. Silver applies cleaning and typing. Gold contains pre-aggregated fact tables and marts optimized for dashboard queries.",
  },
  {
    id: "dbt",
    icon: GitBranch,
    label: "Transformations",
    sublabel: "dbt Core",
    color: "emerald",
    accentClass: "text-emerald-400",
    bgClass: "bg-emerald-500/10",
    borderClass: "border-emerald-500/20",
    dotColor: "bg-emerald-400",
    tech: [
      { name: "18 dbt Models", desc: "6 bronze + 6 silver + 6 gold" },
      { name: "MRR Movements", desc: "fct_mrr_movements with waterfall logic" },
      { name: "Health Scoring", desc: "fct_account_monthly_health composite score" },
      { name: "Cohort Analysis", desc: "fct_customer_cohorts retention matrix" },
      { name: "Sales Funnel", desc: "fct_sales_conversion stage tracking" },
      { name: "Executive Marts", desc: "mart_exec_revenue_summary aggregations" },
    ],
    description:
      "18 dbt models implementing the full medallion pipeline. MRR waterfall logic, cohort retention matrices, health score composites, and sales funnel conversion — all as SQL transformations with lineage.",
  },
  {
    id: "deploy",
    icon: Cloud,
    label: "Deployment",
    sublabel: "Docker + CI/CD",
    color: "rose",
    accentClass: "text-rose-400",
    bgClass: "bg-rose-500/10",
    borderClass: "border-rose-500/20",
    dotColor: "bg-rose-400",
    tech: [
      { name: "Docker Compose", desc: "Local dev: web + api + postgres + dbt" },
      { name: "Vercel", desc: "Frontend deployment (Next.js)" },
      { name: "Render / Railway", desc: "Backend + PostgreSQL hosting" },
      { name: "GitHub Actions", desc: "CI: lint, typecheck, build" },
      { name: "dbt GitHub Action", desc: "Scheduled dbt runs on merge" },
      { name: ".env.example", desc: "Environment variable templates" },
    ],
    description:
      "One-command local dev with Docker Compose. Frontend deploys to Vercel, backend to Render or Railway. GitHub Actions runs TypeScript checks, linting, and dbt transformations on every merge.",
  },
];

// ─── Data flow arrow ──────────────────────────────────────────────────────────
function FlowArrow() {
  return (
    <div className="flex justify-center my-1">
      <motion.div
        animate={{ y: [0, 4, 0] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        className="flex flex-col items-center gap-0.5"
      >
        <div className="w-px h-4 bg-gradient-to-b from-white/20 to-white/5" />
        <ChevronDown className="h-3 w-3 text-slate-600" />
      </motion.div>
    </div>
  );
}

// ─── Layer card ───────────────────────────────────────────────────────────────
function LayerCard({
  layer,
  isActive,
  onClick,
}: {
  layer: (typeof LAYERS)[0];
  isActive: boolean;
  onClick: () => void;
}) {
  const Icon = layer.icon;

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.01 }}
      transition={{ duration: 0.2 }}
      className={`w-full text-left rounded-2xl border transition-all duration-300 overflow-hidden ${
        isActive
          ? `${layer.bgClass} ${layer.borderClass} shadow-lg`
          : "bg-slate-900/40 border-white/[0.06] hover:bg-slate-900/70 hover:border-white/10"
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-3 p-4">
        <div className={`${isActive ? layer.bgClass : "bg-slate-800/60"} rounded-xl p-2.5 transition-colors`}>
          <Icon className={`h-5 w-5 ${isActive ? layer.accentClass : "text-slate-500"}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className={`text-sm font-semibold ${isActive ? "text-white" : "text-slate-300"}`}>
              {layer.label}
            </p>
            {isActive && (
              <div className={`h-1.5 w-1.5 rounded-full ${layer.dotColor} animate-pulse`} />
            )}
          </div>
          <p className={`text-xs ${isActive ? layer.accentClass : "text-slate-500"}`}>
            {layer.sublabel}
          </p>
        </div>
        <ChevronDown
          className={`h-4 w-4 transition-all duration-300 ${
            isActive ? `${layer.accentClass} rotate-180` : "text-slate-600"
          }`}
        />
      </div>

      {/* Expanded content */}
      <AnimatePresence>
        {isActive && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 border-t border-white/[0.06]">
              <p className="text-xs text-slate-400 leading-relaxed mt-3 mb-3">
                {layer.description}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {layer.tech.map((t) => (
                  <div
                    key={t.name}
                    className={`${layer.bgClass} border ${layer.borderClass} rounded-lg px-2.5 py-1`}
                    title={t.desc}
                  >
                    <span className={`text-[10px] font-semibold ${layer.accentClass}`}>
                      {t.name}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
}

// ─── Architecture diagram (right panel) ───────────────────────────────────────
function ArchDiagram({ activeLayer }: { activeLayer: (typeof LAYERS)[0] }) {
  return (
    <motion.div
      key={activeLayer.id}
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="sticky top-24"
    >
      {/* Main diagram */}
      <div className="bg-slate-900/60 border border-white/[0.07] rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-white/[0.05] bg-slate-950/40">
          <Code2 className="h-4 w-4 text-slate-500" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Architecture — {activeLayer.label}
          </span>
        </div>

        {/* Stack visualization */}
        <div className="p-5 space-y-1">
          {LAYERS.map((layer, i) => {
            const Icon = layer.icon;
            const isActive = layer.id === activeLayer.id;
            return (
              <React.Fragment key={layer.id}>
                <motion.div
                  animate={{
                    scale: isActive ? 1.02 : 1,
                    opacity: isActive ? 1 : 0.45,
                  }}
                  transition={{ duration: 0.3 }}
                  className={`flex items-center gap-3 rounded-xl px-4 py-3 border transition-all ${
                    isActive
                      ? `${layer.bgClass} ${layer.borderClass}`
                      : "bg-slate-900/40 border-white/[0.04]"
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? layer.accentClass : "text-slate-600"}`} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-semibold ${isActive ? "text-white" : "text-slate-500"}`}>
                      {layer.label}
                    </p>
                    <p className={`text-[10px] ${isActive ? layer.accentClass : "text-slate-600"}`}>
                      {layer.sublabel}
                    </p>
                  </div>
                  {isActive && (
                    <div className={`h-2 w-2 rounded-full ${layer.dotColor} animate-pulse`} />
                  )}
                </motion.div>
                {i < LAYERS.length - 1 && (
                  <div className="flex justify-center">
                    <div className="w-px h-3 bg-white/10" />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Tech detail panel */}
      <div className={`mt-4 ${activeLayer.bgClass} border ${activeLayer.borderClass} rounded-2xl p-5`}>
        <p className={`text-xs font-semibold uppercase tracking-wider ${activeLayer.accentClass} mb-3`}>
          {activeLayer.label} Stack
        </p>
        <div className="space-y-2">
          {activeLayer.tech.slice(0, 5).map((t) => (
            <div key={t.name} className="flex items-start gap-2.5">
              <div className={`h-1.5 w-1.5 rounded-full ${activeLayer.dotColor} mt-1.5 flex-shrink-0`} />
              <div>
                <span className="text-xs font-semibold text-white">{t.name}</span>
                <span className="text-xs text-slate-500 ml-1.5">{t.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

// ─── Section ──────────────────────────────────────────────────────────────────
export function ArchitectureSection() {
  const [activeIdx, setActiveIdx] = useState(0);
  const activeLayer = LAYERS[activeIdx];

  return (
    <section id="architecture" className="relative py-28 bg-slate-950 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 -translate-y-1/2 right-0 w-[600px] h-[600px] bg-blue-700/5 rounded-full blur-[140px]" />
        <div className="absolute top-1/2 -translate-y-1/2 left-0 w-[400px] h-[400px] bg-emerald-700/4 rounded-full blur-[120px]" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <StaggerContainer className="text-center mb-16">
          <StaggerChild>
            <div className="inline-flex items-center gap-2 bg-slate-800/60 border border-white/[0.06] rounded-full px-4 py-1.5 mb-5">
              <Layers3 className="h-3.5 w-3.5 text-blue-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Technical Architecture
              </span>
            </div>
          </StaggerChild>
          <StaggerChild>
            <h2 className="text-4xl sm:text-5xl font-bold text-white tracking-tight mb-5">
              Production-grade{" "}
              <span className="bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                full-stack design
              </span>
            </h2>
          </StaggerChild>
          <StaggerChild>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
              Five-layer architecture from browser to database — each layer independently
              deployable, containerized, and connected through typed interfaces.
            </p>
          </StaggerChild>
        </StaggerContainer>

        {/* Main layout */}
        <div className="grid lg:grid-cols-2 gap-8 items-start">
          {/* Left: accordion layers */}
          <div className="space-y-2">
            {LAYERS.map((layer, i) => (
              <React.Fragment key={layer.id}>
                <LayerCard
                  layer={layer}
                  isActive={i === activeIdx}
                  onClick={() => setActiveIdx(i)}
                />
                {i < LAYERS.length - 1 && <FlowArrow />}
              </React.Fragment>
            ))}
          </div>

          {/* Right: diagram */}
          <ArchDiagram activeLayer={activeLayer} />
        </div>

        {/* Bottom: data flow summary */}
        <div className="mt-16 bg-slate-900/40 border border-white/[0.06] rounded-2xl p-6">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 text-center">
            Data Flow
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2">
            {[
              { label: "Python Generator", color: "text-slate-400" },
              { label: "→", color: "text-slate-600" },
              { label: "PostgreSQL Bronze", color: "text-amber-400" },
              { label: "→", color: "text-slate-600" },
              { label: "dbt Silver", color: "text-blue-400" },
              { label: "→", color: "text-slate-600" },
              { label: "dbt Gold", color: "text-emerald-400" },
              { label: "→", color: "text-slate-600" },
              { label: "FastAPI", color: "text-indigo-400" },
              { label: "→", color: "text-slate-600" },
              { label: "Next.js Dashboard", color: "text-violet-400" },
            ].map((item, i) => (
              <span key={i} className={`text-sm font-semibold ${item.color}`}>
                {item.label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
