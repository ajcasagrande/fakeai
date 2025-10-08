/**
 * TypeScript type definitions for Rate Limits Dashboard
 */

// Tier definitions
export type RateLimitTier = 'free' | 'tier1' | 'tier2' | 'tier3' | 'tier4' | 'tier5';

// Rate limit configuration
export interface RateLimitConfig {
  tier: RateLimitTier;
  rpm: number; // Requests per minute
  tpm: number; // Tokens per minute
  rpd: number; // Requests per day
}

// API key rate limit status
export interface ApiKeyRateLimit {
  api_key: string;
  api_key_name?: string;
  tier: RateLimitTier;
  limits: RateLimitConfig;
  current_usage: {
    rpm: number;
    tpm: number;
    rpd: number;
  };
  usage_percentage: {
    rpm: number;
    tpm: number;
    rpd: number;
  };
  last_request_time: number;
  total_requests: number;
  throttled_requests: number;
  status: 'healthy' | 'warning' | 'critical' | 'throttled';
}

// Rate limit breach event
export interface RateLimitBreach {
  id: string;
  api_key: string;
  api_key_name?: string;
  timestamp: number;
  breach_type: 'rpm' | 'tpm' | 'rpd';
  limit: number;
  attempted_value: number;
  duration_ms?: number;
  resolved: boolean;
}

// Throttle analytics (429 errors)
export interface ThrottleEvent {
  timestamp: number;
  api_key: string;
  api_key_name?: string;
  breach_type: 'rpm' | 'tpm' | 'rpd';
  endpoint: string;
  count: number;
}

// Time series data for throttle events
export interface ThrottleTimeSeries {
  timestamp: number;
  rpm_throttles: number;
  tpm_throttles: number;
  rpd_throttles: number;
  total_throttles: number;
}

// Abuse pattern detection
export interface AbusePattern {
  api_key: string;
  api_key_name?: string;
  pattern_type: 'burst' | 'sustained' | 'distributed' | 'suspicious';
  severity: 'low' | 'medium' | 'high' | 'critical';
  detected_at: number;
  description: string;
  metrics: {
    requests_per_second: number;
    unique_endpoints: number;
    error_rate: number;
    geographic_distribution?: string[];
  };
  recommended_action: string;
}

// Top consumer
export interface TopConsumer {
  api_key: string;
  api_key_name?: string;
  tier: RateLimitTier;
  total_requests: number;
  total_tokens: number;
  throttle_count: number;
  avg_requests_per_minute: number;
  utilization_percentage: number;
  last_active: number;
}

// Tier distribution
export interface TierDistribution {
  tier: RateLimitTier;
  count: number;
  percentage: number;
  total_requests: number;
  total_tokens: number;
}

// Tier upgrade recommendation
export interface TierUpgradeRecommendation {
  api_key: string;
  api_key_name?: string;
  current_tier: RateLimitTier;
  recommended_tier: RateLimitTier;
  reason: string;
  metrics: {
    throttle_rate: number;
    avg_utilization: number;
    peak_requests: number;
  };
  potential_savings: {
    reduced_throttles: number;
    improved_latency_ms: number;
  };
  priority: 'low' | 'medium' | 'high';
}

// Overall rate limits overview
export interface RateLimitsOverview {
  total_api_keys: number;
  total_requests: number;
  total_throttled: number;
  throttle_rate: number;
  active_breaches: number;
  detected_abuse_patterns: number;
  avg_utilization: number;
  tier_distribution: TierDistribution[];
}

// Dashboard filters
export interface RateLimitFilters {
  api_key?: string;
  tier?: RateLimitTier;
  status?: 'all' | 'healthy' | 'warning' | 'critical' | 'throttled';
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  breach_type?: 'rpm' | 'tpm' | 'rpd' | 'all';
}

// Real-time monitoring data
export interface RealTimeRateLimitData {
  timestamp: number;
  api_keys: ApiKeyRateLimit[];
  recent_throttles: ThrottleEvent[];
  active_breaches: RateLimitBreach[];
}
