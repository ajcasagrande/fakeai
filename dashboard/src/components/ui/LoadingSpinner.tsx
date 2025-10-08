import * as React from "react"
import { motion } from "framer-motion"
import { Loader2, Activity } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * NVIDIA-themed loading spinner component
 *
 * @component
 * @example
 * ```tsx
 * <LoadingSpinner />
 * <LoadingSpinner size="lg" />
 * <LoadingSpinner variant="nvidia" text="Loading..." />
 * <LoadingSpinner variant="pulse" />
 * ```
 */

export interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: "sm" | "md" | "lg" | "xl"
  /** Spinner variant */
  variant?: "spinner" | "nvidia" | "pulse" | "dots"
  /** Optional loading text */
  text?: string
  /** Additional CSS classes */
  className?: string
  /** Center the spinner in its container */
  centered?: boolean
}

const sizeClasses = {
  sm: "w-4 h-4",
  md: "w-8 h-8",
  lg: "w-12 h-12",
  xl: "w-16 h-16",
}

const LoadingSpinner = React.forwardRef<HTMLDivElement, LoadingSpinnerProps>(
  (
    {
      size = "md",
      variant = "spinner",
      text,
      className,
      centered = false,
    },
    ref
  ) => {
    const containerClasses = cn(
      "flex flex-col items-center justify-center gap-3",
      centered && "min-h-[200px]",
      className
    )

    const renderSpinner = () => {
      switch (variant) {
        case "spinner":
          return (
            <div
              className={cn(
                sizeClasses[size],
                "border-4 border-nvidia-green/20 border-t-nvidia-green rounded-full animate-spin"
              )}
            />
          )

        case "nvidia":
          return (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              <Activity className={cn(sizeClasses[size], "text-nvidia-green")} />
            </motion.div>
          )

        case "pulse":
          return (
            <motion.div
              animate={{
                scale: [1, 1.2, 1],
                opacity: [1, 0.5, 1],
              }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
              className={cn(
                sizeClasses[size],
                "bg-nvidia-green rounded-full"
              )}
            />
          )

        case "dots":
          return (
            <div className="flex gap-2">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  animate={{
                    y: [0, -10, 0],
                  }}
                  transition={{
                    duration: 0.6,
                    repeat: Infinity,
                    delay: i * 0.15,
                    ease: "easeInOut",
                  }}
                  className={cn(
                    "w-3 h-3 bg-nvidia-green rounded-full",
                    size === "sm" && "w-2 h-2",
                    size === "lg" && "w-4 h-4",
                    size === "xl" && "w-5 h-5"
                  )}
                />
              ))}
            </div>
          )

        default:
          return null
      }
    }

    return (
      <div ref={ref} className={containerClasses}>
        {renderSpinner()}
        {text && (
          <p className="text-sm text-gray-400 animate-pulse">{text}</p>
        )}
      </div>
    )
  }
)
LoadingSpinner.displayName = "LoadingSpinner"

/**
 * Full-screen loading overlay
 */
export interface LoadingOverlayProps {
  text?: string
  variant?: LoadingSpinnerProps["variant"]
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  text = "Loading...",
  variant = "nvidia",
}) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50"
    >
      <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-8">
        <LoadingSpinner size="xl" variant={variant} text={text} />
      </div>
    </motion.div>
  )
}
LoadingOverlay.displayName = "LoadingOverlay"

/**
 * Inline loading spinner for buttons
 */
export interface ButtonSpinnerProps {
  className?: string
}

const ButtonSpinner: React.FC<ButtonSpinnerProps> = ({ className }) => {
  return (
    <Loader2 className={cn("w-4 h-4 animate-spin", className)} />
  )
}
ButtonSpinner.displayName = "ButtonSpinner"

/**
 * Loading skeleton component
 */
export interface LoadingSkeletonProps {
  className?: string
  count?: number
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  className,
  count = 1,
}) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "animate-pulse bg-white/10 rounded-lg",
            className
          )}
        />
      ))}
    </>
  )
}
LoadingSkeleton.displayName = "LoadingSkeleton"

export { LoadingSpinner, LoadingOverlay, ButtonSpinner, LoadingSkeleton }
