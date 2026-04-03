"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Github, Twitter, Linkedin, ExternalLink,
  BarChart3, ArrowUpRight,
} from "lucide-react";

const NAV_GROUPS = [
  {
    title: "Dashboards",
    links: [
      { label: "Executive Overview", href: "/dashboard" },
      { label: "Revenue Movements", href: "/dashboard/revenue" },
      { label: "Cohort Retention", href: "/dashboard/cohorts" },
      { label: "Customer Health", href: "/dashboard/health" },
      { label: "Funnel & Growth", href: "/dashboard/funnel" },
    ],
  },
  {
    title: "Landing Sections",
    links: [
      { label: "Why It Matters", href: "#why" },
      { label: "Features", href: "#features" },
      { label: "Architecture", href: "#architecture" },
      { label: "Insights", href: "#insights" },
    ],
  },
  {
    title: "Tech Stack",
    links: [
      { label: "Next.js 14", href: "https://nextjs.org", external: true },
      { label: "FastAPI", href: "https://fastapi.tiangolo.com", external: true },
      { label: "dbt Core", href: "https://getdbt.com", external: true },
      { label: "React Three Fiber", href: "https://r3f.docs.pmnd.rs", external: true },
      { label: "Recharts", href: "https://recharts.org", external: true },
    ],
  },
  {
    title: "Data Layer",
    links: [
      { label: "Bronze Models (6)", href: "#architecture" },
      { label: "Silver Models (6)", href: "#architecture" },
      { label: "Gold Models (6)", href: "#architecture" },
      { label: "Python Generator", href: "#architecture" },
      { label: "Medallion Schema", href: "#architecture" },
    ],
  },
];

const SOCIAL_LINKS = [
  { icon: Github, href: "https://github.com", label: "GitHub" },
  { icon: Twitter, href: "https://twitter.com", label: "Twitter" },
  { icon: Linkedin, href: "https://linkedin.com", label: "LinkedIn" },
];

const METRIC_PILLS = [
  { label: "MRR", value: "$847K" },
  { label: "NRR", value: "118%" },
  { label: "Churn", value: "2.1%" },
  { label: "ARR", value: "$10.2M" },
];

export function Footer() {
  return (
    <footer className="relative bg-slate-950 border-t border-white/[0.05] overflow-hidden">
      {/* Subtle top gradient */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-violet-500/30 to-transparent" />

      {/* Background glow */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[200px] bg-violet-700/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top section */}
        <div className="py-14 grid lg:grid-cols-5 gap-10">
          {/* Brand column */}
          <div className="lg:col-span-1">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2.5 mb-5 group w-fit">
              <div className="relative h-8 w-8 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
                <BarChart3 className="h-4 w-4 text-white" strokeWidth={2.5} />
              </div>
              <div>
                <span className="text-sm font-bold text-white tracking-tight">FlowSync</span>
                <span className="block text-[9px] text-slate-500 font-medium -mt-0.5 tracking-wider uppercase">
                  Revenue BI
                </span>
              </div>
            </Link>

            <p className="text-xs text-slate-500 leading-relaxed mb-5">
              A production-grade SaaS Revenue Intelligence platform built as a
              full-stack portfolio project. Fictional company, real engineering.
            </p>

            {/* Live metrics pills */}
            <div className="flex flex-wrap gap-1.5 mb-6">
              {METRIC_PILLS.map((m) => (
                <div
                  key={m.label}
                  className="bg-slate-900/80 border border-white/[0.06] rounded-full px-2.5 py-1 flex items-center gap-1.5"
                >
                  <span className="text-[9px] text-slate-500">{m.label}</span>
                  <span className="text-[9px] font-bold text-violet-400">{m.value}</span>
                </div>
              ))}
            </div>

            {/* Social links */}
            <div className="flex items-center gap-2">
              {SOCIAL_LINKS.map(({ icon: Icon, href, label }) => (
                <motion.a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={label}
                  whileHover={{ scale: 1.1, y: -1 }}
                  transition={{ duration: 0.15 }}
                  className="h-8 w-8 rounded-lg bg-slate-900/80 border border-white/[0.06] flex items-center justify-center text-slate-500 hover:text-slate-300 hover:border-white/10 transition-colors"
                >
                  <Icon className="h-3.5 w-3.5" />
                </motion.a>
              ))}
            </div>
          </div>

          {/* Nav groups */}
          <div className="lg:col-span-4 grid grid-cols-2 sm:grid-cols-4 gap-8">
            {NAV_GROUPS.map((group) => (
              <div key={group.title}>
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-4">
                  {group.title}
                </p>
                <ul className="space-y-2.5">
                  {group.links.map((link) => (
                    <li key={link.label}>
                      {"external" in link && link.external ? (
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors group"
                        >
                          {link.label}
                          <ExternalLink className="h-2.5 w-2.5 opacity-0 group-hover:opacity-60 transition-opacity" />
                        </a>
                      ) : (
                        <Link
                          href={link.href}
                          className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors group"
                        >
                          {link.label}
                          <ArrowUpRight className="h-2.5 w-2.5 opacity-0 group-hover:opacity-60 transition-opacity" />
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-white/[0.05]" />

        {/* Bottom bar */}
        <div className="py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <p className="text-xs text-slate-600">
              © {new Date().getFullYear()} FlowSync Revenue Intelligence
            </p>
            <span className="text-slate-700">·</span>
            <p className="text-xs text-slate-600">
              Portfolio project — fictional company
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Stack badges */}
            {["Next.js", "FastAPI", "PostgreSQL", "dbt"].map((tech) => (
              <span
                key={tech}
                className="text-[9px] font-semibold text-slate-600 bg-slate-900/60 border border-white/[0.04] rounded px-2 py-0.5"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
