"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { formatMRR, formatMonth, MOVEMENT_COLORS } from "@/lib/formatters";
import type { MRRBridgePoint } from "@/types";

interface MRRBridgeChartProps {
  data: MRRBridgePoint[];
  height?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card/95 backdrop-blur-sm p-3 shadow-xl text-xs min-w-[180px]">
      <p className="font-semibold text-foreground mb-2">{formatMonth(label)}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4 py-0.5">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-muted-foreground capitalize">{entry.name}</span>
          </div>
          <span className={`font-medium ${entry.value < 0 ? "text-red-400" : "text-foreground"}`}>
            {entry.value < 0 ? "" : "+"}{formatMRR(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
};

export function MRRBridgeChart({ data, height = 300 }: MRRBridgeChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 0 }} barCategoryGap="20%">
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
        <XAxis
          dataKey="month"
          tickFormatter={formatMonth}
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          axisLine={false}
          tickLine={false}
          width={55}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }} />
        <Legend
          wrapperStyle={{ fontSize: 11, paddingTop: 12 }}
          formatter={(value: string) => <span className="text-muted-foreground capitalize">{value}</span>}
        />
        <Bar dataKey="new_mrr" name="New" stackId="a" fill={MOVEMENT_COLORS.new} radius={[0, 0, 0, 0]} />
        <Bar dataKey="expansion_mrr" name="Expansion" stackId="a" fill={MOVEMENT_COLORS.expansion} />
        <Bar dataKey="reactivation_mrr" name="Reactivation" stackId="a" fill={MOVEMENT_COLORS.reactivation} />
        <Bar dataKey="contraction_mrr" name="Contraction" stackId="b" fill={MOVEMENT_COLORS.contraction} />
        <Bar dataKey="churned_mrr" name="Churn" stackId="b" fill={MOVEMENT_COLORS.churn} radius={[0, 0, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
