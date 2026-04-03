import { Skeleton } from "@/components/ui/skeleton";

function ScoreDistributionSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4 h-72">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
      {/* Horizontal bar chart */}
      <div className="space-y-3 pt-2">
        {["Critical (0–40)", "At Risk (41–60)", "Neutral (61–75)", "Healthy (76–90)", "Champion (91–100)"].map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-3 w-24 shrink-0" />
            <div className="flex-1 h-6 rounded-sm bg-muted overflow-hidden">
              <Skeleton
                className="h-full rounded-sm"
                style={{ width: `${15 + Math.random() * 70}%` }}
              />
            </div>
            <Skeleton className="h-3 w-8 shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
}

function QuadrantSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4 h-72">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-44" />
        <Skeleton className="h-8 w-28 rounded-lg" />
      </div>
      {/* Scatter plot placeholder */}
      <div className="relative flex-1 h-48 border border-border/30 rounded-lg bg-muted/20">
        {/* Quadrant lines */}
        <div className="absolute inset-0 flex">
          <div className="flex-1 border-r border-border/30" />
          <div className="flex-1" />
        </div>
        <div className="absolute inset-0 flex flex-col">
          <div className="flex-1 border-b border-border/30" />
          <div className="flex-1" />
        </div>
        {/* Scatter dots */}
        {Array.from({ length: 20 }).map((_, i) => (
          <Skeleton
            key={i}
            className="absolute rounded-full"
            style={{
              width: 10 + Math.random() * 8,
              height: 10 + Math.random() * 8,
              left: `${5 + Math.random() * 88}%`,
              top: `${5 + Math.random() * 88}%`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function UsageTrendSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4 h-64">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
      <div className="flex-1 flex items-end gap-2 pt-2">
        {Array.from({ length: 12 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-t-sm"
            style={{ height: `${20 + Math.random() * 80}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function RiskyAccountsTableSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Skeleton className="h-5 w-44" />
          <Skeleton className="h-3 w-64" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-24 rounded-lg" />
          <Skeleton className="h-8 w-24 rounded-lg" />
        </div>
      </div>
      {/* Table header */}
      <div className="flex gap-4 pb-2 border-b border-border/30">
        {["Account", "Plan", "MRR", "Health", "Risk Flags", "Action"].map((_, i) => (
          <Skeleton key={i} className="h-3 flex-1" />
        ))}
      </div>
      {/* Table rows */}
      <div className="space-y-3">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="flex items-center gap-2 flex-1">
              <Skeleton className="h-8 w-8 rounded-full shrink-0" />
              <div className="space-y-1">
                <Skeleton className="h-3 w-28" />
                <Skeleton className="h-2 w-20" />
              </div>
            </div>
            <Skeleton className="h-6 w-16 rounded-full flex-1" />
            <Skeleton className="h-4 w-16 flex-1" />
            {/* Health score bar */}
            <div className="flex items-center gap-2 flex-1">
              <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                <Skeleton
                  className="h-full rounded-full"
                  style={{ width: `${10 + Math.random() * 60}%` }}
                />
              </div>
              <Skeleton className="h-3 w-8 shrink-0" />
            </div>
            {/* Risk flags */}
            <div className="flex gap-1 flex-1">
              {Array.from({ length: Math.ceil(Math.random() * 3) }).map((_, j) => (
                <Skeleton key={j} className="h-5 w-5 rounded" />
              ))}
            </div>
            <Skeleton className="h-7 w-20 rounded-lg flex-1" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function HealthLoading() {
  return (
    <div className="flex-1 overflow-auto">
      {/* Page header */}
      <div className="border-b border-border/50 bg-background/95 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-7 w-56" />
            <Skeleton className="h-4 w-80" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-9 w-28 rounded-lg" />
            <Skeleton className="h-9 w-28 rounded-lg" />
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* KPI row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-border/50 bg-card p-5 space-y-2">
              <Skeleton className="h-3 w-28" />
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-3 w-16" />
            </div>
          ))}
        </div>

        {/* Score distribution + Quadrant */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ScoreDistributionSkeleton />
          <QuadrantSkeleton />
        </div>

        {/* Usage trend + Support burden */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <UsageTrendSkeleton />
          <UsageTrendSkeleton />
        </div>

        {/* At-risk accounts table */}
        <RiskyAccountsTableSkeleton />
      </div>
    </div>
  );
}
