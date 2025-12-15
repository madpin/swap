# 🚀 S.W.A.P. Railway Deployment Guide

## Quick Deploy to Railway

### 1. Prerequisites
- Railway account ([railway.app](https://railway.app))
- Google Service Account JSON file with Calendar and Sheets API access
- Admin password for the web interface

### 2. Deploy Steps

1. **Create a new Railway project:**
   ```bash
   railway login
   railway init
   ```

2. **Link your repository:**
   - Push this code to GitHub
   - Or use Railway CLI to deploy directly

3. **Set Environment Variables in Railway Dashboard:**

   Required variables:
   
   - `ADMIN_PASSWORD`: Your secure password to access the web interface
     ```
     Example: my_super_secure_password_123
     ```
   
   - `SERVICE_ACCOUNT_FILE`: Path to service account file (or use SERVICE_ACCOUNT_JSON)
     ```
     /app/service-account.json
     ```
   
   - `SERVICE_ACCOUNT_JSON`: (Alternative) Paste entire JSON content here
     ```json
     {
       "type": "service_account",
       "project_id": "your-project",
       ...
     }
     ```
   
   Optional variables:
   
   - `SECRET_KEY`: Flask secret key (auto-generated if not set)
     ```
     your_random_secret_key_here
     ```

4. **Handle Service Account Credentials:**

   **Option A: Use SERVICE_ACCOUNT_JSON env var (Recommended for Railway)**
   - Copy your entire `service-account.json` content
   - Paste it as the value for `SERVICE_ACCOUNT_JSON` env var
   - The app will create the file at runtime

   **Option B: Upload file via Railway volumes**
   - Create a volume in Railway
   - Mount it to `/app`
   - Upload your `service-account.json` file
   - Set `SERVICE_ACCOUNT_FILE=/app/service-account.json`

### 3. Access Your App

Once deployed, Railway will provide you with a URL like:
```
https://your-app-name.railway.app
```

1. Open the URL in your browser
2. Login with your `ADMIN_PASSWORD`
3. Use the dashboard to:
   - ▶️ **Play**: Start the automatic scheduler (runs every hour)
   - ⏸️ **Pause**: Stop the automatic scheduler
   - 🔄 **Sync Now**: Run a sync immediately

### 4. How It Works

- **Scheduler**: When running, syncs your calendar automatically every hour at :00
- **Manual Sync**: Click "Sync Now" to run a sync immediately
- **Status Display**: Shows last sync time, status, and any error messages
- **Auto-refresh**: Dashboard refreshes every 30 seconds

### 5. Monitoring

Check Railway logs to monitor sync operations:
```bash
railway logs
```

### 6. Troubleshooting

**Login Issues:**
- Verify `ADMIN_PASSWORD` is set correctly in Railway dashboard
- Clear browser cookies and try again

**Sync Failures:**
- Check that `SERVICE_ACCOUNT_FILE` or `SERVICE_ACCOUNT_JSON` is set
- Verify Google APIs (Sheets & Calendar) are enabled for your project
- Check service account has proper permissions
- Review Railway logs for detailed error messages

**Scheduler Not Running:**
- The scheduler needs to be manually started after deployment
- Click the "Play" button in the web interface
- Note: Scheduler state does not persist across restarts

### 7. Security Notes

- Always use a strong `ADMIN_PASSWORD`
- Never commit service account credentials to git
- Use Railway's environment variables for sensitive data
- Consider using Railway's private networking features

### 8. Cost Estimate

Railway offers:
- $5/month starter plan (sufficient for this app)
- Free $5 credit for new accounts
- This app uses minimal resources (1 worker, lightweight Flask app)

## Local Development

To run locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ADMIN_PASSWORD="testpassword"
export SERVICE_ACCOUNT_FILE="/path/to/service-account.json"

# Run the web app
python web.py
```

Access at `http://localhost:5000`

## Alternative: Update Service Account Handling

If you prefer to use `SERVICE_ACCOUNT_JSON` env var, update `aio.py` to write the JSON to a file:

```python
import json

def get_service_account_file() -> str:
    """Retrieve the service account file path from environment variables."""
    # Try to get from file path first
    service_account_file = os.environ.get("SERVICE_ACCOUNT_FILE")
    if service_account_file and os.path.exists(service_account_file):
        return service_account_file
    
    # Try to get from JSON env var
    service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")
    if service_account_json:
        # Write to temp file
        import tempfile
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            f.write(service_account_json)
        return path
    
    logger.error("Error: Neither SERVICE_ACCOUNT_FILE nor SERVICE_ACCOUNT_JSON is set.")
    exit(1)
```

---

Built with ❤️ for shift workers everywhere. Happy swapping! 🔄✨

