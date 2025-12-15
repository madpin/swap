# 🚂 Railway Quick Setup Guide

## Step-by-Step Deployment

### 1. Push to GitHub (if not already done)

```bash
git add .
git commit -m "Add web interface with scheduler"
git push origin main
```

### 2. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `swap` repository

### 3. Configure Environment Variables

In Railway dashboard, go to **Variables** and add:

#### Required Variables:

**ADMIN_PASSWORD**
```
your_secure_password_here
```
This is the password you'll use to login to the web interface.

**SERVICE_ACCOUNT_JSON**
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/...",
  "universe_domain": "googleapis.com"
}
```
⚠️ **Important**: Copy your ENTIRE `service-account.json` file content and paste it as-is. Include all braces, quotes, and newlines.

#### Optional Variables:

**SECRET_KEY** (recommended for production)
```
generate_a_random_string_here_32_chars_plus
```
Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

### 4. Deploy

Railway will automatically deploy after you add the variables. Watch the deployment logs to ensure everything starts correctly.

### 5. Access Your App

1. Railway will provide a URL like: `https://swap-production.up.railway.app`
2. Click the URL to open your app
3. Login with your `ADMIN_PASSWORD`
4. Click **▶️ Play** to start the scheduler

### 6. Verify It's Working

After clicking Play:
- Click **🔄 Sync Now** to test immediately
- Check the sync status on the dashboard
- Verify events appear in your Google Calendar

## Troubleshooting

### "Invalid password" on login
- Double-check `ADMIN_PASSWORD` in Railway variables
- Ensure there are no extra spaces before/after the password

### "SERVICE_ACCOUNT_FILE environment variable is not set"
- Verify `SERVICE_ACCOUNT_JSON` contains valid JSON
- Make sure you copied the ENTIRE JSON content including outer braces
- Check for any special characters that might have been corrupted

### Sync fails with Google API errors
- Verify your service account has these APIs enabled:
  - Google Sheets API
  - Google Calendar API
- Check service account has access to the spreadsheet (share it with the service account email)
- Verify the spreadsheet ID in `aio.py` matches your spreadsheet

### Scheduler keeps stopping after deploy
- The scheduler state doesn't persist across deployments
- After each deployment, click **Play** again to restart it
- This is normal behavior

## Update Spreadsheet ID

To change which spreadsheet to sync:

1. Edit `aio.py` line 29:
   ```python
   SPREADSHEET_ID = "your-new-spreadsheet-id-here"
   ```

2. Commit and push:
   ```bash
   git add aio.py
   git commit -m "Update spreadsheet ID"
   git push
   ```

3. Railway will auto-deploy the changes

## Update Users/Calendars

Edit the `USERS` array in `aio.py` (lines 32-50) to add/remove calendars:

```python
USERS = [
    {
        "CALENDAR_NAME": "Your Calendar Name",
        "USER_NAME": "NameInSpreadsheet",
        "EMAILS_TO_SHARE": [
            "email1@example.com",
            "email2@example.com",
        ],
    },
]
```

## Cost

- Railway: ~$5/month (includes $5 free credit for new users)
- This app is very lightweight and stays within the starter plan limits

## Support

If you run into issues:
1. Check Railway deployment logs
2. Verify all environment variables are set correctly
3. Test locally first with `./start.sh`
4. Check Google API quotas in Google Cloud Console

---

Built with ❤️ for Rachel and shift workers everywhere! 🔄✨

