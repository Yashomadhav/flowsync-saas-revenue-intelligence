"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  TrendingUp,
  Users,
  Heart,
  ChevronLeft,
  ChevronRight,
  Zap,
  BarChart3,
  Settings,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  {
    label: "Executive Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "MRR, ARR, NRR at a glance",
  },
  {
    label: "Revenue Movements",
    href: "/dashboard/revenue",
    icon: TrendingUp,
    description: "MRR bridge & account movements",
  },
  {
    label: "Cohort Retention",
    href: "/dashboard/cohorts",
    icon: Users,
    description: "Retention heatmaps & NRR",
  },
  {
    label: "Customer Health",
    href: "/dashboard/health",
    icon: Heart,
    description: "Health scores & churn risk",
  },
  {
    label: "Funnel & Growth",
    href: "/dashboard/funnel",
    icon: BarChart3,
    description: "Lead-to-paid conversion",
  },
];

const BOTTOM_ITEMS = [
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
  { label: "Help", href: "/dashboard/help", icon: HelpCircle },
];

export function DashboardSidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 256 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="relative flex h-screen flex-col border-r border-border/50 bg-card/50 backdrop-blur-sm"
    >
      {/* Logo */}
      <div className="flex h-16 items-center border-b border-border/50 px-4">
        <Link href="/" className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-600 shadow-lg shadow-brand-500/25">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <p className="text-sm font-bold text-foreground leading-none">FlowSync</p>
                <p className="text-[10px] text-muted-foreground leading-none mt-0.5">Revenue Intelligence</p>
              </motion.div>
            )}
          </AnimatePresence>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2">
        <div className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);
            const Icon = item.icon;

            return (
              <Link key={item.href} href={item.href}>
                <motion.div
                  whileHover={{ x: collapsed ? 0 : 2 }}
                  className={cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all duration-200",
                    isActive
                      ? "bg-brand-500/10 text-brand-400 font-medium"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors",
                      isActive ? "text-brand-400" : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                  <AnimatePresence>
                    {!collapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.15 }}
                        className="truncate"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                  {isActive && (
                    <motion.div
                      layoutId="activeIndicator"
                      className="absolute left-0 h-6 w-0.5 rounded-r-full bg-brand-500"
                    />
                  )}
                </motion.div>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Bottom items */}
      <div className="border-t border-border/50 py-3 px-2 space-y-1">
        {BOTTOM_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href}>
              <div className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors">
                <Icon className="h-4 w-4 shrink-0" />
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="truncate"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-background shadow-sm hover:bg-accent transition-colors z-10"
      >
        {collapsed ? (
          <ChevronRight className="h-3 w-3 text-muted-foreground" />
        ) : (
          <ChevronLeft className="h-3 w-3 text-muted-foreground" />
        )}
      </button>
    </motion.aside>
  );
}
