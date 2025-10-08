/**
 * Component Showcase - Demo of all UI components
 *
 * This file demonstrates all available UI components with various configurations.
 * Use this as a reference for component usage and styling.
 */

import React from 'react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  IconButton,
  Badge,
  PulseBadge,
  StatCard,
  SimpleStatCard,
  GradientText,
  AnimatedGradientHeading,
  GradientBadge,
  LoadingSpinner,
  LoadingOverlay,
  ButtonSpinner,
  LoadingSkeleton,
  EmptyState,
  SimpleEmptyState,
  NoResultsState,
} from './index'
import {
  Zap,
  Activity,
  Database,
  Clock,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Upload,
  Settings,
} from 'lucide-react'

export function ComponentShowcase() {
  const [showOverlay, setShowOverlay] = React.useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-nvidia-darkGray to-black p-8">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header */}
        <div className="text-center mb-12">
          <AnimatedGradientHeading variant="nvidia">
            UI Component Library
          </AnimatedGradientHeading>
          <p className="text-gray-400 mt-4">
            NVIDIA-themed components with glass morphism and animations
          </p>
        </div>

        {/* Cards */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Basic Card</CardTitle>
                <CardDescription>Standard card without effects</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Glass morphism card with backdrop blur
                </p>
              </CardContent>
            </Card>

            <Card hover>
              <CardHeader>
                <CardTitle>Hover Card</CardTitle>
                <CardDescription>Hover to see scale effect</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Scales up and changes border color on hover
                </p>
              </CardContent>
            </Card>

            <Card hover animated>
              <CardHeader>
                <CardTitle gradient>Animated Card</CardTitle>
                <CardDescription>With gradient title</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Framer Motion powered animations
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Buttons */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Buttons</h2>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="link">Link</Button>

            <Button variant="primary" size="sm">Small</Button>
            <Button variant="primary" size="lg">Large</Button>

            <IconButton icon={<Settings />} variant="primary" />

            <Button disabled>
              <ButtonSpinner className="mr-2" />
              Loading
            </Button>
          </div>
        </section>

        {/* Badges */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Badges</h2>
          <div className="flex flex-wrap gap-3">
            <Badge variant="success">Success</Badge>
            <Badge variant="warning">Warning</Badge>
            <Badge variant="error">Error</Badge>
            <Badge variant="info">Info</Badge>
            <Badge variant="nvidia">NVIDIA</Badge>
            <Badge variant="purple">Purple</Badge>
            <Badge variant="default">Default</Badge>

            <PulseBadge variant="success" pulse>Live</PulseBadge>
            <PulseBadge variant="nvidia" pulse>Active</PulseBadge>

            <Badge icon={<CheckCircle className="w-3 h-3" />} variant="success">
              Complete
            </Badge>
          </div>
        </section>

        {/* Stat Cards */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Stat Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              icon={Zap}
              label="Throughput"
              value="1,234.56"
              unit="req/s"
              trend={{ value: 12.5, direction: "up" }}
              color="green"
            />
            <StatCard
              icon={Activity}
              label="Token Rate"
              value="5,678"
              unit="tok/s"
              trend={{ value: 8.3, direction: "down" }}
              color="blue"
            />
            <StatCard
              icon={Clock}
              label="Latency"
              value="45"
              unit="ms"
              trend={{ value: 2.1, direction: "neutral" }}
              color="purple"
            />
            <StatCard
              icon={Database}
              label="Data Processed"
              value="2.4"
              unit="TB"
              color="orange"
            />
          </div>
        </section>

        {/* Gradient Text */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Gradient Text</h2>
          <div className="space-y-4">
            <GradientText variant="nvidia" size="3xl">
              NVIDIA Performance Dashboard
            </GradientText>
            <GradientText variant="blue" size="2xl">
              Blue Gradient Heading
            </GradientText>
            <GradientText variant="purple" size="xl" animated>
              Animated Purple Gradient
            </GradientText>

            <div className="flex gap-3">
              <GradientBadge variant="nvidia">New</GradientBadge>
              <GradientBadge variant="blue">Beta</GradientBadge>
              <GradientBadge variant="purple">Pro</GradientBadge>
            </div>
          </div>
        </section>

        {/* Loading Spinners */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Loading Spinners</h2>
          <Card>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                <div className="flex flex-col items-center gap-3">
                  <LoadingSpinner variant="spinner" size="md" />
                  <p className="text-sm text-gray-400">Spinner</p>
                </div>
                <div className="flex flex-col items-center gap-3">
                  <LoadingSpinner variant="nvidia" size="md" />
                  <p className="text-sm text-gray-400">NVIDIA</p>
                </div>
                <div className="flex flex-col items-center gap-3">
                  <LoadingSpinner variant="pulse" size="md" />
                  <p className="text-sm text-gray-400">Pulse</p>
                </div>
                <div className="flex flex-col items-center gap-3">
                  <LoadingSpinner variant="dots" size="md" />
                  <p className="text-sm text-gray-400">Dots</p>
                </div>
              </div>

              <div className="mt-8">
                <Button onClick={() => setShowOverlay(true)}>
                  Show Loading Overlay
                </Button>
              </div>

              <div className="mt-8 space-y-2">
                <LoadingSkeleton className="h-8 w-full" />
                <LoadingSkeleton className="h-8 w-3/4" />
                <LoadingSkeleton className="h-8 w-1/2" />
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Empty States */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Empty States</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardContent>
                <EmptyState
                  icon={Database}
                  title="No Data Available"
                  description="Upload your first benchmark to get started with performance analysis"
                  action={{
                    label: "Upload Now",
                    onClick: () => console.log("Upload clicked"),
                  }}
                  secondaryAction={{
                    label: "Learn More",
                    onClick: () => console.log("Learn more clicked"),
                  }}
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <NoResultsState
                  searchQuery="test query"
                  onClear={() => console.log("Clear filters")}
                />
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Simple Components */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Simple Components</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <SimpleStatCard label="CPU Usage" value="78" unit="%" />
            <SimpleStatCard label="Memory" value="12.4" unit="GB" />
            <SimpleStatCard label="GPU Temp" value="65" unit="°C" />
          </div>
        </section>
      </div>

      {/* Overlay Demo */}
      {showOverlay && (
        <LoadingOverlay
          text="Processing your request..."
          variant="nvidia"
        />
      )}
    </div>
  )
}

export default ComponentShowcase
