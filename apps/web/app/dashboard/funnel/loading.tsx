import { Skeleton } from "@/components/ui/skeleton";

function FunnelVizSkeleton() {
  const stages = [100, 78, 52, 34, 22];
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-44" />
        <Skeleton className="h-8 w-28 rounded-lg" />
      </div>
      {/* Funnel shape */}
      <div className="flex flex-col items-center gap-1 py-4">
        {stages.map((width, i) => (
          <div key={i} className="flex items-center gap-4 w-full">
            <Skeleton className="h-3 w-20 shrink-0" />
            <div className="flex-1 flex justify-center">
              <Skeleton
                className="h-10 rounded-sm"
                style={{ width: `${width}%` }}
              />
            </div>
            <Skeleton className="h-3 w-16 shrink-0" />
          </div>
        ))}
      </div>
      {/* Conversion rates row */}
      <div className="grid grid-cols-4 gap-3 pt-2 border-t border-border/30">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="text-center space-y-1">
            <Skeleton className="h-5 w-12 mx-auto" />
            <Skeleton className="h-3 w-16 mx-auto" />
          </div>
        ))}
      </div>
    </div>
  );
}

function ChannelChartSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4 h-72">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-44" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
      {/* Grouped bar chart */}
      <div className="flex-1 flex items-end gap-3 pt-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex-1 flex items-end gap-0.5">
            <Skeleton
              className="flex-1 rounded-t-sm"
              style={{ height: `${30 + Math.random() * 70}%` }}
            />
            <Skeleton
              className="flex-1 rounded-t-sm"
              style={{ height: `${20 + Math.random() * 60}%` }}
            />
            <Skeleton
              className="flex-1 rounded-t-sm"
              style={{ height: `${10 + Math.random() * 50}%` }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function SalesCycleSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4 h-64">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
      {/* Horizontal bars */}
      <div className="space-y-3 pt-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-3 w-20 shrink-0" />
            <div className="flex-1 h-5 rounded-sm bg-muted overflow-hidden">
              <Skeleton
                className="h-full rounded-sm"
                style={{ width: `${20 + Math.random() * 75}%` }}
              />
            </div>
            <Skeleton className="h-3 w-12 shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
}

function ExpansionTableSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
      {/* Header */}
      <div className="flex gap-4 pb-2 border-b border-border/30">
        {["Segment", "Plan", "Channel", "Expansion MRR", "Accounts", "Avg/Account"].map((_, i) => (
          <Skeleton key={i} className="h-3 flex-1" />
        ))}
      </div>
      {/* Rows */}
      <div className="space-y-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-6 w-16 rounded-full flex-1" />
            <Skeleton className="h-6 w-16 rounded-full flex-1" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 flex-1" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function FunnelLoading() {
  return (
    <div className="flex-1 overflow-auto">
      {/* Page header */}
      <div className="border-b border-border/50 bg-background/95 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-7 w-44" />
            <Skeleton className="h-4 w-72" />
          </div>
          <Skeleton className="h-9 w-32 rounded-lg" />
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

        {/* Funnel viz + Channel chart */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FunnelVizSkeleton />
          <ChannelChartSkeleton />
        </div>

        {/* Sales cycle + Trial usage */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SalesCycleSkeleton />
          <SalesCycleSkeleton />
        </div>

        {/* Expansion by segment table */}
        <ExpansionTableSkeleton />
      </div>
    </div>
  );
}
