const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const executiveApi = {
  getSummary: (monthKey?: string) =>
    fetchApi<any>(`/executive/summary${monthKey ? `?month_key=${monthKey}` : ""}`),
  getMRRTrend: (months = 24) =>
    fetchApi<any>(`/executive/mrr-trend?months=${months}`),
  getWaterfall: (monthKey?: string) =>
    fetchApi<any>(`/executive/waterfall${monthKey ? `?month_key=${monthKey}` : ""}`),
  getByPlan: (monthKey?: string) =>
    fetchApi<any>(`/executive/by-plan${monthKey ? `?month_key=${monthKey}` : ""}`),
  getByRegion: (monthKey?: string) =>
    fetchApi<any>(`/executive/by-region${monthKey ? `?month_key=${monthKey}` : ""}`),
  getTopExpanding: (limit = 10) =>
    fetchApi<any>(`/executive/top-expanding?limit=${limit}`),
  getTopChurnRisk: (limit = 10) =>
    fetchApi<any>(`/executive/top-churn-risk?limit=${limit}`),
};

export const revenueApi = {
  getMRRBridge: (months = 12) =>
    fetchApi<any>(`/revenue/mrr-bridge?months=${months}`),
  getAccountMovements: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return fetchApi<any>(`/revenue/account-movements${qs}`);
  },
  getNewMRRByChannel: (monthKey?: string) =>
    fetchApi<any>(`/revenue/new-mrr-by-channel${monthKey ? `?month_key=${monthKey}` : ""}`),
  getPaymentTrend: (months = 12) =>
    fetchApi<any>(`/revenue/payment-trend?months=${months}`),
};

export const cohortsApi = {
  getHeatmap: (metric = "logo_retention") =>
    fetchApi<any>(`/cohorts/heatmap?metric=${metric}`),
  getLogoChurnTrend: (months = 24) =>
    fetchApi<any>(`/cohorts/logo-churn-trend?months=${months}`),
  getNRRByCohort: (periodMonths = 12) =>
    fetchApi<any>(`/cohorts/nrr-by-cohort?period_months=${periodMonths}`),
  getRetentionBySegment: (dimension = "plan_name", periodMonths = 12) =>
    fetchApi<any>(`/cohorts/retention-by-segment?dimension=${dimension}&period_months=${periodMonths}`),
};

export const healthApi = {
  getDistribution: (monthKey?: string) =>
    fetchApi<any>(`/health/distribution${monthKey ? `?month_key=${monthKey}` : ""}`),
  getChurnRiskQuadrant: (monthKey?: string) =>
    fetchApi<any>(`/health/churn-risk-quadrant${monthKey ? `?month_key=${monthKey}` : ""}`),
  getRiskyAccounts: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return fetchApi<any>(`/health/risky-accounts${qs}`);
  },
  getSupportBurden: (monthKey?: string) =>
    fetchApi<any>(`/health/support-burden${monthKey ? `?month_key=${monthKey}` : ""}`),
};

export const funnelApi = {
  getOverview: (months = 12) =>
    fetchApi<any>(`/funnel/overview?months=${months}`),
  getConversionByChannel: (months = 12) =>
    fetchApi<any>(`/funnel/conversion-by-channel?months=${months}`),
  getSalesCycle: (months = 12) =>
    fetchApi<any>(`/funnel/sales-cycle?months=${months}`),
  getExpansionBySegment: (months = 12) =>
    fetchApi<any>(`/funnel/expansion-by-segment?months=${months}`),
};
