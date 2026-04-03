// =============================================================================
// FlowSync Revenue Intelligence — TypeScript Types
// =============================================================================

// ---------------------------------------------------------------------------
// Executive / KPI
// ---------------------------------------------------------------------------
export interface ExecutiveSummary {
  month: string;
  total_mrr: number;
  arr: number;
  new_mrr: number;
  expansion_mrr: number;
  contraction_mrr: number;
  churned_mrr: number;
  reactivation_mrr: number;
  net_new_mrr: number;
  active_accounts: number;
  new_accounts: number;
  churned_accounts: number;
  mrr_growth_pct: number;
  arpa: number;
  logo_churn_rate: number;
  revenue_churn_rate: number;
  nrr: number;
  grr: number;
  prev_mrr: number;
  prev_active_accounts: number;
}

export interface MRRTrendPoint {
  month: string;
  total_mrr: number;
  arr: number;
  net_new_mrr: number;
  new_mrr: number;
  expansion_mrr: number;
  contraction_mrr: number;
  churned_mrr: number;
  reactivation_mrr: number;
  active_accounts: number;
  mrr_growth_pct: number;
  nrr: number;
  arpa: number;
}

export interface WaterfallItem {
  label: string;
  value: number;
  type: "start" | "positive" | "negative" | "end";
}

export interface WaterfallData {
  month: string;
  waterfall: WaterfallItem[];
  net_new_mrr: number;
}

export interface RevenueByPlan {
  plan_name: string;
  total_mrr: number;
  account_count: number;
  avg_mrr_per_account: number;
  expansion_mrr: number;
  churned_mrr: number;
}

export interface RevenueByRegion {
  region: string;
  total_mrr: number;
  account_count: number;
  avg_mrr: number;
  new_mrr: number;
  churned_mrr: number;
}

export interface TopAccount {
  account_id: string;
  company_name: string;
  plan_name: string;
  region: string;
  company_size: string;
  current_mrr: number;
  previous_mrr?: number;
  expansion_mrr?: number;
  mrr_growth_pct?: number;
  health_score?: number;
  risk_level?: RiskLevel;
  risk_flag_count?: number;
  flag_usage_drop?: boolean;
  flag_no_login?: boolean;
  flag_open_tickets?: boolean;
  flag_payment_failure?: boolean;
  flag_low_csat?: boolean;
  flag_low_seat_util?: boolean;
}

// ---------------------------------------------------------------------------
// Revenue Movements
// ---------------------------------------------------------------------------
export interface MRRBridgePoint {
  month: string;
  new_mrr: number;
  expansion_mrr: number;
  reactivation_mrr: number;
  contraction_mrr: number;
  churned_mrr: number;
  net_new_mrr: number;
  total_mrr: number;
}

export interface AccountMovement {
  account_id: string;
  company_name: string;
  plan_name: string;
  region: string;
  company_size: string;
  acquisition_channel: string;
  month: string;
  movement_type: MovementType;
  current_mrr: number;
  previous_mrr: number;
  mrr_delta: number;
  mrr_growth_pct: number;
  new_mrr: number;
  expansion_mrr: number;
  contraction_mrr: number;
  churned_mrr: number;
  reactivation_mrr: number;
}

export interface AccountMovementsResponse {
  total: number;
  data: AccountMovement[];
}

export interface NewMRRByChannel {
  month: string;
  acquisition_channel: string;
  new_mrr: number;
  new_accounts: number;
}

export interface PaymentTrend {
  month: string;
  total_invoices: number;
  paid_invoices: number;
  failed_invoices: number;
  pending_invoices: number;
  paid_amount: number;
  failed_amount: number;
  failure_rate_pct: number;
}

// ---------------------------------------------------------------------------
// Cohort Retention
// ---------------------------------------------------------------------------
export interface CohortRetentionRow {
  cohort_month: string;
  period_number: number;
  cohort_size: number;
  active_customers: number;
  customer_retention_rate: number;
  logo_churn_rate: number;
}

export interface CohortRevenueRow {
  cohort_month: string;
  period_number: number;
  cohort_size: number;
  cohort_starting_mrr: number;
  active_mrr: number;
  revenue_retention_rate: number;
  nrr: number;
}

export interface LogoChurnTrend {
  month: string;
  logo_churn_rate: number;
  revenue_churn_rate: number;
  churned_accounts: number;
  active_accounts: number;
}

export interface RetentionBySegment {
  plan_name?: string;
  company_size?: string;
  acquisition_channel?: string;
  avg_customer_retention: number;
  avg_revenue_retention: number;
  avg_nrr: number;
  cohort_accounts: number;
}

// ---------------------------------------------------------------------------
// Customer Health
// ---------------------------------------------------------------------------
export type RiskLevel = "healthy" | "at_risk" | "critical";

export interface HealthScoreBucket {
  score_bucket: string;
  account_count: number;
  total_mrr: number;
  avg_score: number;
}

export interface RiskQuadrantAccount {
  account_id: string;
  company_name: string;
  plan_name: string;
  company_size: string;
  region: string;
  current_mrr: number;
  health_score: number;
  risk_level: RiskLevel;
  usage_score: number;
  seat_utilization_score: number;
  flag_usage_drop: boolean;
  flag_no_login: boolean;
  flag_open_tickets: boolean;
  flag_payment_failure: boolean;
  flag_low_csat: boolean;
  flag_low_seat_util: boolean;
  risk_flag_count: number;
}

export interface SupportBurden {
  account_id: string;
  company_name: string;
  plan_name: string;
  total_tickets: number;
  high_priority_tickets: number;
  open_tickets: number;
  avg_csat: number;
  avg_resolution_hours: number;
  last_ticket_date: string;
}

export interface RiskyAccountsResponse {
  total: number;
  data: RiskQuadrantAccount[];
}

export interface HealthSummaryStats {
  total_accounts: number;
  healthy_count: number;
  at_risk_count: number;
  critical_count: number;
  avg_health_score: number;
  at_risk_mrr: number;
  total_mrr: number;
}

// ---------------------------------------------------------------------------
// Funnel & Growth
// ---------------------------------------------------------------------------
export interface FunnelConversion {
  total_leads: number;
  trial_starts: number;
  paid_conversions: number;
  lead_to_trial_rate: number;
  trial_to_paid_rate: number;
  overall_conversion_rate: number;
  avg_days_to_convert: number;
  avg_trial_engagement: number;
}

export interface ConversionByChannel {
  channel: string;
  total_leads: number;
  trial_starts: number;
  paid_conversions: number;
  trial_to_paid_rate: number;
  avg_days_to_convert: number;
  avg_first_month_mrr: number;
}

export interface SalesCycle {
  channel: string;
  plan_name: string;
  avg_days: number;
  median_days: number;
  min_days: number;
  max_days: number;
  conversions: number;
}

export interface TrialUsagePoint {
  lead_id: string;
  channel: string;
  plan_name: string;
  trial_engagement_score: number;
  trial_converted: boolean;
  days_to_convert: number | null;
  first_month_mrr: number | null;
  trial_duration_days: number;
}

export interface ExpansionBySegment {
  company_size: string;
  acquisition_channel: string;
  plan_name: string;
  total_expansion_mrr: number;
  expanding_accounts: number;
  avg_expansion_per_account: number;
}

// ---------------------------------------------------------------------------
// Shared / UI
// ---------------------------------------------------------------------------
export type MovementType = "new" | "expansion" | "contraction" | "churn" | "reactivation" | "existing";

export interface KPICardData {
  title: string;
  value: string | number;
  formatted: string;
  delta?: number;
  deltaLabel?: string;
  trend?: "up" | "down" | "neutral";
  icon?: string;
  color?: "blue" | "green" | "red" | "amber" | "purple";
  subtitle?: string;
}

export interface ChartColor {
  new: string;
  expansion: string;
  reactivation: string;
  contraction: string;
  churn: string;
  existing: string;
}

export interface DateRange {
  from: Date;
  to: Date;
}

export interface PaginationParams {
  limit: number;
  offset: number;
}

export interface ApiResponse<T> {
  data: T;
  error?: string;
  loading: boolean;
}
