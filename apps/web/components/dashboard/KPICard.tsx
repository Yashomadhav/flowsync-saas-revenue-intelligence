"use client";

import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatCurrency, formatPercent } from "@/lib/formatters";

interface KPICardProps {
  title: string;
  value: string | number;
  delta?: number;
  deltaLabel?: string;
  icon?: LucideIcon;
  iconColor?: string;
  format?: "currency" | "percent" | "number" | "raw";
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  invertDelta?: boolean; // for churn — down is good
  className?: string;
  index?: number;
}

export function KPICard({
  title,
  value,
  delta,
  deltaLabel = "vs last month",
  icon: Icon,
  iconColor = "text-brand-400",
  format = "raw",
  subtitle,
  invertDelta = false,
  className,
  index = 0,
}: KPICardProps) {
  const isPositive = delta !== undefined ? (invertDelta ? delta < 0 : delta > 0) : null;
  const isNeutral = delta === 0;

  const formattedValue =
    format === "currency"
      ? formatCurrency(Number(value))
      : format === "percent"
      ? formatPercent(Number(value))
      : format === "number"
      ? Number(value).toLocaleString()
      : String(value);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08, ease: "easeOut" }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      className={cn(
        "group relative overflow-hidden rounded-xl border border-border/50 bg-card p-5 shadow-sm transition-shadow hover:shadow-md hover:shadow-black/5",
        className
      )}
    >
      {/* Gradient accent */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-500/3 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      {/* Top row */}
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</p>
        {Icon && (
          <div className={cn("rounded-lg p-1.5 bg-muted/50", iconColor)}>
            <Icon className="h-3.5 w-3.5" />
          </div>
        )}
      </div>

      {/* Value */}
      <div className="mb-2">
        <p className="text-2xl font-bold text-foreground tracking-tight">{formattedValue}</p>
        {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
      </div>

      {/* Delta */}
      {delta !== undefined && (
        <div className="flex items-center gap-1.5">
          <div
            className={cn(
              "flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-xs font-medium",
              isNeutral
                ? "bg-muted text-muted-foreground"
                : isPositive
                ? "bg-emerald-500/10 text-emerald-500"
                : "bg-red-500/10 text-red-500"
            )}
          >
            {isNeutral ? (
              <Minus className="h-3 w-3" />
            ) : isPositive ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            <span>{Math.abs(delta).toFixed(1)}%</span>
          </div>
          <span className="text-xs text-muted-foreground">{deltaLabel}</span>
        </div>
      )}
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Skeleton loader
// ---------------------------------------------------------------------------
export function KPICardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-xl border border-border/50 bg-card p-5 animate-pulse", className)}>
      <div className="flex items-start justify-between mb-3">
        <div className="h-3 w-24 rounded bg-muted" />
        <div className="h-7 w-7 rounded-lg bg-muted" />
      </div>
      <div className="h-8 w-32 rounded bg-muted mb-2" />
      <div className="h-5 w-20 rounded-full bg-muted" />
    </div>
  );
}
