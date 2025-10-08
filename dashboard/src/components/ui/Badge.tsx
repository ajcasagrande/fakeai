import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

/**
 * Status badge component with colored variants
 *
 * @component
 * @example
 * ```tsx
 * <Badge variant="success">Active</Badge>
 * <Badge variant="warning">Pending</Badge>
 * <Badge variant="error">Failed</Badge>
 * <Badge variant="info">Info</Badge>
 * ```
 */

const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-full px-3 py-1 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        /** Success/green badge */
        success: "bg-green-500/20 text-green-400 border border-green-500/30",
        /** Warning/yellow badge */
        warning: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
        /** Error/red badge */
        error: "bg-red-500/20 text-red-400 border border-red-500/30",
        /** Info/blue badge */
        info: "bg-blue-500/20 text-blue-400 border border-blue-500/30",
        /** NVIDIA green badge */
        nvidia: "bg-nvidia-green/20 text-nvidia-green border border-nvidia-green/30",
        /** Purple badge */
        purple: "bg-purple-500/20 text-purple-400 border border-purple-500/30",
        /** Default/gray badge */
        default: "bg-gray-500/20 text-gray-400 border border-gray-500/30",
      },
      size: {
        sm: "text-xs px-2 py-0.5",
        default: "text-xs px-3 py-1",
        lg: "text-sm px-4 py-1.5",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  /** Optional icon to display before text */
  icon?: React.ReactNode
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant, size, icon, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(badgeVariants({ variant, size }), className)}
        {...props}
      >
        {icon && <span className="mr-1.5">{icon}</span>}
        {children}
      </div>
    )
  }
)
Badge.displayName = "Badge"

/**
 * Status badge with pulsing animation for active states
 */
export interface PulseBadgeProps extends BadgeProps {
  pulse?: boolean
}

const PulseBadge = React.forwardRef<HTMLDivElement, PulseBadgeProps>(
  ({ pulse = true, className, children, ...props }, ref) => {
    return (
      <Badge
        ref={ref}
        className={cn(pulse && "animate-pulse-slow", className)}
        {...props}
      >
        {pulse && (
          <span className="relative flex h-2 w-2 mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-current"></span>
          </span>
        )}
        {children}
      </Badge>
    )
  }
)
PulseBadge.displayName = "PulseBadge"

export { Badge, PulseBadge, badgeVariants }
