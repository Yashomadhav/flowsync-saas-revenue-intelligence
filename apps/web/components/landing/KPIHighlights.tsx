"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import { TrendingUp, Users, DollarSign, Activity, BarChart2, Target } from "lucide-react";

interface KPIItem {
  label: string;
  value: number;
  suffix: string;
  prefix?: string;
  description: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  borderColor: string;
}

const kpis: KPIItem[] = [
  {
    label: "Monthly Recurring Revenue",
    value: 847,
    suffix: "K",
    prefix: "$",
    description: "Total normalized monthly revenue",
    icon: DollarSign,
    color: "text-violet-400",
    bgColor: "bg-violet-500/10",
    borderColor: "border-violet-500/20",
  },
  {
    label: "Net Revenue Retention",
    value: 118,
    suffix: "%",
    description: "Expansion exceeds churn",
    icon: TrendingUp,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20",
  },
  {
    label: "Active Accounts",
    value: 1247,
    suffix: "",
    description: "Paying customers this month",
    icon: Users,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20",
  },
  {
    label: "Annual Run Rate",
    value: 10.2,
    suffix: "M",
    prefix: "$",
    description: "MRR × 12 annualized",
    icon: BarChart2,
    color: "text-indigo-400",
    bgColor: "bg-indigo-500/10",
    borderColor: "border-indigo-500/20",
  },
  {
    label: "Trial → Paid Rate",
    value: 34,
    suffix: "%",
    description: "Conversion from free trial",
    icon: Target,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/20",
  },
  {
    label: "Avg Health Score",
    value: 72,
    suffix: "/100",
    description: "Composite account health",
    icon: Activity,
    color: "text-rose-400",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/20",
  },
];

function AnimatedNumber({ value, prefix = "", suffix = "", inView }: {
  value: number; prefix?: string; suffix?: string; inView: boolean;
}) {
  const [display, setDisplay] = useState(0);
  const startRef = useRef<number | null>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (!inView) return;
    const duration = 1800;
    const start = performance.now();
    startRef.current = start;

    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(parseFloat((eased * value).toFixed(value < 10 ? 1 : 0)));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [inView, value]);

  return (
    <span>
      {prefix}{display < 10 ? display.toFixed(1) : Math.round(display).toLocaleString()}{suffix}
    </span>
  );
}

export function KPIHighlights() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="metrics" className="py-24 bg-slate-950 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-violet-600/5 rounded-full blur-[100px]" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-violet-500/10 border border-violet-500/20 rounded-full px-4 py-1.5 mb-4">
            <BarChart2 className="h-3.5 w-3.5 text-violet-400" />
            <span className="text-xs font-medium text-violet-300">Live Metrics</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Every SaaS Metric That Matters
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            From MRR movements to cohort retention — FlowSync tracks the complete
            revenue picture with real-time precision.
          </p>
        </motion.div>

        {/* KPI grid */}
        <div ref={ref} className="grid grid-cols-2 md:grid-cols-3 gap-4 lg:gap-6">
          {kpis.map((kpi, i) => {
            const Icon = kpi.icon;
            return (
              <motion.div
                key={kpi.label}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
                className={`relative bg-slate-900/60 backdrop-blur-sm border ${kpi.borderColor} rounded-2xl p-6 group cursor-default`}
              >
                {/* Hover glow */}
                <div className={`absolute inset-0 ${kpi.bgColor} rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />

                <div className="relative">
                  <div className={`inline-flex items-center justify-center h-10 w-10 rounded-xl ${kpi.bgColor} border ${kpi.borderColor} mb-4`}>
                    <Icon className={`h-5 w-5 ${kpi.color}`} />
                  </div>

                  <div className={`text-3xl font-bold ${kpi.color} mb-1 tabular-nums`}>
                    <AnimatedNumber
                      value={kpi.value}
                      prefix={kpi.prefix}
                      suffix={kpi.suffix}
                      inView={inView}
                    />
                  </div>

                  <p className="text-sm font-semibold text-white mb-1">{kpi.label}</p>
                  <p className="text-xs text-slate-500">{kpi.description}</p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Bottom note */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="text-center text-xs text-slate-600 mt-8"
        >
          Metrics computed from synthetic FlowSync data · 500 accounts · 24 months history
        </motion.p>
      </div>
    </section>
  );
}
