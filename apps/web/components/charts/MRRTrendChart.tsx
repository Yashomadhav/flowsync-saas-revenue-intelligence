"use client";

import React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { formatMRR, formatMonth, CHART_PALETTE } from "@/lib/formatters";
import type { MRRTrendPoint } from "@/types";

interface MRRTrendChartProps {
  data: MRRTrendPoint[];
  height?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card/95 backdrop-blur-sm p-3 shadow-xl text-xs">
      <p className="font-semibold text-foreground mb-2">{label}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4 py-0.5">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-muted-foreground capitalize">{entry.name}</span>
          </div>
          <span className="font-medium text-foreground">{formatMRR(entry.value)}</span>
        </div>
      ))}
    </div>
  );
};

export function MRRTrendChart({ data, height = 300 }: MRRTrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
        <defs>
          <linearGradient id="mrrGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={CHART_PALETTE[0]} stopOpacity={0.15} />
            <stop offset="95%" stopColor={CHART_PALETTE[0]} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="arrGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={CHART_PALETTE[1]} stopOpacity={0.1} />
            <stop offset="95%" stopColor={CHART_PALETTE[1]} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} />
        <XAxis
          dataKey="month"
          tickFormatter={formatMonth}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          axisLine={false}
          tickLine={false}
          width={55}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 11, paddingTop: 12 }}
          formatter={(value) => <span className="text-muted-foreground capitalize">{value}</span>}
        />
        <Area
          type="monotone"
          dataKey="total_mrr"
          name="MRR"
          stroke={CHART_PALETTE[0]}
          strokeWidth={2}
          fill="url(#mrrGradient)"
          dot={false}
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
        <Area
          type="monotone"
          dataKey="arr"
          name="ARR"
          stroke={CHART_PALETTE[1]}
          strokeWidth={1.5}
          strokeDasharray="4 4"
          fill="url(#arrGradient)"
          dot={false}
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
