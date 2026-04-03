import Link from "next/link";
import { BarChart3, Home, ArrowLeft, Search } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(to right, hsl(var(--foreground)) 1px, transparent 1px),
            linear-gradient(to bottom, hsl(var(--foreground)) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />

      {/* Gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-primary/5 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-violet-500/5 blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-lg w-full text-center space-y-8">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <BarChart3 className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-lg font-bold tracking-tight text-foreground">
            FlowSync BI
          </span>
        </div>

        {/* 404 display */}
        <div className="space-y-2">
          <div className="relative inline-block">
            <span
              className="text-[8rem] font-black leading-none tracking-tighter select-none"
              style={{
                background:
                  "linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.3) 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              404
            </span>
            {/* Decorative chart bars behind the 404 */}
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-end gap-1 opacity-10 pointer-events-none">
              {[40, 65, 30, 80, 55, 70, 45, 90, 60, 75].map((h, i) => (
                <div
                  key={i}
                  className="w-3 rounded-t-sm bg-primary"
                  style={{ height: `${h}px` }}
                />
              ))}
            </div>
          </div>

          <h1 className="text-2xl font-bold text-foreground">
            Dashboard Not Found
          </h1>
          <p className="text-muted-foreground leading-relaxed">
            The analytics page you&apos;re looking for doesn&apos;t exist or
            has been moved. Check the URL or navigate back to the dashboard.
          </p>
        </div>

        {/* Quick links */}
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/dashboard"
            className="group flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3 text-sm font-medium text-foreground shadow-sm transition-all hover:border-primary/50 hover:bg-primary/5 hover:shadow-md"
          >
            <Home className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            Executive Overview
          </Link>
          <Link
            href="/dashboard/revenue"
            className="group flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3 text-sm font-medium text-foreground shadow-sm transition-all hover:border-primary/50 hover:bg-primary/5 hover:shadow-md"
          >
            <BarChart3 className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            Revenue Movements
          </Link>
          <Link
            href="/dashboard/cohorts"
            className="group flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3 text-sm font-medium text-foreground shadow-sm transition-all hover:border-primary/50 hover:bg-primary/5 hover:shadow-md"
          >
            <Search className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            Cohort Retention
          </Link>
          <Link
            href="/"
            className="group flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3 text-sm font-medium text-foreground shadow-sm transition-all hover:border-primary/50 hover:bg-primary/5 hover:shadow-md"
          >
            <ArrowLeft className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
            Back to Landing
          </Link>
        </div>

        {/* Primary CTA */}
        <Link
          href="/dashboard"
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-8 py-3 text-sm font-semibold text-primary-foreground shadow-lg transition-all hover:bg-primary/90 hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0"
        >
          <Home className="h-4 w-4" />
          Go to Dashboard
        </Link>

        {/* Footer note */}
        <p className="text-xs text-muted-foreground">
          FlowSync Revenue Intelligence &mdash; Fictional B2B SaaS Portfolio Project
        </p>
      </div>
    </div>
  );
}
