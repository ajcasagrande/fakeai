# Fine-Tuning Dashboard Architecture

## Overview

A production-ready React TypeScript dashboard for managing fine-tuning jobs with real-time updates, beautiful visualizations, and comprehensive monitoring capabilities.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FakeAI Dashboard                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────┐          ┌──────────────────────┐      │
│  │  Main Page     │          │   API Client         │      │
│  │  index.tsx     │◄────────►│   client.ts          │      │
│  └────────────────┘          └──────────────────────┘      │
│         │                              │                     │
│         │                              │                     │
│         ▼                              ▼                     │
│  ┌────────────────────────────────────────────────┐         │
│  │          Component Layer                        │         │
│  ├────────────────────────────────────────────────┤         │
│  │  • JobsList                                    │         │
│  │  • JobDetails                                  │         │
│  │  • JobStatusTimeline                           │         │
│  │  • TrainingProgress (with Recharts)            │         │
│  │  • HyperparametersDisplay                      │         │
│  │  • CheckpointManager                           │         │
│  │  • ModelComparison                             │         │
│  │  • CostTracker                                 │         │
│  │  • EventsLogViewer                             │         │
│  │  • CreateJobDialog                             │         │
│  └────────────────────────────────────────────────┘         │
│         │                                                    │
│         ▼                                                    │
│  ┌────────────────────────────────────────────────┐         │
│  │         Utilities & Types                       │         │
│  ├────────────────────────────────────────────────┤         │
│  │  • TypeScript Types (fine-tuning.ts)           │         │
│  │  • Format Utils (format.ts)                    │         │
│  │  • NVIDIA Theme (globals.css)                  │         │
│  └────────────────────────────────────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │   FakeAI API Server  │
              │   localhost:8000     │
              └──────────────────────┘
```

## Component Hierarchy

```
App.tsx (Router)
└── FineTuningDashboard (Main Page)
    ├── Header Section
    │   ├── Title & Description
    │   ├── Controls (Auto-refresh, Refresh, Create)
    │   └── Search & Stats
    │
    ├── Left Panel: JobsList
    │   └── Job Items (with status, model, metadata)
    │
    └── Right Panel: JobDetails (if job selected)
        ├── Job Header (ID, Model, Cancel Button)
        ├── Error Display (if failed)
        ├── JobStatusTimeline
        ├── Grid Row 1
        │   ├── HyperparametersDisplay
        │   └── CostTracker
        ├── TrainingProgress (with Loss Curves)
        ├── CheckpointManager
        └── EventsLogViewer
```

## Data Flow

### 1. Job Listing Flow
```
User loads dashboard
    → FineTuningDashboard.fetchJobs()
        → fineTuningAPI.listJobs()
            → GET /v1/fine_tuning/jobs
                → Update jobs state
                    → Render JobsList
                        → Display jobs with status
```

### 2. Job Selection Flow
```
User clicks job in list
    → onSelectJob(job)
        → selectedJob state updated
            → JobDetails component renders
                → Parallel API calls:
                    - fineTuningAPI.getEvents(job.id)
                    - fineTuningAPI.getCheckpoints(job.id)
                        → Update events & checkpoints state
                            → Render all sub-components
```

### 3. Job Creation Flow
```
User clicks "Create Fine-Tuning Job"
    → showCreateDialog = true
        → CreateJobDialog renders
            → User fills form
                → Submit form
                    → fineTuningAPI.createJob(request)
                        → POST /v1/fine_tuning/jobs
                            → Success: onJobCreated()
                                → fetchJobs() (refresh list)
                                    → Close dialog
```

### 4. Real-time Updates
```
Auto-refresh enabled
    → setInterval(fetchJobs, 3000)
        → Every 3 seconds:
            - Fetch job list
            - Update selected job
            - Fetch events/checkpoints for selected job
                → Components re-render with new data
```

## API Integration

### Endpoints Used

| Endpoint | Method | Purpose | Component |
|----------|--------|---------|-----------|
| `/v1/fine_tuning/jobs` | GET | List all jobs | FineTuningDashboard |
| `/v1/fine_tuning/jobs` | POST | Create new job | CreateJobDialog |
| `/v1/fine_tuning/jobs/{id}` | GET | Get job details | JobDetails |
| `/v1/fine_tuning/jobs/{id}/cancel` | POST | Cancel job | JobDetails |
| `/v1/fine_tuning/jobs/{id}/events` | GET | Get job events | JobDetails |
| `/v1/fine_tuning/jobs/{id}/checkpoints` | GET | Get checkpoints | JobDetails |

### Request Flow
```typescript
// Example: Creating a job
const request: FineTuningJobRequest = {
  model: 'meta-llama/Llama-3.1-8B-Instruct',
  training_file: 'file-abc123',
  hyperparameters: {
    n_epochs: 3,
    batch_size: 4,
    learning_rate_multiplier: 0.1
  }
};

await fineTuningAPI.createJob(request);
// → POST /v1/fine_tuning/jobs
// → Returns FineTuningJob object
```

## State Management

### Dashboard State
```typescript
interface DashboardState {
  jobs: FineTuningJob[];              // All jobs
  selectedJob: FineTuningJob | null;  // Currently selected
  loading: boolean;                   // Initial load
  searchQuery: string;                // Filter jobs
  showCreateDialog: boolean;          // Dialog visibility
  autoRefresh: boolean;               // Auto-refresh toggle
}
```

### JobDetails State
```typescript
interface JobDetailsState {
  events: FineTuningEvent[];          // Job events
  checkpoints: FineTuningCheckpoint[]; // Job checkpoints
  cancelling: boolean;                // Cancel in progress
}
```

## Styling Architecture

### Tailwind Configuration
```javascript
// Custom NVIDIA theme
nvidia: {
  green: '#76b900',      // Primary brand color
  'green-dark': '#669900',
  'green-light': '#8acc00',
  gray: {
    900: '#0a0a0a',      // Darkest background
    800: '#1a1a1a',      // Cards
    700: '#2a2a2a',      // Nested elements
    600: '#3a3a3a',      // Borders
  }
}
```

### CSS Custom Properties
```css
:root {
  --nvidia-green: #76B900;
  --bg-primary: #000000;
  --surface-base: #1A1A1A;
  --text-primary: #FFFFFF;
  /* ... more variables */
}
```

## Performance Optimizations

1. **Memoization**: useMemo for expensive computations (metrics data)
2. **Interval Management**: Cleanup intervals on unmount
3. **Conditional Rendering**: Only render JobDetails when job selected
4. **Throttled API Calls**: 3-second interval prevents overwhelming server
5. **Lazy Loading**: Components loaded on-demand

## Type Safety

Full TypeScript coverage:
- API request/response types
- Component prop types
- Event handler types
- State types

Example:
```typescript
interface JobsListProps {
  jobs: FineTuningJob[];
  selectedJob: FineTuningJob | null;
  onSelectJob: (job: FineTuningJob) => void;
  loading: boolean;
}
```

## Visualization Details

### Recharts Configuration
```typescript
<LineChart data={metricsData}>
  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
  <XAxis dataKey="step" stroke="#666666" />
  <YAxis stroke="#666666" />
  <Tooltip contentStyle={{ backgroundColor: '#1a1a1a' }} />
  <Line type="monotone" dataKey="train_loss" stroke="#76b900" />
</LineChart>
```

### Charts Provided
1. **Training Loss Curve**: Solid line, NVIDIA green
2. **Validation Loss Curve**: Dashed line, lighter green
3. **Training Accuracy**: Area chart showing improvement

## Error Handling

### API Errors
```typescript
try {
  await fineTuningAPI.createJob(request);
} catch (error) {
  setError(error.response?.data?.message || 'Failed to create job');
}
```

### Job Errors
Display error banner in JobDetails when `job.error` exists:
```typescript
{job.error && (
  <ErrorBanner
    code={job.error.code}
    message={job.error.message}
    param={job.error.param}
  />
)}
```

## Build Configuration

### Development
- Vite dev server on port 3000
- Hot module replacement (HMR)
- Proxy to API server on port 8000

### Production
- TypeScript compilation check
- Vite build with minification
- Output to `../static/spa/`
- Code splitting for vendors

## Security Considerations

1. **No Secrets**: All API keys handled server-side
2. **CORS**: Configured via API server
3. **Input Validation**: Form validation before submission
4. **XSS Protection**: React's built-in escaping

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast ratios meet WCAG AA

## Future Enhancements

1. **WebSocket Support**: Real-time SSE streaming
2. **Export Functionality**: Download metrics as CSV
3. **Comparison View**: Side-by-side job comparison
4. **Advanced Filters**: Filter by date range, status, model
5. **Notifications**: Browser notifications for job completion
6. **Dark/Light Mode**: Theme switching (currently dark only)
7. **Multi-language**: i18n support

## Testing Strategy

Recommended testing approach:
1. **Unit Tests**: Component logic with Jest
2. **Integration Tests**: API client with MSW
3. **E2E Tests**: User flows with Playwright
4. **Visual Tests**: Chromatic for visual regression

## Deployment

### Static Hosting
```bash
npm run build
# Deploy ../static/spa/ to:
# - AWS S3 + CloudFront
# - Vercel
# - Netlify
# - GitHub Pages
```

### Docker
```dockerfile
FROM node:18 as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

## Monitoring

Recommended metrics to track:
- Page load time
- API response times
- Error rates
- User engagement (jobs created, cancelled)
- Chart rendering performance

---

**Last Updated**: 2025-10-06
**Version**: 1.0.0
**Status**: Production Ready
