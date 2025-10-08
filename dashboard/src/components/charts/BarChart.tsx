'use client'

import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { motion } from 'framer-motion'

interface DataPoint {
  [key: string]: string | number
}

interface BarChartProps {
  data: DataPoint[]
  xKey: string
  yKeys: string[]
  colors?: string[]
  xLabel?: string
  yLabel?: string
  loading?: boolean
  height?: number
  showLegend?: boolean
  horizontal?: boolean
  showValues?: boolean
}

export function BarChart({
  data,
  xKey,
  yKeys,
  colors = ['#76B900', '#3b82f6', '#f59e0b', '#ef4444'],
  xLabel,
  yLabel,
  loading = false,
  height = 400,
  showLegend = true,
  horizontal = false,
  showValues = false,
}: BarChartProps) {
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

  const CustomLabel = ({ x, y, width, height, value }: any) => {
    if (!showValues) return null
    const labelX = horizontal ? x + width + 5 : x + width / 2
    const labelY = horizontal ? y + height / 2 + 5 : y - 5
    return (
      <text
        x={labelX}
        y={labelY}
        fill="#999"
        textAnchor={horizontal ? 'start' : 'middle'}
        fontSize="12"
      >
        {typeof value === 'number' ? value.toFixed(1) : value}
      </text>
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
        <RechartsBarChart
          data={data}
          layout={horizontal ? 'horizontal' : 'vertical'}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.3} />
          {horizontal ? (
            <>
              <XAxis
                type="number"
                stroke="#666"
                tick={{ fill: '#999' }}
                label={xLabel ? { value: xLabel, position: 'insideBottom', offset: -5, fill: '#999' } : undefined}
              />
              <YAxis
                type="category"
                dataKey={xKey}
                stroke="#666"
                tick={{ fill: '#999' }}
                width={100}
                label={yLabel ? { value: yLabel, angle: -90, position: 'insideLeft', fill: '#999' } : undefined}
              />
            </>
          ) : (
            <>
              <XAxis
                dataKey={xKey}
                stroke="#666"
                tick={{ fill: '#999' }}
                angle={-45}
                textAnchor="end"
                height={80}
                label={xLabel ? { value: xLabel, position: 'insideBottom', offset: -50, fill: '#999' } : undefined}
              />
              <YAxis
                stroke="#666"
                tick={{ fill: '#999' }}
                label={yLabel ? { value: yLabel, angle: -90, position: 'insideLeft', fill: '#999' } : undefined}
              />
            </>
          )}
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
            cursor={{ fill: 'rgba(118, 185, 0, 0.1)' }}
          />
          {showLegend && (
            <Legend
              wrapperStyle={{ color: '#999' }}
              iconType="square"
            />
          )}
          {yKeys.map((key, index) => (
            <Bar
              key={key}
              dataKey={key}
              fill={colors[index % colors.length]}
              radius={[4, 4, 0, 0]}
              animationDuration={1000}
              animationEasing="ease-in-out"
              label={showValues ? <CustomLabel /> : undefined}
            >
              {data.map((entry, idx) => (
                <Cell
                  key={`cell-${idx}`}
                  fill={colors[index % colors.length]}
                  opacity={0.9}
                  className="transition-opacity hover:opacity-100"
                />
              ))}
            </Bar>
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </motion.div>
  )
}
