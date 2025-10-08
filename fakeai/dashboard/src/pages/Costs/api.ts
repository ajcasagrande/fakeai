/**
 * API client functions for Cost Tracking Dashboard
 */

import {
  OrganizationCostsResponse,
  MetricsCostsResponse,
  CostData,
  ServiceCost,
  ModelCost,
  DailyCost,
  CostTrend,
} from './types';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Fetch costs from /v1/organization/costs endpoint
 */
export async function fetchOrganizationCosts(
  startTime: number,
  endTime: number,
  bucketWidth: string = '1d',
  projectId?: string,
  groupBy?: string[]
): Promise<OrganizationCostsResponse> {
  const params = new URLSearchParams({
    start_time: startTime.toString(),
    end_time: endTime.toString(),
    bucket_width: bucketWidth,
  });

  if (projectId) {
    params.append('project_id', projectId);
  }

  if (groupBy && groupBy.length > 0) {
    groupBy.forEach(group => params.append('group_by', group));
  }

  const response = await fetch(
    `${BASE_URL}/v1/organization/costs?${params.toString()}`,
    {
      headers: {
        'Authorization': `Bearer ${getApiKey()}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch organization costs: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch costs from /metrics/costs endpoint
 */
export async function fetchMetricsCosts(
  startTime?: number,
  endTime?: number
): Promise<MetricsCostsResponse> {
  const params = new URLSearchParams();

  if (startTime) {
    params.append('start_time', startTime.toString());
  }

  if (endTime) {
    params.append('end_time', endTime.toString());
  }

  const url = params.toString()
    ? `${BASE_URL}/metrics/costs?${params.toString()}`
    : `${BASE_URL}/metrics/costs`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch metrics costs: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch comprehensive cost data by combining multiple endpoints
 */
export async function fetchComprehensiveCostData(
  startTime: number,
  endTime: number,
  bucketWidth: string = '1d'
): Promise<CostData> {
  try {
    // Fetch from both endpoints in parallel
    const [orgCosts, metricsCosts] = await Promise.all([
      fetchOrganizationCosts(startTime, endTime, bucketWidth),
      fetchMetricsCosts(startTime, endTime),
    ]);

    // Process organization costs
    const dailyCosts: DailyCost[] = [];
    let totalCost = 0;
    const serviceMap = new Map<string, number>();
    const modelMap = new Map<string, { cost: number; requests: number; inputTokens: number; outputTokens: number }>();

    orgCosts.data.forEach(bucket => {
      const dailyCost: DailyCost = {
        date: new Date(bucket.start_time * 1000).toISOString().split('T')[0],
        timestamp: bucket.start_time,
        total_cost: 0,
        costs_by_service: {},
        request_count: 0,
      };

      bucket.results.forEach(result => {
        const cost = result.amount.value;
        totalCost += cost;
        dailyCost.total_cost += cost;

        // Extract service from line_item
        const service = extractServiceFromLineItem(result.line_item);
        dailyCost.costs_by_service[service] = (dailyCost.costs_by_service[service] || 0) + cost;
        serviceMap.set(service, (serviceMap.get(service) || 0) + cost);
      });

      dailyCosts.push(dailyCost);
    });

    // Process metrics costs
    Object.entries(metricsCosts.cost_by_model || {}).forEach(([model, cost]) => {
      const existing = modelMap.get(model) || { cost: 0, requests: 0, inputTokens: 0, outputTokens: 0 };
      existing.cost += cost;
      modelMap.set(model, existing);
    });

    // Build service costs
    const costs_by_service: ServiceCost[] = Array.from(serviceMap.entries()).map(([service, cost]) => ({
      service,
      total_cost: cost,
      request_count: 0, // Will be populated if we have request data
      percentage: (cost / totalCost) * 100,
      cost_breakdown: {
        input_cost: cost * 0.6, // Estimated breakdown
        output_cost: cost * 0.4,
      },
    }));

    // Build model costs
    const costs_by_model: ModelCost[] = Array.from(modelMap.entries()).map(([model, data]) => {
      const service = extractServiceFromModel(model);
      return {
        model,
        service,
        total_cost: data.cost,
        request_count: data.requests,
        input_tokens: data.inputTokens,
        output_tokens: data.outputTokens,
        avg_cost_per_request: data.requests > 0 ? data.cost / data.requests : 0,
        cost_per_1k_tokens: (data.inputTokens + data.outputTokens) > 0
          ? (data.cost / ((data.inputTokens + data.outputTokens) / 1000))
          : 0,
        percentage: (data.cost / totalCost) * 100,
      };
    });

    // Calculate cost trend
    const midpoint = Math.floor(dailyCosts.length / 2);
    const firstHalf = dailyCosts.slice(0, midpoint);
    const secondHalf = dailyCosts.slice(midpoint);

    const firstHalfCost = firstHalf.reduce((sum, d) => sum + d.total_cost, 0);
    const secondHalfCost = secondHalf.reduce((sum, d) => sum + d.total_cost, 0);
    const changePercentage = firstHalfCost > 0
      ? ((secondHalfCost - firstHalfCost) / firstHalfCost) * 100
      : 0;

    const cost_trend: CostTrend = {
      current_period_cost: secondHalfCost,
      previous_period_cost: firstHalfCost,
      change_percentage: changePercentage,
      trend: Math.abs(changePercentage) < 5 ? 'stable' : changePercentage > 0 ? 'up' : 'down',
    };

    return {
      total_cost: totalCost,
      start_time: startTime,
      end_time: endTime,
      costs_by_service: costs_by_service.sort((a, b) => b.total_cost - a.total_cost),
      costs_by_model: costs_by_model.sort((a, b) => b.total_cost - a.total_cost),
      daily_costs: dailyCosts.sort((a, b) => a.timestamp - b.timestamp),
      cost_trend,
    };
  } catch (error) {
    console.error('Error fetching comprehensive cost data:', error);
    throw error;
  }
}

/**
 * Export cost data in various formats
 */
export async function exportCostData(
  format: 'csv' | 'json' | 'pdf',
  startTime: number,
  endTime: number
): Promise<Blob> {
  const costData = await fetchComprehensiveCostData(startTime, endTime);

  if (format === 'csv') {
    return generateCSV(costData);
  } else if (format === 'json') {
    return generateJSON(costData);
  } else {
    return generatePDF(costData);
  }
}

/**
 * Generate CSV export
 */
function generateCSV(data: CostData): Blob {
  const lines: string[] = [];

  // Header
  lines.push('Cost Report');
  lines.push(`Period: ${new Date(data.start_time * 1000).toLocaleDateString()} - ${new Date(data.end_time * 1000).toLocaleDateString()}`);
  lines.push(`Total Cost: $${data.total_cost.toFixed(2)}`);
  lines.push('');

  // Daily costs
  lines.push('Date,Total Cost,Request Count');
  data.daily_costs.forEach(day => {
    lines.push(`${day.date},${day.total_cost.toFixed(6)},${day.request_count}`);
  });
  lines.push('');

  // Service breakdown
  lines.push('Service,Total Cost,Percentage');
  data.costs_by_service.forEach(service => {
    lines.push(`${service.service},${service.total_cost.toFixed(6)},${service.percentage.toFixed(2)}%`);
  });
  lines.push('');

  // Model breakdown
  lines.push('Model,Service,Total Cost,Avg Cost/Request,Cost per 1K Tokens');
  data.costs_by_model.forEach(model => {
    lines.push(`${model.model},${model.service},${model.total_cost.toFixed(6)},${model.avg_cost_per_request.toFixed(6)},${model.cost_per_1k_tokens.toFixed(6)}`);
  });

  return new Blob([lines.join('\n')], { type: 'text/csv' });
}

/**
 * Generate JSON export
 */
function generateJSON(data: CostData): Blob {
  const exportData = {
    export_date: new Date().toISOString(),
    period: {
      start: new Date(data.start_time * 1000).toISOString(),
      end: new Date(data.end_time * 1000).toISOString(),
    },
    summary: {
      total_cost: data.total_cost,
      trend: data.cost_trend,
    },
    daily_costs: data.daily_costs,
    costs_by_service: data.costs_by_service,
    costs_by_model: data.costs_by_model,
  };

  return new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
}

/**
 * Generate PDF export (simplified - would need proper PDF library in production)
 */
function generatePDF(data: CostData): Blob {
  // In production, use a library like jsPDF or pdfmake
  // For now, return HTML content that can be printed to PDF
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Cost Report</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: #76B900; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #76B900; color: white; }
      </style>
    </head>
    <body>
      <h1>Cost Report</h1>
      <p>Period: ${new Date(data.start_time * 1000).toLocaleDateString()} - ${new Date(data.end_time * 1000).toLocaleDateString()}</p>
      <p>Total Cost: $${data.total_cost.toFixed(2)}</p>

      <h2>Costs by Service</h2>
      <table>
        <tr><th>Service</th><th>Cost</th><th>Percentage</th></tr>
        ${data.costs_by_service.map(s => `
          <tr>
            <td>${s.service}</td>
            <td>$${s.total_cost.toFixed(6)}</td>
            <td>${s.percentage.toFixed(2)}%</td>
          </tr>
        `).join('')}
      </table>

      <h2>Costs by Model</h2>
      <table>
        <tr><th>Model</th><th>Service</th><th>Total Cost</th><th>Avg/Request</th></tr>
        ${data.costs_by_model.map(m => `
          <tr>
            <td>${m.model}</td>
            <td>${m.service}</td>
            <td>$${m.total_cost.toFixed(6)}</td>
            <td>$${m.avg_cost_per_request.toFixed(6)}</td>
          </tr>
        `).join('')}
      </table>
    </body>
    </html>
  `;

  return new Blob([html], { type: 'text/html' });
}

/**
 * Extract service name from line item
 */
function extractServiceFromLineItem(lineItem: string): string {
  const lower = lineItem.toLowerCase();
  if (lower.includes('chat') || lower.includes('completion')) return 'chat';
  if (lower.includes('embedding')) return 'embeddings';
  if (lower.includes('image')) return 'images';
  if (lower.includes('audio') || lower.includes('speech') || lower.includes('tts')) return 'audio';
  if (lower.includes('fine-tun')) return 'fine-tuning';
  if (lower.includes('assistant')) return 'assistants';
  if (lower.includes('batch')) return 'batch';
  return 'other';
}

/**
 * Extract service name from model name
 */
function extractServiceFromModel(model: string): string {
  const lower = model.toLowerCase();
  if (lower.includes('gpt') || lower.includes('chat') || lower.includes('claude')) return 'chat';
  if (lower.includes('embedding') || lower.includes('ada')) return 'embeddings';
  if (lower.includes('dall-e') || lower.includes('image')) return 'images';
  if (lower.includes('whisper') || lower.includes('tts')) return 'audio';
  return 'chat'; // default
}

/**
 * Get API key from localStorage or environment
 */
function getApiKey(): string {
  return localStorage.getItem('apiKey') || process.env.REACT_APP_API_KEY || 'fake-api-key';
}

/**
 * Download blob as file
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
