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
  Cell,
  ReferenceLine,
} from "recharts";
import { formatMRR, MOVEMENT_COLORS } from "@/lib/formatters";
import type { WaterfallItem } from "@/types";

interface WaterfallChartProps {
  data: WaterfallItem[];
  height?: number;
}

// Map waterfall item type + label to a color
function getBarColor(item: WaterfallItem): string {
  const label = item.label.toLowerCase();
  if (item.type === "start") return MOVEMENT_COLORS.existing;
  if (item.type === "end") return "#3b82f6"; // blue for ending MRR
  if (label.includes("new")) return MOVEMENT_COLORS.new;
  if (label.includes("expansion")) return MOVEMENT_COLORS.expansion;
  if (label.includes("reactivation")) return MOVEMENT_COLORS.reactivation;
  if (label.includes("contraction")) return MOVEMENT_COLORS.contraction;
  if (label.includes("churn")) return MOVEMENT_COLORS.churn;
  return item.type === "positive" ? MOVEMENT_COLORS.new : MOVEMENT_COLORS.churn;
}

// Build stacked bar data for waterfall effect
function buildWaterfallData(items: WaterfallItem[]) {
  let running = 0;
  return items.map((item) => {
    const isEnd = item.type === "end";
    const base = isEnd ? 0 : item.value >= 0 ? running : running + item.value;
    const bar = isEnd ? Math.abs(running + item.value) : Math.abs(item.value);
    if (!isEnd) running += item.value;
    return { ...item, base, bar };
  });
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const item = payload[0]?.payload as WaterfallItem;
  const sign = item.type === "negative" ? "" : item.type === "start" || item.type === "end" ? "" : "+";
  return (
    <div className="rounded-lg border border-border bg-card/95 backdrop-blur-sm p-3 shadow-xl text-xs">
      <p className="font-semibold text-foreground mb-1">{item.label}</p>
      <p className="text-muted-foreground">
        {sign}{formatMRR(item.value)}
      </p>
    </div>
  );
};

export function WaterfallChart({ data, height = 280 }: WaterfallChartProps) {
  const chartData = buildWaterfallData(data);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 0 }} barCategoryGap="25%">
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} vertical={false} />
        <XAxis
          dataKey="label"
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
        <ReferenceLine y={0} stroke="hsl(var(--border))" strokeWidth={1} />
        {/* Invisible base bar for offset */}
        <Bar dataKey="base" stackId="waterfall" fill="transparent" />
        {/* Visible value bar */}
        <Bar dataKey="bar" stackId="waterfall" radius={[3, 3, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={getBarColor(entry)}
              opacity={0.9}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
