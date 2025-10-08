'use client'

import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { motion } from 'framer-motion'

interface DataPoint {
  [key: string]: string | number
}

interface LineChartProps {
  data: DataPoint[]
  xKey: string
  yKeys: string[]
  colors?: string[]
  xLabel?: string
  yLabel?: string
  loading?: boolean
  height?: number
  showLegend?: boolean
  smooth?: boolean
}

export function LineChart({
  data,
  xKey,
  yKeys,
  colors = ['#76B900', '#3b82f6', '#f59e0b', '#ef4444'],
  xLabel,
  yLabel,
  loading = false,
  height = 400,
  showLegend = true,
  smooth = true,
}: LineChartProps) {
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center justify-center"
        style={{ height }}
      >
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-nvidia-green border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 text-sm">Loading chart data...</p>
        </div>
      </motion.div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-center rounded-xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 backdrop-blur-sm"
        style={{ height }}
      >
        <p className="text-gray-400">No data available</p>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="rounded-xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 backdrop-blur-sm p-6"
    >
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart data={data}>
          <defs>
            {yKeys.map((key, index) => (
              <linearGradient key={key} id={`gradient-${key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={colors[index % colors.length]} stopOpacity={0.8} />
                <stop offset="95%" stopColor={colors[index % colors.length]} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.3} />
          <XAxis
            dataKey={xKey}
            stroke="#666"
            tick={{ fill: '#999' }}
            label={xLabel ? { value: xLabel, position: 'insideBottom', offset: -5, fill: '#999' } : undefined}
          />
          <YAxis
            stroke="#666"
            tick={{ fill: '#999' }}
            label={yLabel ? { value: yLabel, angle: -90, position: 'insideLeft', fill: '#999' } : undefined}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.9)',
              border: '1px solid rgba(118, 185, 0, 0.3)',
              borderRadius: '8px',
              backdropFilter: 'blur(10px)',
            }}
            labelStyle={{ color: '#999', fontWeight: 'bold' }}
            itemStyle={{ color: '#fff' }}
            formatter={(value: number) => (typeof value === 'number' ? value.toFixed(2) : value)}
          />
          {showLegend && (
            <Legend
              wrapperStyle={{ color: '#999' }}
              iconType="line"
            />
          )}
          {yKeys.map((key, index) => (
            <Line
              key={key}
              type={smooth ? 'monotone' : 'linear'}
              dataKey={key}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ fill: colors[index % colors.length], r: 4 }}
              activeDot={{ r: 6, stroke: colors[index % colors.length], strokeWidth: 2, fill: '#000' }}
              animationDuration={1000}
              animationEasing="ease-in-out"
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </motion.div>
  )
}
