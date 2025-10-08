import * as React from "react"
import { motion } from "framer-motion"
import { TrendingUp, TrendingDown, Minus, LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * Metric display card with icon, label, value, and trend indicator
 *
 * @component
 * @example
 * ```tsx
 * <StatCard
 *   icon={Zap}
 *   label="Throughput"
 *   value="1,234.56"
 *   unit="req/s"
 *   trend={{ value: 12.5, direction: "up" }}
 *   color="green"
 * />
 * ```
 */

export interface StatCardProps {
  /** Icon component from lucide-react */
  icon: LucideIcon
  /** Label text */
  label: string
  /** Main value to display */
  value: string | number
  /** Optional unit (e.g., "req/s", "ms", "%") */
  unit?: string
  /** Trend indicator */
  trend?: {
    value: number
    direction: "up" | "down" | "neutral"
  }
  /** Color theme */
  color?: "green" | "blue" | "purple" | "orange" | "pink" | "red"
  /** Additional CSS classes */
  className?: string
  /** Delay for animation (in seconds) */
  delay?: number
}

const colorClasses = {
  green: "text-green-400",
  blue: "text-blue-400",
  purple: "text-purple-400",
  orange: "text-orange-400",
  pink: "text-pink-400",
  red: "text-red-400",
}

const StatCard = React.forwardRef<HTMLDivElement, StatCardProps>(
  (
    {
      icon: Icon,
      label,
      value,
      unit,
      trend,
      color = "green",
      className,
      delay = 0,
    },
    ref
  ) => {
    const getTrendIcon = () => {
      if (!trend) return null
      switch (trend.direction) {
        case "up":
          return <TrendingUp className="w-4 h-4 text-green-400" />
        case "down":
          return <TrendingDown className="w-4 h-4 text-red-400" />
        case "neutral":
          return <Minus className="w-4 h-4 text-gray-400" />
      }
    }

    const getTrendColor = () => {
      if (!trend) return ""
      switch (trend.direction) {
        case "up":
          return "text-green-400"
        case "down":
          return "text-red-400"
        case "neutral":
          return "text-gray-400"
      }
    }

    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay }}
        whileHover={{ scale: 1.02 }}
        className={cn(
          "bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:border-nvidia-green/50 transition-colors",
          className
        )}
      >
        {/* Icon */}
        <div className={cn("mb-4", colorClasses[color])}>
          <Icon className="w-6 h-6" />
        </div>

        {/* Value and Unit */}
        <div className="mb-2">
          <span className="text-3xl font-bold text-white">
            {value}
          </span>
          {unit && (
            <span className="text-lg text-gray-400 ml-2">{unit}</span>
          )}
        </div>

        {/* Label and Trend */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">{label}</span>
          {trend && (
            <div className="flex items-center gap-1">
              {getTrendIcon()}
              <span className={cn("text-xs font-semibold", getTrendColor())}>
                {Math.abs(trend.value)}%
              </span>
            </div>
          )}
        </div>
      </motion.div>
    )
  }
)
StatCard.displayName = "StatCard"

/**
 * Simplified stat card for inline metrics
 */
export interface SimpleStatCardProps {
  label: string
  value: string | number
  unit?: string
  className?: string
}

const SimpleStatCard = React.forwardRef<HTMLDivElement, SimpleStatCardProps>(
  ({ label, value, unit, className }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-black/30 rounded-lg p-3 text-center",
          className
        )}
      >
        <div className="text-xs text-gray-400 mb-1">{label}</div>
        <div className="text-lg font-bold text-white">
          {value}
          {unit && <span className="text-sm text-gray-400 ml-1">{unit}</span>}
        </div>
      </div>
    )
  }
)
SimpleStatCard.displayName = "SimpleStatCard"

export { StatCard, SimpleStatCard }
