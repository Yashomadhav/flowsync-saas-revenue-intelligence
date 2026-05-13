import numeral from "numeral";

export function formatMRR(value: number): string {
  if (value >= 1_000_000) return numeral(value).format("$0.0a");
  if (value >= 1_000) return numeral(value).format("$0.0a");
  return numeral(value).format("$0,0");
}

export function formatARR(value: number): string {
  return formatMRR(value);
}

export function formatCurrency(value: number): string {
  return numeral(value).format("$0,0.00");
}

export function formatPercent(value: number): string {
  return numeral(value / 100).format("0.0%");
}

export function formatRetentionRate(value: number): string {
  return numeral(value).format("0.0%");
}

export function formatScore(value: number): string {
  return numeral(value).format("0.0");
}

export function formatDelta(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${formatMRR(value)}`;
}

export function formatMonth(dateStr: string): string {
  const date = new Date(dateStr + "-01");
  return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

export function formatCohortPeriod(months: number): string {
  if (months === 0) return "M0";
  return `M${months}`;
}

export function getRetentionColor(value: number): string {
  if (value >= 0.9) return "#10b981";
  if (value >= 0.75) return "#f59e0b";
  if (value >= 0.5) return "#f97316";
  return "#ef4444";
}

export function getNRRColor(value: number): string {
  if (value >= 1.1) return "#10b981";
  if (value >= 1.0) return "#3b82f6";
  if (value >= 0.9) return "#f59e0b";
  return "#ef4444";
}

export const CHART_PALETTE = [
  "#6366f1", "#8b5cf6", "#ec4899", "#f43f5e",
  "#f97316", "#eab308", "#22c55e", "#14b8a6",
  "#06b6d4", "#3b82f6",
];

export const MOVEMENT_COLORS: Record<string, string> = {
  new: "#22c55e",
  expansion: "#3b82f6",
  contraction: "#f97316",
  churn: "#ef4444",
  reactivation: "#8b5cf6",
  retained: "#6b7280",
  existing: "#64748b",
};

export const PLAN_COLORS: Record<string, string> = {
  starter: "#6366f1",
  growth: "#8b5cf6",
  business: "#ec4899",
  enterprise: "#f43f5e",
};

export const RISK_COLORS: Record<string, string> = {
  healthy: "#22c55e",
  at_risk: "#f59e0b",
  critical: "#ef4444",
};
