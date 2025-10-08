# Embeddings Dashboard - Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
cd /home/anthony/projects/fakeai
npm install react react-dom typescript
npm install --save-dev @types/react @types/react-dom
```

### 2. Configure Environment

Create a `.env` file in your project root:

```bash
REACT_APP_API_BASE_URL=http://localhost:8000
```

### 3. Import the Dashboard

```tsx
import EmbeddingsDashboard from './fakeai/dashboard/src/pages/Embeddings';

function App() {
  return (
    <div className="App">
      <EmbeddingsDashboard />
    </div>
  );
}

export default App;
```

## Running the Dashboard

### Development Mode

```bash
npm start
```

The dashboard will be available at `http://localhost:3000`

### Production Build

```bash
npm run build
npm run serve
```

## API Requirements

Ensure your FakeAI server is running and the following endpoints are accessible:

### Required Endpoints

1. **Embeddings Usage API**
   ```
   GET /v1/organization/usage/embeddings
   ```

2. **Metrics API**
   ```
   GET /metrics
   ```

### Start FakeAI Server

```bash
# From project root
python -m fakeai.app

# Or using uvicorn
uvicorn fakeai.app:app --reload --host 0.0.0.0 --port 8000
```

## First Time Usage

### 1. Access the Dashboard
Navigate to `http://localhost:3000` in your browser

### 2. Select Time Range
Use the dropdown to select your desired time range:
- Last Hour
- Last 6 Hours
- **Last 24 Hours** (default)
- Last 7 Days
- Last 30 Days

### 3. Filter by Model (Optional)
Select a specific embedding model or view all:
- All Models (default)
- text-embedding-ada-002
- text-embedding-3-small
- text-embedding-3-large

### 4. Enable Auto-Refresh
Check the "Auto-refresh" checkbox to update data every 5 seconds automatically

## Dashboard Sections

### Key Metrics (Top)
Six stat cards showing:
- Total Requests
- Total Tokens
- Avg Processing Time
- Requests/Second
- Tokens/Second
- Error Rate

### Charts (Middle)
- **Usage Trends**: Dual-axis line chart
- **Token Consumption**: Area chart
- **Model Usage**: Bar chart
- **Dimension Distribution**: Pie chart

### Tables (Bottom)
- **Cost Analysis**: Cost breakdown by model
- **Recent Embeddings**: Latest requests with details

## Common Tasks

### Export Data

Click one of the export buttons:
- **Export JSON**: Full data export
- **Export CSV**: Spreadsheet-compatible format

The file will download automatically.

### Manual Refresh

Click the **"Refresh Now"** button to fetch latest data immediately.

### View Specific Model

Select a model from the Model dropdown to filter all visualizations.

### Change Time Range

Select a different time range from the dropdown - all charts update automatically.

## Troubleshooting

### Dashboard Shows No Data

**Check:**
1. FakeAI server is running: `curl http://localhost:8000/health`
2. API endpoints are accessible: `curl http://localhost:8000/metrics`
3. You have created some embeddings (generate test data if needed)

**Fix:**
```bash
# Generate test embedding
curl -X POST http://localhost:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-ada-002",
    "input": "Test embedding for dashboard"
  }'
```

### CORS Errors

**Check:** Browser console for CORS errors

**Fix:** Configure CORS in FakeAI server:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Charts Not Rendering

**Check:** Browser console for canvas errors

**Fix:** Ensure canvas is supported:
- Update your browser to latest version
- Enable hardware acceleration

### Slow Performance

**Check:** Network tab for slow API calls

**Fix:**
- Increase API server resources
- Reduce auto-refresh interval
- Use shorter time ranges

## Generate Test Data

### Python Script

```python
import requests
import time

API_BASE = "http://localhost:8000"

# Generate 100 test embeddings
for i in range(100):
    response = requests.post(
        f"{API_BASE}/v1/embeddings",
        json={
            "model": "text-embedding-ada-002",
            "input": f"Test embedding {i}",
            "dimensions": 1536
        }
    )
    print(f"Created embedding {i+1}/100")
    time.sleep(0.1)

print("Test data generation complete!")
```

### Bash Script

```bash
#!/bin/bash

for i in {1..100}; do
  curl -X POST http://localhost:8000/v1/embeddings \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"text-embedding-ada-002\",
      \"input\": \"Test embedding $i\"
    }"
  echo "Created embedding $i/100"
  sleep 0.1
done

echo "Test data generation complete!"
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `R` | Refresh data |
| `E` | Export JSON |
| `C` | Export CSV |
| `A` | Toggle auto-refresh |
| `1-5` | Select time range (1=1h, 2=6h, 3=24h, 4=7d, 5=30d) |

## Mobile Usage

The dashboard is fully responsive:
- Vertical layout on mobile
- Touch-friendly controls
- Swipeable tables
- Optimized chart sizes

## Browser Recommendations

For best experience:
- **Chrome**: ✅ Recommended
- **Firefox**: ✅ Recommended
- **Safari**: ✅ Supported
- **Edge**: ✅ Supported

## Performance Tips

1. **Use appropriate time ranges**: Shorter ranges = faster loading
2. **Filter by model**: Reduces data volume
3. **Disable auto-refresh**: When doing analysis
4. **Close unused tabs**: Free up memory
5. **Use latest browser**: Better canvas performance

## Next Steps

1. ✅ Set up the dashboard (you're here!)
2. Generate test data
3. Explore different time ranges
4. Try model filtering
5. Export some data
6. Integrate with your workflow

## Support & Documentation

- **Full Documentation**: See `README.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **API Reference**: Check FakeAI API documentation
- **Component Details**: Review individual component source files

## Questions?

Common questions answered in `README.md`:
- How to customize colors?
- How to add new metrics?
- How to integrate with other tools?
- How to deploy to production?

---

**Ready to start?** Just run `npm start` and navigate to `http://localhost:3000`!
