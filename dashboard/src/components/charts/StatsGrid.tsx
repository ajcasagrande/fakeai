'use client'

import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import { MetricCard } from './MetricCard'

interface Stat {
  id: string
  icon: LucideIcon
  label: string
  value: string | number
  unit?: string
  trend?: number
  trendLabel?: string
  color?: 'green' | 'blue' | 'yellow' | 'red' | 'purple' | 'gray'
}

interface StatsGridProps {
  stats: Stat[]
  loading?: boolean
  columns?: 1 | 2 | 3 | 4
  gap?: number
}

export function StatsGrid({
  stats,
  loading = false,
  columns = 4,
  gap = 6,
}: StatsGridProps) {
  const gridColsMap = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  }

  const gapMap = {
    2: 'gap-2',
    4: 'gap-4',
    6: 'gap-6',
    8: 'gap-8',
  }

  if (!stats || stats.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 backdrop-blur-sm p-12 text-center"
      >
        <p className="text-gray-400">No statistics available</p>
      </motion.div>
    )
  }

  return (
    <div className={`grid ${gridColsMap[columns]} ${gapMap[gap as keyof typeof gapMap] || 'gap-6'}`}>
      {stats.map((stat, index) => (
        <MetricCard
          key={stat.id}
          icon={stat.icon}
          label={stat.label}
          value={stat.value}
          unit={stat.unit}
          trend={stat.trend}
          trendLabel={stat.trendLabel}
          color={stat.color}
          loading={loading}
          delay={index * 0.05}
        />
      ))}
    </div>
  )
}
