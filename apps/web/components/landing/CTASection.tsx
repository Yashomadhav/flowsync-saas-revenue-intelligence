"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight, Github, ExternalLink, Star,
  LayoutDashboard, Database, GitBranch, Server,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StaggerContainer, StaggerChild } from "./SectionWrapper";

const TECH_BADGES = [
  { label: "Next.js 14", color: "text-slate-300" },
  { label: "FastAPI", color: "text-emerald-400" },
  { label: "PostgreSQL", color: "text-blue-400" },
  { label: "dbt Core", color: "text-orange-400" },
  { label: "React Three Fiber", color: "text-violet-400" },
  { label: "Framer Motion", color: "text-pink-400" },
  { label: "Recharts", color: "text-cyan-400" },
  { label: "Docker", color: "text-sky-400" },
  { label: "TypeScript", color: "text-blue-300" },
  { label: "Tailwind CSS", color: "text-teal-400" },
  { label: "shadcn/ui", color: "text-slate-300" },
  { label: "GitHub Actions", color: "text-amber-400" },
];

const QUICK_LINKS = [
  {
    icon: LayoutDashboard,
    label: "Executive Overview",
    href: "/dashboard",
    color: "text-violet-400",
    bg: "bg-violet-500/10",
  },
  {
    icon: Database,
    label: "Cohort Retention",
    href: "/dashboard/cohorts",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  {
    icon: GitBranch,
    label: "Funnel & Growth",
    href: "/dashboard/funnel",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    icon: Server,
    label: "Customer Health",
    href: "/dashboard/health",
    color: "text-rose-400",
    bg: "bg-rose-500/10",
  },
];

// ─── Floating tech badge ──────────────────────────────────────────────────────
function TechBadge({ label, color, delay }: { label: string; color: string; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
      whileHover={{ scale: 1.05, y: -2 }}
      className="bg-slate-900/70 border border-white/[0.07] rounded-full px-3 py-1.5 cursor-default"
    >
      <span className={`text-xs font-semibold ${color}`}>{label}</span>
    </motion.div>
  );
}

// ─── Section ──────────────────────────────────────────────────────────────────
export function CTASection() {
  return (
    <section className="relative py-28 bg-slate-950 overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.06, 0.1, 0.06],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-600 rounded-full blur-[120px]"
        />
        {/* Grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main CTA block */}
        <StaggerContainer className="text-center mb-16">
          <StaggerChild>
            <div className="inline-flex items-center gap-2 bg-violet-500/10 border border-violet-500/20 rounded-full px-4 py-1.5 mb-6">
              <Star className="h-3.5 w-3.5 text-violet-400 fill-violet-400" />
              <span className="text-xs font-semibold text-violet-300">
                Portfolio Project — Production-Grade Code
              </span>
            </div>
          </StaggerChild>

          <StaggerChild>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight mb-6 leading-tight">
              Ready to explore{" "}
              <span className="bg-gradient-to-r from-violet-400 via-indigo-400 to-blue-400 bg-clip-text text-transparent">
                FlowSync BI?
              </span>
            </h2>
          </StaggerChild>

          <StaggerChild>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed mb-10">
              Dive into the live dashboards, explore the data architecture, or browse
              the source code. Everything is open and documented.
            </p>
          </StaggerChild>

          {/* CTA buttons */}
          <StaggerChild>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
              <Link href="/dashboard">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white border-0 shadow-xl shadow-violet-500/25 gap-2 group px-8 h-12 text-base font-semibold"
                >
                  <LayoutDashboard className="h-5 w-5" />
                  Open Dashboard
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                </Button>
              </Link>
              <a
                href="https://github.com/Yashomadhav/flowsync-saas-revenue-intelligence"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button
                  size="lg"
                  variant="outline"
                  className="border-white/10 bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 hover:text-white gap-2 px-8 h-12 text-base font-semibold"
                >
                  <Github className="h-5 w-5" />
                  View Source
                  <ExternalLink className="h-3.5 w-3.5 opacity-60" />
                </Button>
              </a>
            </div>
          </StaggerChild>

          {/* Quick links */}
          <StaggerChild>
            <div className="flex flex-wrap items-center justify-center gap-3 mb-4">
              <span className="text-xs text-slate-600 font-medium">Jump to:</span>
              {QUICK_LINKS.map((link) => {
                const Icon = link.icon;
                return (
                  <Link key={link.href} href={link.href}>
                    <motion.div
                      whileHover={{ scale: 1.05, y: -1 }}
                      transition={{ duration: 0.15 }}
                      className={`flex items-center gap-1.5 ${link.bg} border border-white/[0.06] rounded-full px-3 py-1.5 cursor-pointer hover:border-white/10 transition-colors`}
                    >
                      <Icon className={`h-3 w-3 ${link.color}`} />
                      <span className={`text-xs font-semibold ${link.color}`}>{link.label}</span>
                    </motion.div>
                  </Link>
                );
              })}
            </div>
          </StaggerChild>
        </StaggerContainer>

        {/* Divider */}
        <div className="flex items-center gap-4 mb-12">
          <div className="flex-1 h-px bg-white/[0.05]" />
          <span className="text-xs text-slate-600 font-medium uppercase tracking-wider">Built With</span>
          <div className="flex-1 h-px bg-white/[0.05]" />
        </div>

        {/* Tech badges */}
        <div className="flex flex-wrap justify-center gap-2.5 mb-16">
          {TECH_BADGES.map((badge, i) => (
            <TechBadge
              key={badge.label}
              label={badge.label}
              color={badge.color}
              delay={i * 0.04}
            />
          ))}
        </div>

        {/* Stats row */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-white/[0.04] rounded-2xl overflow-hidden border border-white/[0.06]"
        >
          {[
            { value: "80+", label: "Source Files" },
            { value: "18", label: "dbt Models" },
            { value: "25+", label: "API Endpoints" },
            { value: "5", label: "Dashboard Pages" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="bg-slate-900/80 px-6 py-6 text-center hover:bg-slate-900/95 transition-colors"
            >
              <p className="text-2xl font-bold text-white mb-1">{stat.value}</p>
              <p className="text-xs text-slate-500 font-medium">{stat.label}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
