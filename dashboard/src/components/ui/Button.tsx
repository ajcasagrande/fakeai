import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { motion, HTMLMotionProps } from "framer-motion"
import { cn } from "@/lib/utils"

/**
 * Button component with NVIDIA-themed variants and Framer Motion animations
 *
 * @component
 * @example
 * ```tsx
 * <Button variant="primary">Click me</Button>
 * <Button variant="secondary" size="lg">Large button</Button>
 * <Button variant="ghost">Ghost button</Button>
 * ```
 */

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-nvidia-green disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        /** NVIDIA green primary button - flat design */
        primary:
          "bg-nvidia-green text-black hover:bg-nvidia-green/80 font-bold",
        /** Flat secondary button */
        secondary:
          "bg-[#1a1a1a] text-nvidia-green border-2 border-nvidia-green hover:bg-nvidia-green/10 font-bold",
        /** Ghost button with hover effect */
        ghost:
          "bg-transparent text-white hover:bg-nvidia-green/10 border-2 border-nvidia-green/20 hover:border-nvidia-green",
        /** Outline variant */
        outline:
          "border-2 border-nvidia-green/40 bg-transparent text-white hover:bg-nvidia-green/10 hover:border-nvidia-green",
        /** Destructive/danger button */
        destructive:
          "bg-red-500 text-white hover:bg-red-600",
        /** Link style button */
        link:
          "text-nvidia-green underline-offset-4 hover:underline hover:text-nvidia-green/80",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3 text-xs",
        lg: "h-11 px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Render as a child component */
  asChild?: boolean
  /** Enable Framer Motion animations */
  animated?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, animated = true, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    const classes = cn(buttonVariants({ variant, size, className }))

    if (animated && !asChild) {
      return (
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={classes}
          ref={ref}
          {...(props as any)}
        >
          {children}
        </motion.button>
      )
    }

    return (
      <Comp
        className={classes}
        ref={ref}
        {...props}
      >
        {children}
      </Comp>
    )
  }
)
Button.displayName = "Button"

/**
 * Icon button with consistent sizing
 */
export interface IconButtonProps extends ButtonProps {
  icon: React.ReactNode
}

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ icon, className, ...props }, ref) => {
    return (
      <Button
        ref={ref}
        size="icon"
        className={className}
        {...props}
      >
        {icon}
      </Button>
    )
  }
)
IconButton.displayName = "IconButton"

export { Button, IconButton, buttonVariants }
