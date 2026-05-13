// Mock data for development and demo mode fallback
// Used when API is unavailable or NEXT_PUBLIC_USE_MOCK_DATA=true

export const MOCK_EXECUTIVE_SUMMARY = {
  total_mrr: 287450,
  total_arr: 3449400,
  active_accounts: 247,
  nrr: 1.12,
  grr: 0.91,
  logo_churn_rate: 0.032,
  revenue_churn_rate: 0.028,
  arpa: 1164,
  net_new_mrr: 12350,
  new_mrr: 8900,
  expansion_mrr: 6200,
  contraction_mrr: 1450,
  churned_mrr: 1300,
  month_key: "2024-12",
};

export const MOCK_MRR_TREND = Array.from({ length: 24 }, (_, i) => ({
  month: `2023-${String((i % 12) + 1).padStart(2, "0")}`,
  total_mrr: 180000 + i * 5000 + Math.random() * 3000,
  new_mrr: 4000 + Math.random() * 2000,
  expansion_mrr: 3000 + Math.random() * 1500,
  contraction_mrr: -(1000 + Math.random() * 800),
  churned_mrr: -(800 + Math.random() * 600),
}));

export const MOCK_WATERFALL = {
  month_key: "2024-12",
  starting_mrr: 275100,
  new_mrr: 8900,
  expansion_mrr: 6200,
  contraction_mrr: -1450,
  churned_mrr: -1300,
  reactivation_mrr: 0,
  ending_mrr: 287450,
};

export const MOCK_REVENUE_BY_PLAN = [
  { plan_name: "Starter", mrr: 29700, accounts: 100 },
  { plan_name: "Growth", mrr: 89700, accounts: 85 },
  { plan_name: "Business", mrr: 111650, accounts: 45 },
  { plan_name: "Enterprise", mrr: 56400, accounts: 17 },
];

export const MOCK_REVENUE_BY_REGION = [
  { region: "North America", mrr: 143725, accounts: 120 },
  { region: "Europe", mrr: 86235, accounts: 72 },
  { region: "Asia Pacific", mrr: 34494, accounts: 33 },
  { region: "Latin America", mrr: 22996, accounts: 22 },
];

export const MOCK_TOP_EXPANDING = Array.from({ length: 10 }, (_, i) => ({
  account_id: `acc-${i}`,
  company_name: `Company ${String.fromCharCode(65 + i)}`,
  plan_name: ["Growth", "Business", "Enterprise"][i % 3],
  expansion_mrr: 2500 - i * 200,
  current_mrr: 5000 + i * 500,
}));

export const MOCK_TOP_CHURN_RISK = Array.from({ length: 10 }, (_, i) => ({
  account_id: `risk-${i}`,
  company_name: `RiskCo ${String.fromCharCode(65 + i)}`,
  plan_name: ["Starter", "Growth"][i % 2],
  health_score: 25 + i * 3,
  mrr: 1500 + i * 200,
  risk_flags: ["usage_drop", "no_login", "payment_failure"].slice(0, (i % 3) + 1),
}));

export const MOCK_MRR_BRIDGE = Array.from({ length: 12 }, (_, i) => ({
  month: `2024-${String(i + 1).padStart(2, "0")}`,
  new_mrr: 5000 + Math.random() * 4000,
  expansion_mrr: 3000 + Math.random() * 3000,
  contraction_mrr: -(1000 + Math.random() * 1000),
  churned_mrr: -(800 + Math.random() * 800),
  net_new_mrr: 4000 + Math.random() * 3000,
}));

export const MOCK_ACCOUNT_MOVEMENTS = {
  movements: Array.from({ length: 20 }, (_, i) => ({
    account_id: `mov-${i}`,
    company_name: `MovCo ${i}`,
    movement_type: ["new", "expansion", "contraction", "churn"][i % 4],
    mrr_delta: (i % 2 === 0 ? 1 : -1) * (500 + i * 100),
    current_mrr: 2000 + i * 300,
  })),
  total: 50,
  page: 1,
  page_size: 20,
};

export const MOCK_NEW_MRR_BY_CHANNEL = [
  { channel: "Organic", mrr: 3200 },
  { channel: "Paid", mrr: 2800 },
  { channel: "Referral", mrr: 1900 },
  { channel: "Direct", mrr: 1000 },
];

export const MOCK_PAYMENT_TRENDS = Array.from({ length: 12 }, (_, i) => ({
  month: `2024-${String(i + 1).padStart(2, "0")}`,
  successful: 200 + Math.floor(Math.random() * 30),
  failed: 5 + Math.floor(Math.random() * 8),
  total_paid: 250000 + i * 5000,
}));

export const MOCK_COHORT_RETENTION = {
  cohorts: Array.from({ length: 12 }, (_, cohortIdx) => ({
    cohort_month: `2024-${String(cohortIdx + 1).padStart(2, "0")}`,
    periods: Array.from({ length: 12 - cohortIdx }, (__, periodIdx) => ({
      period: periodIdx,
      retention_rate: Math.max(0.5, 1 - periodIdx * 0.04 - Math.random() * 0.02),
      accounts: 20 + Math.floor(Math.random() * 10),
    })),
  })),
};

export const MOCK_COHORT_REVENUE = {
  cohorts: Array.from({ length: 12 }, (_, cohortIdx) => ({
    cohort_month: `2024-${String(cohortIdx + 1).padStart(2, "0")}`,
    periods: Array.from({ length: 12 - cohortIdx }, (__, periodIdx) => ({
      period: periodIdx,
      nrr: 1.0 + (Math.random() * 0.2 - 0.05),
      mrr: 50000 * Math.max(0.7, 1 - periodIdx * 0.02),
    })),
  })),
};

export const MOCK_LOGO_CHURN_TREND = Array.from({ length: 24 }, (_, i) => ({
  month: `2023-${String((i % 12) + 1).padStart(2, "0")}`,
  churn_rate: 0.02 + Math.random() * 0.02,
  churned_accounts: 3 + Math.floor(Math.random() * 5),
}));

export const MOCK_RETENTION_BY_PLAN = [
  { segment: "Starter", retention_12m: 0.72 },
  { segment: "Growth", retention_12m: 0.85 },
  { segment: "Business", retention_12m: 0.92 },
  { segment: "Enterprise", retention_12m: 0.97 },
];

export const MOCK_RETENTION_BY_SIZE = [
  { segment: "1-10", retention_12m: 0.68 },
  { segment: "11-50", retention_12m: 0.78 },
  { segment: "51-200", retention_12m: 0.88 },
  { segment: "201-1000", retention_12m: 0.93 },
  { segment: "1000+", retention_12m: 0.96 },
];

export const MOCK_HEALTH_DISTRIBUTION = [
  { health_label: "healthy", count: 165, avg_mrr: 1350 },
  { health_label: "at_risk", count: 55, avg_mrr: 980 },
  { health_label: "critical", count: 27, avg_mrr: 750 },
];

export const MOCK_RISK_QUADRANT = Array.from({ length: 50 }, (_, i) => ({
  account_id: `q-${i}`,
  company_name: `QuadCo ${i}`,
  health_score: 20 + Math.random() * 80,
  mrr: 500 + Math.random() * 5000,
  risk_level: ["healthy", "at_risk", "critical"][i % 3],
}));

export const MOCK_SUPPORT_BURDEN = Array.from({ length: 15 }, (_, i) => ({
  account_id: `sup-${i}`,
  company_name: `SupportCo ${i}`,
  open_tickets: 5 - Math.floor(i * 0.3),
  high_priority: Math.max(0, 3 - i),
  avg_csat: 2.5 + Math.random() * 2,
  mrr: 2000 + i * 300,
}));

export const MOCK_HEALTH_STATS = {
  avg_health_score: 68.5,
  at_risk_count: 55,
  critical_count: 27,
  at_risk_mrr: 53900,
  critical_mrr: 20250,
};

export const MOCK_FUNNEL = {
  leads: 450,
  trials: 180,
  paid: 85,
  lead_to_trial_rate: 0.4,
  trial_to_paid_rate: 0.47,
  lead_to_paid_rate: 0.19,
  avg_days_lead_to_trial: 12,
  avg_days_trial_to_paid: 18,
};

export const MOCK_CONVERSION_BY_CHANNEL = [
  { channel: "Organic", leads: 150, trials: 72, paid: 38, conversion_rate: 0.253 },
  { channel: "Paid", leads: 120, trials: 48, paid: 22, conversion_rate: 0.183 },
  { channel: "Referral", leads: 80, trials: 40, paid: 18, conversion_rate: 0.225 },
  { channel: "Direct", leads: 60, trials: 12, paid: 5, conversion_rate: 0.083 },
  { channel: "Partner", leads: 40, trials: 8, paid: 2, conversion_rate: 0.05 },
];

export const MOCK_SALES_CYCLE = [
  { bucket: "0-7 days", count: 15 },
  { bucket: "8-14 days", count: 28 },
  { bucket: "15-30 days", count: 25 },
  { bucket: "31-60 days", count: 12 },
  { bucket: "60+ days", count: 5 },
];

export const MOCK_EXPANSION_BY_SEGMENT = [
  { segment: "Starter → Growth", count: 22, avg_mrr_increase: 200 },
  { segment: "Growth → Business", count: 15, avg_mrr_increase: 500 },
  { segment: "Business → Enterprise", count: 5, avg_mrr_increase: 1700 },
];
