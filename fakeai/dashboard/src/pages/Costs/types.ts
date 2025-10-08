/**
 * TypeScript type definitions for Cost Tracking Dashboard
 */

export interface CostData {
  total_cost: number;
  start_time: number;
  end_time: number;
  costs_by_service: ServiceCost[];
  costs_by_model: ModelCost[];
  daily_costs: DailyCost[];
  cost_trend: CostTrend;
}

export interface ServiceCost {
  service: string;
  total_cost: number;
  request_count: number;
  percentage: number;
  cost_breakdown: {
    input_cost: number;
    output_cost: number;
    cached_cost?: number;
    other_cost?: number;
  };
}

export interface ModelCost {
  model: string;
  service: string;
  total_cost: number;
  request_count: number;
  input_tokens: number;
  output_tokens: number;
  cached_tokens?: number;
  avg_cost_per_request: number;
  cost_per_1k_tokens: number;
  percentage: number;
}

export interface DailyCost {
  date: string;
  timestamp: number;
  total_cost: number;
  costs_by_service: {
    [service: string]: number;
  };
  request_count: number;
}

export interface CostTrend {
  current_period_cost: number;
  previous_period_cost: number;
  change_percentage: number;
  trend: 'up' | 'down' | 'stable';
}

export interface BudgetAlert {
  id: string;
  type: 'warning' | 'critical' | 'info';
  title: string;
  message: string;
  threshold: number;
  current_value: number;
  percentage_used: number;
  created_at: number;
}

export interface CostProjection {
  period: 'daily' | 'weekly' | 'monthly' | 'annual';
  projected_cost: number;
  confidence_level: number;
  based_on_days: number;
  upper_bound: number;
  lower_bound: number;
}

export interface CostFilters {
  dateRange: {
    start: Date | null;
    end: Date | null;
    preset?: 'today' | 'yesterday' | 'last7days' | 'last30days' | 'thisMonth' | 'lastMonth' | 'custom';
  };
  service: string | null;
  model: string | null;
  groupBy: 'day' | 'week' | 'month';
}

export interface EfficiencyMetric {
  metric_name: string;
  value: number;
  formatted_value: string;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  change_percentage: number;
  benchmark?: number;
}

export interface CostExportData {
  format: 'csv' | 'json' | 'pdf';
  date_range: {
    start: string;
    end: string;
  };
  total_cost: number;
  breakdown: any[];
  generated_at: string;
}

export interface OrganizationCostsResponse {
  object: 'page';
  data: CostBucket[];
  has_more: boolean;
  next_page: string | null;
}

export interface CostBucket {
  object: 'bucket';
  start_time: number;
  end_time: number;
  results: CostResult[];
}

export interface CostResult {
  object: 'organization.costs.result';
  amount: {
    value: number;
    currency: string;
  };
  line_item: string;
  project_id?: string;
}

export interface MetricsCostsResponse {
  total_cost: number;
  cost_by_service: {
    [service: string]: number;
  };
  cost_by_model: {
    [model: string]: number;
  };
  time_period: {
    start: number;
    end: number;
  };
}

export interface TopCostContributor {
  rank: number;
  name: string;
  type: 'model' | 'service';
  cost: number;
  percentage: number;
  request_count: number;
  efficiency_score: number;
}

export interface CostAlertSettings {
  daily_budget: number;
  weekly_budget: number;
  monthly_budget: number;
  alert_thresholds: {
    warning: number; // percentage
    critical: number; // percentage
  };
  email_notifications: boolean;
  webhook_url?: string;
}

export interface HourlyCost {
  hour: string;
  timestamp: number;
  cost: number;
  requests: number;
}

export interface WeeklyCost {
  week: string;
  week_number: number;
  year: number;
  start_date: string;
  end_date: string;
  total_cost: number;
  daily_breakdown: DailyCost[];
}

export interface MonthlyCost {
  month: string;
  month_number: number;
  year: number;
  total_cost: number;
  daily_breakdown: DailyCost[];
  weekly_breakdown: WeeklyCost[];
}
