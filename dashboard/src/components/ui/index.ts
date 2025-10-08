/**
 * UI Component Library - NVIDIA Themed
 *
 * A comprehensive set of reusable UI components with glass morphism styling,
 * NVIDIA branding, and Framer Motion animations.
 *
 * @module ui
 */

// Card components
export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  type CardProps,
} from "./Card"

// Button components
export {
  Button,
  IconButton,
  buttonVariants,
  type ButtonProps,
  type IconButtonProps,
} from "./Button"

// Badge components
export {
  Badge,
  PulseBadge,
  badgeVariants,
  type BadgeProps,
  type PulseBadgeProps,
} from "./Badge"

// Stat card components
export {
  StatCard,
  SimpleStatCard,
  type StatCardProps,
  type SimpleStatCardProps,
} from "./StatCard"

// Gradient text components
export {
  GradientText,
  AnimatedGradientHeading,
  GradientBadge,
  type GradientTextProps,
  type AnimatedGradientHeadingProps,
  type GradientBadgeProps,
} from "./GradientText"

// Loading components
export {
  LoadingSpinner,
  LoadingOverlay,
  ButtonSpinner,
  LoadingSkeleton,
  type LoadingSpinnerProps,
  type LoadingOverlayProps,
  type ButtonSpinnerProps,
  type LoadingSkeletonProps,
} from "./LoadingSpinner"

// Empty state components
export {
  EmptyState,
  SimpleEmptyState,
  NoResultsState,
  type EmptyStateProps,
  type SimpleEmptyStateProps,
  type NoResultsStateProps,
} from "./EmptyState"

// Legacy components (for backward compatibility)
export { Input } from "./input"
export { Label } from "./label"
export { Tabs, TabsContent, TabsList, TabsTrigger } from "./tabs"
