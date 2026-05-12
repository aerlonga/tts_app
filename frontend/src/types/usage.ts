export interface UsageSummaryResponse {
  start_date: string | null;
  end_date: string | null;
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_estimated_cost_usd: number;
  projected_monthly_cost_usd: number;
  active_days: number;
}

export interface UsageByFeatureItem {
  feature: string;
  provider: string;
  start_date: string | null;
  end_date: string | null;
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_estimated_cost_usd: number;
  projected_monthly_cost_usd: number;
  active_days: number;
}
