import { Skeleton } from "@/components/ui/skeleton";

function KPICardSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-32" />
      <Skeleton className="h-3 w-20" />
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
            style={{ height: `${30 + Math.random() * 70}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
      <Skeleton className="h-5 w-48" />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardLoading() {
  return (
    <div className="flex-1 overflow-auto">
      {/* Page header skeleton */}
      <div className="border-b border-border/50 bg-background/95 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-7 w-52" />
            <Skeleton className="h-4 w-80" />
          </div>
          <div className="flex items-center gap-3">
            <Skeleton className="h-9 w-32 rounded-lg" />
            <Skeleton className="h-9 w-9 rounded-lg" />
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* KPI Cards row */}
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <KPICardSkeleton key={i} />
          ))}
        </div>

        {/* Main charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ChartSkeleton height="h-80" />
          </div>
          <ChartSkeleton height="h-80" />
        </div>

        {/* Secondary charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton height="h-72" />
          <ChartSkeleton height="h-72" />
        </div>

        {/* Table row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TableSkeleton />
          <TableSkeleton />
        </div>
      </div>
    </div>
  );
}
