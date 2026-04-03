"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DashboardError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log to error reporting service in production
    console.error("[Dashboard Error]", error);
  }, [error]);

  return (
    <div className="flex-1 flex items-center justify-center min-h-[60vh] p-6">
      <div className="max-w-md w-full text-center space-y-6">
        {/* Icon */}
        <div className="flex justify-center">
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-destructive/20 blur-xl" />
            <div className="relative flex h-20 w-20 items-center justify-center rounded-full border border-destructive/30 bg-destructive/10">
              <AlertTriangle className="h-9 w-9 text-destructive" />
            </div>
          </div>
        </div>

        {/* Heading */}
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            Dashboard Error
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Something went wrong while loading this dashboard page. This may be
            a temporary issue with the data pipeline or API connection.
          </p>
        </div>

        {/* Error detail (dev only) */}
        {process.env.NODE_ENV === "development" && error.message && (
          <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 text-left">
            <p className="text-xs font-mono text-destructive/80 break-all">
              {error.message}
            </p>
            {error.digest && (
              <p className="mt-1 text-xs text-muted-foreground">
                Digest: {error.digest}
              </p>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={reset}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-all hover:bg-primary/90 hover:shadow-md active:scale-95"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-background px-5 py-2.5 text-sm font-medium text-foreground shadow-sm transition-all hover:bg-muted active:scale-95"
          >
            <Home className="h-4 w-4" />
            Executive Overview
          </Link>
        </div>

        {/* Hint */}
        <p className="text-xs text-muted-foreground">
          The dashboard uses mock data as a fallback — if the API is
          unavailable, data will still display from the built-in dataset.
        </p>
      </div>
    </div>
  );
}
