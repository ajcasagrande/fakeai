/**
 * Tests for MetricsOverview component
 */

import { describe, it, expect } from 'vitest';
import { renderWithProviders, screen } from '@test/utils';
import { MetricsOverview } from './MetricsOverview';
import { MetricsOverview as MetricsOverviewType } from '../types';

describe('MetricsOverview', () => {
  const mockMetrics: MetricsOverviewType = {
    total_requests: 6982,
    total_tokens: 1426788,
    total_cost: 92.57,
    avg_latency_ms: 872,
    error_rate: 0.573,
    streaming_percentage: 56.2,
    requests_per_second: 1.94,
  };

  it('renders all metrics correctly', () => {
    renderWithProviders(<MetricsOverview metrics={mockMetrics} loading={false} />);

    expect(screen.getByText('6,982')).toBeInTheDocument();
    expect(screen.getByText('1,426,788')).toBeInTheDocument();
    expect(screen.getByText('$92.57')).toBeInTheDocument();
    expect(screen.getByText('872ms')).toBeInTheDocument();
    expect(screen.getByText('0.57%')).toBeInTheDocument();
    expect(screen.getByText('56.2%')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    renderWithProviders(<MetricsOverview metrics={mockMetrics} loading={true} />);

    expect(screen.getByTestId('metrics-loading')).toBeInTheDocument();
  });

  it('formats large numbers with commas', () => {
    const largeMetrics: MetricsOverviewType = {
      ...mockMetrics,
      total_requests: 1234567,
      total_tokens: 9876543210,
    };

    renderWithProviders(<MetricsOverview metrics={largeMetrics} loading={false} />);

    expect(screen.getByText('1,234,567')).toBeInTheDocument();
    expect(screen.getByText('9,876,543,210')).toBeInTheDocument();
  });

  it('handles zero values gracefully', () => {
    const zeroMetrics: MetricsOverviewType = {
      total_requests: 0,
      total_tokens: 0,
      total_cost: 0,
      avg_latency_ms: 0,
      error_rate: 0,
      streaming_percentage: 0,
      requests_per_second: 0,
    };

    renderWithProviders(<MetricsOverview metrics={zeroMetrics} loading={false} />);

    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('$0.00')).toBeInTheDocument();
    expect(screen.getByText('0ms')).toBeInTheDocument();
    expect(screen.getByText('0.00%')).toBeInTheDocument();
  });

  it('applies correct CSS classes for error rate warnings', () => {
    const highErrorMetrics: MetricsOverviewType = {
      ...mockMetrics,
      error_rate: 5.5,
    };

    const { container } = renderWithProviders(
      <MetricsOverview metrics={highErrorMetrics} loading={false} />
    );

    const errorRateElement = screen.getByText('5.50%');
    expect(errorRateElement).toHaveClass('metric-warning');
  });

  it('renders metric labels', () => {
    renderWithProviders(<MetricsOverview metrics={mockMetrics} loading={false} />);

    expect(screen.getByText('Total Requests')).toBeInTheDocument();
    expect(screen.getByText('Total Tokens')).toBeInTheDocument();
    expect(screen.getByText('Total Cost')).toBeInTheDocument();
    expect(screen.getByText('Avg Latency')).toBeInTheDocument();
    expect(screen.getByText('Error Rate')).toBeInTheDocument();
    expect(screen.getByText('Streaming %')).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    renderWithProviders(<MetricsOverview metrics={mockMetrics} loading={false} />);

    const metricsGrid = screen.getByRole('region', { name: /metrics overview/i });
    expect(metricsGrid).toBeInTheDocument();
  });
});
