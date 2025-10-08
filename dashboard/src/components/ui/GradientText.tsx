import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

/**
 * Flat colored text component for eye-catching headings and text
 *
 * @component
 * @example
 * ```tsx
 * <GradientText>NVIDIA Performance</GradientText>
 * <GradientText variant="blue" size="lg">Blue Text</GradientText>
 * <GradientText animated>Animated Text</GradientText>
 * ```
 */

export interface GradientTextProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Color variant */
  variant?: "nvidia" | "blue" | "purple" | "orange" | "pink" | "rainbow"
  /** Text size */
  size?: "sm" | "md" | "lg" | "xl" | "2xl" | "3xl"
  /** Enable shimmer animation */
  animated?: boolean
  /** Use as a specific HTML element */
  as?: "span" | "h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "p"
}

const colorVariants = {
  nvidia: "text-nvidia-green",
  blue: "text-blue-400",
  purple: "text-purple-400",
  orange: "text-orange-400",
  pink: "text-pink-400",
  rainbow: "text-nvidia-green",
}

const sizeClasses = {
  sm: "text-sm",
  md: "text-base",
  lg: "text-lg",
  xl: "text-xl",
  "2xl": "text-2xl",
  "3xl": "text-3xl",
}

const GradientText = React.forwardRef<
  HTMLSpanElement,
  GradientTextProps
>(
  (
    {
      variant = "nvidia",
      size = "md",
      animated = false,
      as: Component = "span",
      className,
      children,
      ...props
    },
    ref
  ) => {
    const colorClass = colorVariants[variant]
    const baseClasses = cn(
      "font-bold",
      colorClass,
      sizeClasses[size],
      className
    )

    if (animated) {
      return (
        <motion.span
          ref={ref}
          className={baseClasses}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          {...(props as any)}
        >
          {children}
        </motion.span>
      )
    }

    return React.createElement(
      Component,
      {
        ref,
        className: baseClasses,
        ...props,
      },
      children
    )
  }
)
GradientText.displayName = "GradientText"

/**
 * Animated gradient heading component
 */
export interface AnimatedGradientHeadingProps {
  children: React.ReactNode
  variant?: GradientTextProps["variant"]
  className?: string
}

const AnimatedGradientHeading: React.FC<AnimatedGradientHeadingProps> = ({
  children,
  variant = "nvidia",
  className,
}) => {
  return (
    <motion.h1
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={cn(
        "font-bold text-4xl md:text-5xl lg:text-6xl",
        colorVariants[variant],
        className
      )}
    >
      {children}
    </motion.h1>
  )
}
AnimatedGradientHeading.displayName = "AnimatedGradientHeading"

/**
 * Flat badge component
 */
export interface GradientBadgeProps {
  children: React.ReactNode
  variant?: GradientTextProps["variant"]
  className?: string
}

const GradientBadge: React.FC<GradientBadgeProps> = ({
  children,
  variant = "nvidia",
  className,
}) => {
  const bgColor = variant === "nvidia" ? "bg-nvidia-green text-black" :
                  variant === "blue" ? "bg-blue-400 text-black" :
                  variant === "purple" ? "bg-purple-400 text-black" :
                  variant === "orange" ? "bg-orange-400 text-black" :
                  variant === "pink" ? "bg-pink-400 text-black" :
                  "bg-nvidia-green text-black";

  return (
    <div
      className={cn(
        "inline-flex items-center px-4 py-2 font-bold text-sm border-2",
        bgColor,
        className
      )}
    >
      {children}
    </div>
  )
}
GradientBadge.displayName = "GradientBadge"

export { GradientText, AnimatedGradientHeading, GradientBadge }
