'use client'

import { motion } from 'framer-motion'
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface MetricCardProps {
  icon: LucideIcon
  label: string
  value: string | number
  unit?: string
  trend?: number
  trendLabel?: string
  loading?: boolean
  color?: 'green' | 'blue' | 'yellow' | 'red' | 'purple' | 'gray'
  delay?: number
}

const colorMap = {
  green: {
    icon: 'text-nvidia-green',
    gradient: 'from-nvidia-green/20 to-nvidia-green/5',
    border: 'border-nvidia-green/30',
    value: 'text-nvidia-green',
    trend: 'text-nvidia-green',
  },
  blue: {
    icon: 'text-blue-400',
    gradient: 'from-blue-400/20 to-blue-400/5',
    border: 'border-blue-400/30',
    value: 'text-blue-400',
    trend: 'text-blue-400',
  },
  yellow: {
    icon: 'text-yellow-400',
    gradient: 'from-yellow-400/20 to-yellow-400/5',
    border: 'border-yellow-400/30',
    value: 'text-yellow-400',
    trend: 'text-yellow-400',
  },
  red: {
    icon: 'text-red-400',
    gradient: 'from-red-400/20 to-red-400/5',
    border: 'border-red-400/30',
    value: 'text-red-400',
    trend: 'text-red-400',
  },
  purple: {
    icon: 'text-purple-400',
    gradient: 'from-purple-400/20 to-purple-400/5',
    border: 'border-purple-400/30',
    value: 'text-purple-400',
    trend: 'text-purple-400',
  },
  gray: {
    icon: 'text-gray-400',
    gradient: 'from-white/10 to-white/0',
    border: 'border-white/10',
    value: 'text-white',
    trend: 'text-gray-400',
  },
}

export function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  trend,
  trendLabel,
  loading = false,
  color = 'green',
  delay = 0,
}: MetricCardProps) {
  const colors = colorMap[color]

  const getTrendIcon = () => {
    if (trend === undefined || trend === null) return null
    if (trend > 0) return <TrendingUp className="w-4 h-4" />
    if (trend < 0) return <TrendingDown className="w-4 h-4" />
    return <Minus className="w-4 h-4" />
  }

  const getTrendColor = () => {
    if (trend === undefined || trend === null) return 'text-gray-500'
    if (trend > 0) return 'text-green-400'
    if (trend < 0) return 'text-red-400'
    return 'text-gray-400'
  }

  const formatValue = (val: string | number): string => {
    if (typeof val === 'number') {
      if (val >= 1000000) return `${(val / 1000000).toFixed(2)}M`
      if (val >= 1000) return `${(val / 1000).toFixed(2)}K`
      if (val % 1 !== 0) return val.toFixed(2)
      return val.toString()
    }
    return val
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ scale: 1.02, y: -2 }}
      className={`relative rounded-xl bg-gradient-to-br ${colors.gradient} border ${colors.border} backdrop-blur-sm p-6 overflow-hidden group cursor-default`}
    >
      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-radial from-white/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div className="relative z-10">
        {/* Icon and Label */}
        <div className="flex items-start justify-between mb-4">
          <div className={`p-3 rounded-lg bg-black/30 ${colors.icon}`}>
            <Icon className="w-6 h-6" />
          </div>
          {trend !== undefined && trend !== null && (
            <div className={`flex items-center gap-1 text-sm font-medium ${getTrendColor()}`}>
              {getTrendIcon()}
              <span>{Math.abs(trend)}%</span>
            </div>
          )}
        </div>

        {/* Label */}
        <p className="text-gray-400 text-sm mb-2">{label}</p>

        {/* Value */}
        {loading ? (
          <div className="h-10 bg-white/10 rounded animate-pulse" />
        ) : (
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-bold ${colors.value}`}>
              {formatValue(value)}
            </span>
            {unit && <span className="text-gray-500 text-lg">{unit}</span>}
          </div>
        )}

        {/* Trend Label */}
        {trendLabel && (
          <p className="text-gray-500 text-xs mt-2">{trendLabel}</p>
        )}
      </div>

      {/* Shine effect on hover */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full"
        whileHover={{ translateX: '100%' }}
        transition={{ duration: 0.6 }}
      />
    </motion.div>
  )
}
