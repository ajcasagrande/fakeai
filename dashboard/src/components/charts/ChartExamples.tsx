'use client'

import { LineChart } from './LineChart'
import { BarChart } from './BarChart'
import { MetricCard } from './MetricCard'
import { StatsGrid } from './StatsGrid'
import { PerformanceGauge } from './PerformanceGauge'
import { Zap, Clock, Target, TrendingUp, Cpu, Activity, BarChart3, Gauge } from 'lucide-react'

/**
 * Chart Examples Component
 *
 * This file demonstrates how to use all the shared chart components.
 * Use this as a reference for implementing charts in your own pages.
 */

export function ChartExamples() {
  // Sample data for LineChart
  const timeSeriesData = [
    { time: '00:00', throughput: 100, latency: 50, tokens: 1200 },
    { time: '01:00', throughput: 150, latency: 45, tokens: 1800 },
    { time: '02:00', throughput: 180, latency: 42, tokens: 2100 },
    { time: '03:00', throughput: 200, latency: 38, tokens: 2400 },
    { time: '04:00', throughput: 190, latency: 40, tokens: 2280 },
    { time: '05:00', throughput: 220, latency: 35, tokens: 2640 },
  ]

  // Sample data for BarChart
  const benchmarkData = [
    { model: 'Llama-2-7B', throughput: 150, latency: 45 },
    { model: 'Llama-2-13B', throughput: 120, latency: 60 },
    { model: 'Llama-2-70B', throughput: 80, latency: 95 },
    { model: 'GPT-3.5', throughput: 180, latency: 40 },
  ]

  // Sample stats for StatsGrid
  const stats = [
    {
      id: 'throughput',
      icon: Zap,
      label: 'Request Throughput',
      value: 1250.5,
      unit: 'req/s',
      trend: 12.5,
      trendLabel: 'vs last hour',
      color: 'green' as const,
    },
    {
      id: 'latency',
      icon: Clock,
      label: 'Avg Latency',
      value: 45.2,
      unit: 'ms',
      trend: -5.3,
      trendLabel: 'vs last hour',
      color: 'blue' as const,
    },
    {
      id: 'tokens',
      icon: Target,
      label: 'Token Throughput',
      value: 15420,
      unit: 'tok/s',
      trend: 8.7,
      trendLabel: 'vs last hour',
      color: 'purple' as const,
    },
    {
      id: 'goodput',
      icon: TrendingUp,
      label: 'Goodput',
      value: 0.98,
      trend: 2.1,
      trendLabel: 'vs last hour',
      color: 'yellow' as const,
    },
  ]

  return (
    <div className="min-h-screen bg-black text-white p-8 space-y-12">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-nvidia-green mb-2">
            Chart Components Showcase
          </h1>
          <p className="text-gray-400">
            Beautiful, reusable chart components matching the ultimate_dashboard_v3 style
          </p>
        </div>

        {/* Stats Grid Example */}
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-nvidia-green" />
            <h2 className="text-2xl font-bold">Stats Grid</h2>
          </div>
          <StatsGrid stats={stats} columns={4} gap={6} />
        </section>

        {/* Line Chart Example */}
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-nvidia-green" />
            <h2 className="text-2xl font-bold">Line Chart</h2>
          </div>
          <LineChart
            data={timeSeriesData}
            xKey="time"
            yKeys={['throughput', 'latency']}
            colors={['#76B900', '#3b82f6']}
            xLabel="Time"
            yLabel="Value"
            height={400}
            showLegend
            smooth
          />
        </section>

        {/* Bar Chart Examples */}
        <section className="space-y-8">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-nvidia-green" />
            <h2 className="text-2xl font-bold">Bar Charts</h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Vertical Bar Chart */}
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-300">Vertical</h3>
              <BarChart
                data={benchmarkData}
                xKey="model"
                yKeys={['throughput']}
                colors={['#76B900']}
                yLabel="Throughput (req/s)"
                height={350}
                showLegend={false}
                showValues
              />
            </div>

            {/* Horizontal Bar Chart */}
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-300">Horizontal</h3>
              <BarChart
                data={benchmarkData}
                xKey="model"
                yKeys={['latency']}
                colors={['#3b82f6']}
                xLabel="Latency (ms)"
                height={350}
                horizontal
                showLegend={false}
                showValues
              />
            </div>
          </div>

          {/* Grouped Bar Chart */}
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-gray-300">Grouped Comparison</h3>
            <BarChart
              data={benchmarkData}
              xKey="model"
              yKeys={['throughput', 'latency']}
              colors={['#76B900', '#f59e0b']}
              yLabel="Performance Metrics"
              height={400}
              showLegend
            />
          </div>
        </section>

        {/* Performance Gauges */}
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <Gauge className="w-6 h-6 text-nvidia-green" />
            <h2 className="text-2xl font-bold">Performance Gauges</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 p-8 rounded-xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 backdrop-blur-sm">
            <PerformanceGauge
              value={95}
              label="Excellent"
              description="90-100%"
              size="md"
            />
            <PerformanceGauge
              value={80}
              label="Good"
              description="70-89%"
              size="md"
            />
            <PerformanceGauge
              value={60}
              label="Fair"
              description="50-69%"
              size="md"
            />
            <PerformanceGauge
              value={35}
              label="Poor"
              description="30-49%"
              size="md"
            />
          </div>
        </section>

        {/* Individual Metric Cards */}
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <Cpu className="w-6 h-6 text-nvidia-green" />
            <h2 className="text-2xl font-bold">Individual Metric Cards</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              icon={Zap}
              label="Throughput"
              value={1250.5}
              unit="req/s"
              trend={12.5}
              trendLabel="vs last hour"
              color="green"
            />
            <MetricCard
              icon={Clock}
              label="Latency"
              value={45.2}
              unit="ms"
              trend={-5.3}
              trendLabel="improvement"
              color="blue"
            />
            <MetricCard
              icon={Target}
              label="Tokens"
              value={15420}
              unit="tok/s"
              color="purple"
            />
            <MetricCard
              icon={TrendingUp}
              label="Error Rate"
              value={0.02}
              unit="%"
              trend={-15.2}
              trendLabel="vs last hour"
              color="red"
            />
          </div>
        </section>

        {/* Loading States */}
        <section className="space-y-4">
          <h2 className="text-2xl font-bold">Loading States</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <MetricCard
              icon={Zap}
              label="Loading Metric"
              value={0}
              loading
            />
            <div>
              <PerformanceGauge
                value={0}
                label="Loading Gauge"
                loading
              />
            </div>
          </div>
        </section>

        {/* Empty States */}
        <section className="space-y-4">
          <h2 className="text-2xl font-bold">Empty States</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <LineChart
              data={[]}
              xKey="time"
              yKeys={['value']}
              height={300}
            />
            <BarChart
              data={[]}
              xKey="category"
              yKeys={['value']}
              height={300}
            />
          </div>
        </section>
      </div>
    </div>
  )
}
