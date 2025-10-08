'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface PerformanceGaugeProps {
  value: number
  maxValue?: number
  label: string
  description?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  loading?: boolean
  showPercentage?: boolean
}

const sizeMap = {
  sm: { width: 96, strokeWidth: 8, text: 'text-xl', label: 'text-xs' },
  md: { width: 128, strokeWidth: 10, text: 'text-2xl', label: 'text-sm' },
  lg: { width: 160, strokeWidth: 12, text: 'text-3xl', label: 'text-base' },
  xl: { width: 192, strokeWidth: 14, text: 'text-4xl', label: 'text-lg' },
}

export function PerformanceGauge({
  value,
  maxValue = 100,
  label,
  description,
  size = 'md',
  loading = false,
  showPercentage = true,
}: PerformanceGaugeProps) {
  const [animatedValue, setAnimatedValue] = useState(0)
  const percentage = Math.min(Math.max((value / maxValue) * 100, 0), 100)
  const sizes = sizeMap[size]
  const { width, strokeWidth } = sizes
  const radius = (width - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (animatedValue / 100) * circumference

  useEffect(() => {
    if (!loading) {
      const timer = setTimeout(() => {
        setAnimatedValue(percentage)
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [percentage, loading])

  const getColor = (percent: number): string => {
    if (percent >= 90) return '#76B900' // NVIDIA green
    if (percent >= 70) return '#3b82f6' // Blue
    if (percent >= 50) return '#f59e0b' // Yellow
    if (percent >= 30) return '#f97316' // Orange
    return '#ef4444' // Red
  }

  const getTrailColor = (percent: number): string => {
    if (percent >= 90) return 'rgba(118, 185, 0, 0.1)'
    if (percent >= 70) return 'rgba(59, 130, 246, 0.1)'
    if (percent >= 50) return 'rgba(245, 158, 11, 0.1)'
    if (percent >= 30) return 'rgba(249, 115, 22, 0.1)'
    return 'rgba(239, 68, 68, 0.1)'
  }

  const color = getColor(percentage)
  const trailColor = getTrailColor(percentage)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center gap-4"
    >
      {/* Gauge */}
      <div className="relative">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
          style={{ width, height: width }}
        >
          {loading ? (
            <div className="flex items-center justify-center w-full h-full">
              <div
                className="border-4 border-nvidia-green border-t-transparent rounded-full animate-spin"
                style={{ width: width * 0.75, height: width * 0.75 }}
              />
            </div>
          ) : (
            <svg width={width} height={width} className="transform -rotate-90">
              {/* Background circle */}
              <circle
                cx={width / 2}
                cy={width / 2}
                r={radius}
                fill="none"
                stroke={trailColor}
                strokeWidth={strokeWidth}
              />
              {/* Progress circle */}
              <motion.circle
                cx={width / 2}
                cy={width / 2}
                r={radius}
                fill="none"
                stroke={color}
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                strokeDasharray={circumference}
                initial={{ strokeDashoffset: circumference }}
                animate={{ strokeDashoffset: offset }}
                transition={{ duration: 1, ease: 'easeOut' }}
                style={{ filter: `drop-shadow(0 0 8px ${color}40)` }}
              />
              {/* Center text */}
              {showPercentage && (
                <text
                  x="50%"
                  y="50%"
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className={`font-bold transform rotate-90 origin-center ${sizes.text}`}
                  fill={color}
                >
                  {animatedValue.toFixed(0)}%
                </text>
              )}
            </svg>
          )}
        </motion.div>

        {/* Glow effect */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute inset-0 -z-10 rounded-full blur-xl"
          style={{ backgroundColor: color }}
        />
      </div>

      {/* Label and Description */}
      <div className="text-center space-y-1">
        <p className={`font-bold text-white ${sizes.label}`}>{label}</p>
        {description && (
          <p className="text-gray-400 text-xs">{description}</p>
        )}
        {!showPercentage && !loading && (
          <p className={`font-mono ${sizes.text}`} style={{ color }}>
            {value.toFixed(1)}
            {maxValue !== 100 && <span className="text-gray-500 text-sm ml-1">/ {maxValue}</span>}
          </p>
        )}
      </div>
    </motion.div>
  )
}
