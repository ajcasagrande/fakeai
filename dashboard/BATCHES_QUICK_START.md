# Batch Processing Dashboard - Quick Start Guide

## Setup (5 minutes)

### 1. Environment Configuration
```bash
cd /home/anthony/projects/fakeai/dashboard

# Copy environment template
cp .env.example .env

# Edit .env with your API details
nano .env
```

Required environment variables:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=your-api-key-here
```

### 2. Install Dependencies (if not already done)
```bash
npm install
```

### 3. Start Development Server
```bash
npm run dev
```

Dashboard will be available at: **http://localhost:5173**

## Access the Batches Dashboard

Navigate to: **http://localhost:5173/batches**

## Quick Navigation

### Main Pages
- **Active Batches**: `/batches` - Monitor running batch jobs
- **Create Batch**: `/batches/create` - Upload and start new batch
- **History**: `/batches/history` - View all batches with analytics
- **Batch Details**: `/batches/{batch_id}` - Individual batch view

## Creating Your First Batch

### Step 1: Prepare JSONL File
Create a file named `batch-requests.jsonl`:
```jsonl
{"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello!"}]}}
{"custom_id": "req-2", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "How are you?"}]}}
```

### Step 2: Upload via Dashboard
1. Navigate to `/batches/create`
2. Click "Select File" or drag-and-drop your JSONL file
3. Select endpoint: `/v1/chat/completions`
4. (Optional) Add description: "My first batch"
5. (Optional) Add tags: "test, demo"
6. Click "Create Batch"

### Step 3: Monitor Progress
- Automatically redirected to batch details page
- Status updates every 3 seconds
- Watch progress bar as requests complete

### Step 4: Download Results
- Wait for status to change to "completed"
- Click "Download Results" button
- Results saved as `batch-{id}-output.jsonl`

## Key Features Overview

### Real-time Monitoring
- Auto-refresh every 5 seconds for active batches
- Status indicators with pulse animation
- Progress bars showing completion percentage

### Batch Management
- Create new batches with file upload
- Cancel running batches
- Download results and error files
- View detailed statistics

### Analytics
- Success/failure rate charts
- Processing time analytics
- Cost tracking ($0.001 per request)
- Status distribution

### Filtering & Search
- Search by ID, description, or tags
- Filter by status (multiple selection)
- Filter by endpoint
- Clear filters button

## Batch Statuses

| Status | Description | Actions Available |
|--------|-------------|-------------------|
| **Validating** | File being validated | Cancel |
| **In Progress** | Requests processing | Cancel, View Details |
| **Completed** | All requests finished | Download Results |
| **Failed** | Errors encountered | Download Errors |
| **Cancelled** | User-cancelled | View Details |

## Common Tasks

### View Active Batches
```
Navigate to /batches
```
- See all running batches
- Quick stats (total, completed, failed)
- Cancel button for each batch

### Check Batch Details
```
Click on any batch OR navigate to /batches/{batch_id}
```
- Full batch information
- Request breakdown
- Processing timeline
- Download results

### View History & Analytics
```
Navigate to /batches/history
```
- All batches (past and present)
- Filter and search
- Analytics charts
- Success rates

### Cancel a Batch
```
From BatchList or BatchDetails:
1. Click "Cancel" button
2. Confirm in dialog
3. Status updates to "Cancelling" then "Cancelled"
```

### Download Results
```
From BatchDetails page:
1. Wait for "Completed" status
2. Click "Download Results"
3. File saves automatically
```

## Troubleshooting

### Dashboard won't start
```bash
# Check if dependencies are installed
npm install

# Clear cache and restart
rm -rf node_modules
npm install
npm run dev
```

### API connection errors
- Verify `REACT_APP_API_URL` in `.env`
- Check API server is running
- Verify `REACT_APP_API_KEY` is correct

### File upload fails
- Ensure file is in JSONL format (one JSON per line)
- Check file extension is `.jsonl`
- Verify each line is valid JSON

### Batches not updating
- Check browser console for errors
- Verify API endpoints are responding
- Refresh page manually

## File Locations

All batch-related files are in:
```
/home/anthony/projects/fakeai/dashboard/src/pages/Batches/
```

Key files:
- `index.tsx` - Main routing
- `BatchList.tsx` - Active batches page
- `CreateBatch.tsx` - Create batch form
- `BatchDetails.tsx` - Batch details page
- `BatchHistory.tsx` - History and analytics

Components:
```
/home/anthony/projects/fakeai/dashboard/src/components/
├── BatchStatusBadge.tsx
├── BatchProgressBar.tsx
└── BatchCharts.tsx
```

## API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/v1/batches` | List all batches |
| POST | `/v1/batches` | Create new batch |
| GET | `/v1/batches/{id}` | Get batch details |
| POST | `/v1/batches/{id}/cancel` | Cancel batch |
| POST | `/v1/files` | Upload batch file |
| GET | `/v1/files/{id}/content` | Download results |

## Performance Tips

1. **Auto-refresh**: Automatically pauses when no active batches
2. **Manual refresh**: Use refresh button in BatchDetails
3. **Filter early**: Use filters to reduce displayed data
4. **Clear completed**: Archive old batches to improve load times

## Next Steps

1. Create your first test batch
2. Monitor its progress in real-time
3. Download and review results
4. Explore the analytics in History page
5. Try filtering and searching
6. Review the full documentation in README.md

## Support

For issues or questions:
- Check `/dashboard/src/pages/Batches/README.md` for detailed docs
- Review `/dashboard/BATCHES_DASHBOARD_SUMMARY.md` for complete overview
- Inspect browser console for error messages

---

**Happy Batch Processing!**
