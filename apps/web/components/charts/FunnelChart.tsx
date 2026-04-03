"use client";

import React from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from "recharts";
import { formatPercent, CHART_PALETTE } from "@/lib/formatters";
import type { FunnelConversion, ConversionByChannel } from "@/types";

// ---------------------------------------------------------------------------
// Main Funnel Visualization
// ---------------------------------------------------------------------------
interface FunnelVizProps {
  data: FunnelConversion;
}

export function FunnelViz({ data }: FunnelVizProps) {
  const stages = [
    { label: "Leads", value: data.total_leads, color: CHART_PALETTE[0], pct: 100 },
    {
      label: "Trial Starts",
      value: data.trial_starts,
      color: CHART_PALETTE[2],
      pct: data.lead_to_trial_rate,
    },
    {
      label: "Paid Conversions",
      value: data.paid_conversions,
      color: CHART_PALETTE[1],
      pct: data.overall_conversion_rate,
    },
  ];

  const maxVal = data.total_leads;

  return (
    <div className="space-y-3">
      {stages.map((stage, i) => {
        const widthPct = (stage.value / maxVal) * 100;
        return (
          <div key={stage.label} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-foreground">{stage.label}</span>
              <div className="flex items-center gap-3">
                <span className="text-muted-foreground">{stage.value.toLocaleString()}</span>
                {i > 0 && (
                  <span className="font-semibold" style={{ color: stage.color }}>
                    {formatPercent(stage.pct)}
                  </span>
                )}
              </div>
            </div>
            <div className="h-8 w-full rounded bg-muted/30 overflow-hidden">
              <div
                className="h-full rounded transition-all duration-700 ease-out flex items-center justify-end pr-2"
                style={{
                  width: `${widthPct}%`,
                  backgroundColor: stage.color,
                  opacity: 0.85,
                }}
              />
            </div>
            {i < stages.length - 1 && (
              <div className="flex items-center gap-1 text-[10px] text-muted-foreground pl-1">
                <span>↓</span>
                <span>
                  {formatPercent(stages[i + 1].pct)} conversion rate
                </span>
              </div>
            )}
          </div>
        );
      })}
      <div className="mt-4 grid grid-cols-2 gap-3 pt-3 border-t border-border/50">
        <div className="text-center">
          <p className="text-xs text-muted-foreground">Avg Days to Convert</p>
          <p className="text-lg font-bold text-foreground">{data.avg_days_to_convert.toFixed(0)}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground">Trial Engagement</p>
          <p className="text-lg font-bold text-foreground">{data.avg_trial_engagement.toFixed(1)}</p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Conversion by Channel Bar Chart
// ---------------------------------------------------------------------------
interface ConversionByChannelChartProps {
  data: ConversionByChannel[];
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
            <span className="text-muted-foreground">{entry.name}</span>
          </div>
          <span className="font-medium text-foreground">
            {formatPercent(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
};

export function ConversionByChannelChart({ data, height = 280 }: ConversionByChannelChartProps) {
  const sorted = [...data].sort((a, b) => b.trial_to_paid_rate - a.trial_to_paid_rate);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={sorted} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.5} horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(v: number) => `${v.toFixed(0)}%`}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          axisLine={false}
          tickLine={false}
          domain={[0, 100]}
        />
        <YAxis
          type="category"
          dataKey="channel"
          tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          axisLine={false}
          tickLine={false}
          width={80}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }} />
        <Bar dataKey="trial_to_paid_rate" name="Trial→Paid Rate" radius={[0, 4, 4, 0]}>
          {sorted.map((_, index) => (
            <Cell key={`cell-${index}`} fill={CHART_PALETTE[index % CHART_PALETTE.length]} opacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
