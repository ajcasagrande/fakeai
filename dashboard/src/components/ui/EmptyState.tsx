import * as React from "react"
import { motion } from "framer-motion"
import { LucideIcon } from "lucide-react"
import { Button } from "./Button"
import { cn } from "@/lib/utils"

/**
 * Empty state component for displaying no data/content scenarios
 *
 * @component
 * @example
 * ```tsx
 * <EmptyState
 *   icon={Database}
 *   title="No Data Available"
 *   description="Upload your first benchmark to get started"
 *   action={{ label: "Upload", onClick: handleUpload }}
 * />
 * ```
 */

export interface EmptyStateProps {
  /** Icon to display */
  icon: LucideIcon
  /** Title text */
  title: string
  /** Description text */
  description?: string
  /** Primary action button */
  action?: {
    label: string
    onClick: () => void
    variant?: "primary" | "secondary" | "ghost"
  }
  /** Secondary action button */
  secondaryAction?: {
    label: string
    onClick: () => void
  }
  /** Additional CSS classes */
  className?: string
  /** Size variant */
  size?: "sm" | "md" | "lg"
}

const sizeConfig = {
  sm: {
    icon: "w-12 h-12",
    title: "text-lg",
    description: "text-sm",
    padding: "p-6",
  },
  md: {
    icon: "w-16 h-16",
    title: "text-xl",
    description: "text-base",
    padding: "p-8",
  },
  lg: {
    icon: "w-20 h-20",
    title: "text-2xl",
    description: "text-lg",
    padding: "p-12",
  },
}

const EmptyState = React.forwardRef<HTMLDivElement, EmptyStateProps>(
  (
    {
      icon: Icon,
      title,
      description,
      action,
      secondaryAction,
      className,
      size = "md",
    },
    ref
  ) => {
    const config = sizeConfig[size]

    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className={cn(
          "flex flex-col items-center justify-center text-center",
          config.padding,
          className
        )}
      >
        {/* Icon */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="mb-6"
        >
          <div className="bg-white/5 border border-white/10 rounded-full p-6">
            <Icon className={cn(config.icon, "text-nvidia-green")} />
          </div>
        </motion.div>

        {/* Title */}
        <motion.h3
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className={cn(config.title, "font-bold text-white mb-2")}
        >
          {title}
        </motion.h3>

        {/* Description */}
        {description && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className={cn(config.description, "text-gray-400 mb-6 max-w-md")}
          >
            {description}
          </motion.p>
        )}

        {/* Actions */}
        {(action || secondaryAction) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="flex flex-wrap gap-3 justify-center"
          >
            {action && (
              <Button
                variant={action.variant || "primary"}
                onClick={action.onClick}
              >
                {action.label}
              </Button>
            )}
            {secondaryAction && (
              <Button
                variant="ghost"
                onClick={secondaryAction.onClick}
              >
                {secondaryAction.label}
              </Button>
            )}
          </motion.div>
        )}
      </motion.div>
    )
  }
)
EmptyState.displayName = "EmptyState"

/**
 * Minimal empty state without actions
 */
export interface SimpleEmptyStateProps {
  icon: LucideIcon
  message: string
  className?: string
}

const SimpleEmptyState: React.FC<SimpleEmptyStateProps> = ({
  icon: Icon,
  message,
  className,
}) => {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 text-center",
        className
      )}
    >
      <Icon className="w-12 h-12 text-gray-500 mb-3" />
      <p className="text-sm text-gray-400">{message}</p>
    </div>
  )
}
SimpleEmptyState.displayName = "SimpleEmptyState"

/**
 * Empty state for search/filter with no results
 */
export interface NoResultsStateProps {
  searchQuery?: string
  onClear?: () => void
  className?: string
}

const NoResultsState: React.FC<NoResultsStateProps> = ({
  searchQuery,
  onClear,
  className,
}) => {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 text-center",
        className
      )}
    >
      <div className="bg-white/5 border border-white/10 rounded-full p-4 mb-4">
        <svg
          className="w-12 h-12 text-gray-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-bold text-white mb-2">No Results Found</h3>
      <p className="text-sm text-gray-400 mb-4 max-w-sm">
        {searchQuery
          ? `No results for "${searchQuery}". Try adjusting your search.`
          : "No items match your current filters."}
      </p>
      {onClear && (
        <Button variant="ghost" onClick={onClear} size="sm">
          Clear Filters
        </Button>
      )}
    </div>
  )
}
NoResultsState.displayName = "NoResultsState"

export { EmptyState, SimpleEmptyState, NoResultsState }
