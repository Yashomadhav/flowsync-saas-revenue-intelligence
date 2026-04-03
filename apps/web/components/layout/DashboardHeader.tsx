"use client";

import React from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Bell, Search, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DashboardHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function DashboardHeader({ title, description, actions }: DashboardHeaderProps) {
  const { theme, setTheme } = useTheme();

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-border/50 bg-background/80 backdrop-blur-sm px-6">
      {/* Title */}
      <div className="flex-1 min-w-0">
        <h1 className="text-lg font-semibold text-foreground truncate">{title}</h1>
        {description && (
          <p className="text-xs text-muted-foreground truncate">{description}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {actions}

        {/* Search */}
        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
          <Search className="h-4 w-4" />
        </Button>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative h-8 w-8 text-muted-foreground">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-brand-500" />
        </Button>

        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>

        {/* View landing page */}
        <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs" asChild>
          <a href="/" target="_blank" rel="noopener noreferrer">
            <ExternalLink className="h-3 w-3" />
            Landing
          </a>
        </Button>
      </div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// Page header for dashboard sections
// ---------------------------------------------------------------------------
interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: string;
  children?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, badge, children, className }: PageHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between", className)}>
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">{title}</h2>
          {badge && (
            <span className="rounded-full bg-brand-500/10 px-2 py-0.5 text-xs font-medium text-brand-400">
              {badge}
            </span>
          )}
        </div>
        {description && (
          <p className="text-sm text-muted-foreground mt-0.5">{description}</p>
        )}
      </div>
      {children && <div className="flex items-center gap-2 mt-2 sm:mt-0">{children}</div>}
    </div>
  );
}
