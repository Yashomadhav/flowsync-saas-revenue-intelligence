import { Skeleton } from "@/components/ui/skeleton";

function HeatmapSkeleton() {
  const rows = 12;
  const cols = 13;
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-8 w-32 rounded-lg" />
      </div>
      {/* Column headers */}
      <div className="flex gap-1 pl-20">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-3 flex-1" />
        ))}
      </div>
      {/* Heatmap rows */}
      <div className="space-y-1">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex items-center gap-1">
            <Skeleton className="h-7 w-16 shrink-0" />
            {Array.from({ length: cols }).map((_, c) => (
              <Skeleton
                key={c}
                className="h-7 flex-1 rounded-sm"
                style={{ opacity: c > rows - r ? 0.15 : 0.4 + Math.random() * 0.6 }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function ChartSkeleton({ height = "h-64" }: { height?: string }) {
  return (
    <div className={`rounded-xl border border-border/50 bg-card p-6 space-y-4 ${height}`}>
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
      <div className="flex-1 flex items-end gap-2 pt-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-t-sm"
            style={{ height: `${25 + Math.random() * 75}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function KPIRowSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-xl border border-border/50 bg-card p-5 space-y-2">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-8 w-28" />
          <Skeleton className="h-3 w-16" />
        </div>
      ))}
    </div>
  );
}

function SegmentTableSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
      <Skeleton className="h-5 w-44" />
      <div className="space-y-2">
        {/* Header */}
        <div className="flex gap-4 pb-2 border-b border-border/30">
          {["Segment", "Accounts", "Avg NRR", "Logo Churn", "Rev Churn"].map((_, i) => (
            <Skeleton key={i} className="h-3 flex-1" />
          ))}
        </div>
        {/* Rows */}
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-6 w-16 rounded-full flex-1" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 flex-1" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function CohortsLoading() {
  return (
    <div className="flex-1 overflow-auto">
      {/* Page header */}
      <div className="border-b border-border/50 bg-background/95 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-7 w-52" />
            <Skeleton className="h-4 w-80" />
          </div>
          <Skeleton className="h-9 w-32 rounded-lg" />
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* KPI row */}
        <KPIRowSkeleton />

        {/* Customer cohort heatmap — full width */}
        <HeatmapSkeleton />

        {/* Revenue cohort heatmap — full width */}
        <HeatmapSkeleton />

        {/* Churn trend + NRR by cohort */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton height="h-72" />
          <ChartSkeleton height="h-72" />
        </div>

        {/* Retention by segment table */}
        <SegmentTableSkeleton />
      </div>
    </div>
  );
}
