import { useQuery } from '@tanstack/react-query';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TokenTiming {
  token_index: number;
  timestamp_ms: number;
  latency_ms: number | null;
}

interface RequestTiming {
  request_id: string;
  endpoint: string;
  model: string;
  start_time: number;
  end_time: number | null;
  duration_ms: number;
  ttft_ms: number | null;
  is_streaming: boolean;
  input_tokens: number;
  output_tokens: number;
  tokens: TokenTiming[];
  is_complete: boolean;
}

interface WaterfallData {
  requests: RequestTiming[];
  stats: {
    total_completed: number;
    active_requests: number;
    max_capacity: number;
    utilization_percent: number;
  };
  active_requests: number;
}

export const useWaterfall = (limit: number = 100, enabled: boolean = true) => {
  return useQuery<WaterfallData>({
    queryKey: ['waterfall', limit],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/waterfall/data?limit=${limit}`);
      if (!response.ok) {
        throw new Error('Failed to fetch waterfall data');
      }
      return response.json();
    },
    enabled,
    refetchInterval: 2000, // Auto-refresh every 2 seconds
  });
};
