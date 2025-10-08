# Quick Start Guide - Fine-Tuning Dashboard

This guide will help you get the Fine-Tuning Management Dashboard up and running in minutes.

## Prerequisites

- Node.js 18+ and npm
- FakeAI API server running on `http://localhost:8000`

## Quick Start

### 1. Install Dependencies

```bash
cd dashboard
npm install
```

This will install all required packages including:
- React 18.2
- TypeScript 5.2
- Vite 5.0
- Recharts 2.10 (for charts)
- Tailwind CSS 3.4 (for styling)
- Axios 1.6 (for API calls)

### 2. Start Development Server

```bash
npm run dev
```

The dashboard will start on http://localhost:3000

### 3. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:3000/fine-tuning
```

## Testing the Dashboard

### Create a Test Fine-Tuning Job

1. Click "Create Fine-Tuning Job" button
2. Fill in the form:
   - **Base Model**: Select a model (e.g., Llama 3.1 8B Instruct)
   - **Training File ID**: Enter a file ID (e.g., `file-abc123`)
   - **Validation File ID**: (Optional) Enter validation file ID
   - **Hyperparameters**: Leave as "auto" or customize
   - **Model Suffix**: (Optional) Add a custom suffix
3. Click "Create Fine-Tuning Job"

### Watch the Job Progress

The job will automatically progress through stages:
1. **Validating Files** (1 second)
2. **Queued** (1 second)
3. **Running** (30 seconds with real-time metrics)
4. **Succeeded** (final state)

You'll see:
- Status timeline updating in real-time
- Training progress bar
- Loss curves being plotted
- Checkpoints being created at 25%, 50%, 75%, 100%
- Events log streaming
- Cost tracking updates

## Dashboard Features

### Main View
- **Jobs List (Left Panel)**: All fine-tuning jobs with status indicators
- **Job Details (Right Panel)**: Detailed view of selected job

### Job Details View
1. **Status Timeline**: Visual progression through job stages
2. **Hyperparameters**: Training configuration display
3. **Cost Tracker**: Token usage and cost estimation
4. **Training Progress**: Loss curves and accuracy charts
5. **Checkpoint Manager**: Saved model checkpoints
6. **Events Log**: Chronological event stream

### Controls
- **Auto-refresh Toggle**: Enable/disable automatic updates (default: ON)
- **Manual Refresh**: Click refresh button to update immediately
- **Search Bar**: Filter jobs by ID, model, or status
- **Cancel Job**: Stop running jobs (confirmation required)

## API Endpoints Used

The dashboard connects to these FakeAI API endpoints:

```
POST   /v1/fine_tuning/jobs              - Create job
GET    /v1/fine_tuning/jobs              - List jobs
GET    /v1/fine_tuning/jobs/{job_id}     - Get job details
POST   /v1/fine_tuning/jobs/{job_id}/cancel - Cancel job
GET    /v1/fine_tuning/jobs/{job_id}/events - Stream events
GET    /v1/fine_tuning/jobs/{job_id}/checkpoints - Get checkpoints
```

## Keyboard Shortcuts

- **Ctrl+F / Cmd+F**: Focus search bar
- **Esc**: Close dialogs

## Customization

### Change API URL

Edit `src/api/client.ts`:

```typescript
constructor(baseURL: string = '/v1') {
  // Change to your API URL
  this.client = axios.create({
    baseURL: 'http://your-api-server:8000/v1',
    // ...
  });
}
```

### Adjust Refresh Rate

Edit `src/pages/FineTuning/index.tsx`:

```typescript
const interval = setInterval(fetchJobs, 3000); // Change 3000 to desired ms
```

### Customize Theme Colors

Edit `tailwind.config.js`:

```javascript
nvidia: {
  green: '#76b900', // Change to your brand color
  // ...
}
```

## Building for Production

```bash
# Type check
npm run type-check

# Build
npm run build
```

Build output will be in `../static/spa/` directory.

## Troubleshooting

### Dashboard won't start
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

### API requests failing
- Ensure FakeAI server is running on port 8000
- Check browser console for CORS errors
- Verify API endpoints are accessible

### Charts not rendering
- Check browser console for errors
- Ensure Recharts is installed: `npm list recharts`

### Jobs not updating
- Check auto-refresh is enabled (toggle in top-right)
- Verify API is returning data correctly
- Check browser network tab for failed requests

## Next Steps

- Explore all dashboard features
- Create multiple jobs and compare performance
- Customize the theme to match your brand
- Integrate with your CI/CD pipeline

## Support

For issues or questions:
- Check the main README.md
- Review component source code in `src/components/FineTuning/`
- Examine API client in `src/api/client.ts`

## Performance Tips

- Auto-refresh uses 3-second intervals; adjust if needed
- Limit displayed jobs if you have thousands (use pagination)
- Events log auto-scrolls; filter by level to reduce clutter
- Checkpoints are loaded on-demand per job

Happy fine-tuning! 🚀
