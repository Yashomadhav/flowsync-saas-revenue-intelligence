import { Skeleton } from "@/components/ui/skeleton";

function ChartSkeleton({ height = "h-72" }: { height?: string }) {
  return (
    <div className={`rounded-xl border border-border/50 bg-card p-6 space-y-4 ${height}`}>
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-44" />
        <Skeleton className="h-8 w-28 rounded-lg" />
      </div>
      <div className="flex-1 flex items-end gap-1.5 pt-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="flex-1 flex flex-col gap-1 items-center">
            <Skeleton
              className="w-full rounded-t-sm"
              style={{ height: `${20 + Math.random() * 80}%` }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function TableSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-8 w-20 rounded-lg" />
      </div>
      {/* Table header */}
      <div className="flex gap-4 pb-2 border-b border-border/30">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-3 w-20 ml-auto" />
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-16" />
      </div>
      {/* Table rows */}
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-4 w-36" />
            <Skeleton className="h-4 w-20 ml-auto" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function RevenueLoading() {
  return (
    <div className="flex-1 overflow-auto">
      {/* Page header */}
      <div className="border-b border-border/50 bg-background/95 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-4 w-72" />
          </div>
          <Skeleton className="h-9 w-32 rounded-lg" />
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* MRR Bridge chart — full width */}
        <ChartSkeleton height="h-80" />

        {/* Two charts side by side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton height="h-72" />
          <ChartSkeleton height="h-72" />
        </div>

        {/* Account movements table */}
        <TableSkeleton rows={8} />

        {/* Invoice trends */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton height="h-64" />
          <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
            <Skeleton className="h-5 w-40" />
            <div className="grid grid-cols-2 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-2 rounded-lg border border-border/30 p-4">
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="h-7 w-20" />
                  <Skeleton className="h-3 w-16" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
