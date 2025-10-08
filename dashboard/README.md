# FakeAI Fine-Tuning Management Dashboard

A comprehensive, production-ready React TypeScript dashboard for managing fine-tuning jobs with beautiful NVIDIA-themed visualizations.

## Features

### 1. Active Fine-Tuning Jobs List
- Real-time job listing with auto-refresh
- Status indicators with color-coded badges
- Search and filter functionality
- Job selection for detailed view

### 2. Job Status Timeline
- Visual timeline showing job progression
- States: validating_files → queued → running → succeeded/failed/cancelled
- Duration tracking and estimates
- Created/finished timestamps

### 3. Create New Fine-Tuning Job UI
- Form-based job creation
- Model selection (Llama, Mistral, GPT-OSS)
- Hyperparameter configuration
- File ID input for training/validation data
- Custom model suffix support

### 4. Training Progress with Loss Curves
- Beautiful Recharts visualizations
- Training and validation loss curves
- Training accuracy tracking
- Real-time metrics updates
- Progress bar with percentage

### 5. Hyperparameters Display
- Clean display of training parameters
- Epochs, batch size, learning rate
- Support for 'auto' configuration

### 6. Checkpoint Management
- List of saved checkpoints
- Step-by-step metrics tracking
- Download functionality
- Checkpoint comparison

### 7. Model Comparison (Before/After)
- Compare initial vs final checkpoints
- Percentage improvement tracking
- Metric-by-metric comparison
- Visual indicators for improvements

### 8. Cost Tracking Per Job
- Token usage tracking
- Real-time cost estimation
- Rate display ($0.008/1K tokens)
- Formatted cost display

### 9. Events Log Viewer
- Filterable event stream (all/info/warning/error)
- Chronological event listing
- Detailed event data display
- Color-coded severity levels

### 10. Cancel Job Functionality
- Cancel running/queued jobs
- Confirmation dialog
- Status update on cancellation

## Technology Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom NVIDIA theme
- **Charts**: Recharts
- **Icons**: Lucide React
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Date Formatting**: date-fns

## Project Structure

```
dashboard/
├── src/
│   ├── api/
│   │   └── client.ts              # API client for /v1/fine_tuning endpoints
│   ├── types/
│   │   └── fine-tuning.ts         # TypeScript type definitions
│   ├── utils/
│   │   └── format.ts              # Formatting utilities
│   ├── components/
│   │   └── FineTuning/
│   │       ├── JobsList.tsx               # Jobs list component
│   │       ├── JobDetails.tsx             # Main details view
│   │       ├── JobStatusTimeline.tsx      # Status progression
│   │       ├── TrainingProgress.tsx       # Loss curves & metrics
│   │       ├── HyperparametersDisplay.tsx # Hyperparams display
│   │       ├── CheckpointManager.tsx      # Checkpoint management
│   │       ├── ModelComparison.tsx        # Before/after comparison
│   │       ├── CostTracker.tsx            # Cost tracking
│   │       ├── EventsLogViewer.tsx        # Events log
│   │       └── CreateJobDialog.tsx        # Job creation form
│   ├── pages/
│   │   └── FineTuning/
│   │       └── index.tsx          # Main dashboard page
│   ├── styles/
│   │   └── globals.css            # Global styles & NVIDIA theme
│   ├── App.tsx                    # App component with routing
│   └── main.tsx                   # Entry point
├── public/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## Installation

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install
```

## Development

```bash
# Start development server on port 3000
npm run dev

# The dashboard will be available at http://localhost:3000
# API requests are proxied to http://localhost:8000
```

## Building for Production

```bash
# Type check
npm run type-check

# Build for production
npm run build

# Output will be in ../static/spa/
```

## API Integration

The dashboard integrates with the FakeAI API using the following endpoints:

- `POST /v1/fine_tuning/jobs` - Create new job
- `GET /v1/fine_tuning/jobs` - List jobs
- `GET /v1/fine_tuning/jobs/{job_id}` - Get job details
- `POST /v1/fine_tuning/jobs/{job_id}/cancel` - Cancel job
- `GET /v1/fine_tuning/jobs/{job_id}/events` - Get job events
- `GET /v1/fine_tuning/jobs/{job_id}/checkpoints` - Get checkpoints

## NVIDIA Theme

The dashboard features a beautiful NVIDIA-themed dark design:

- **Primary Color**: NVIDIA Green (#76b900)
- **Background**: Dark gray tones (#0a0a0a, #1a1a1a, #2a2a2a)
- **Typography**: Inter font family
- **Visual Effects**: Glow effects, smooth transitions, gradient backgrounds

## Features Showcase

### Auto-Refresh
Jobs automatically refresh every 3 seconds when auto-refresh is enabled. Toggle it on/off as needed.

### Search
Quickly find jobs by ID, model name, or status using the search bar.

### Real-time Updates
Progress bars, metrics, and events update in real-time as jobs progress.

### Responsive Design
The dashboard is fully responsive and works on all screen sizes.

## Configuration

### API Base URL
Modify the base URL in `src/api/client.ts` if your API is hosted elsewhere:

```typescript
constructor(baseURL: string = '/v1') {
  // Change default if needed
}
```

### Refresh Interval
Adjust auto-refresh intervals in `src/pages/FineTuning/index.tsx`:

```typescript
const interval = setInterval(fetchJobs, 3000); // 3 seconds
```

## License

Apache-2.0
