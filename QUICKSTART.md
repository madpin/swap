# 🚀 S.W.A.P. Quick Start Guide

## What's New? 🎉

Your S.W.A.P. application now has:

✅ **Web Interface** - Beautiful, modern dashboard  
✅ **Play/Pause Controls** - Start and stop the scheduler with one click  
✅ **Auto Scheduler** - Syncs every hour when running  
✅ **Password Protection** - Secured with environment variable  
✅ **Railway Ready** - Deploy to Railway in minutes  
✅ **Status Dashboard** - See last sync time and results  

---

## 🏃 Quick Start Options

### Option 1: Test Locally (Fastest)

```bash
# Set your credentials
export SERVICE_ACCOUNT_FILE='/path/to/service-account.json'
export ADMIN_PASSWORD='testpassword'

# Run the quick start script
./start.sh
```

Open http://localhost:5000 and login with your password!

### Option 2: Deploy to Railway (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add web interface"
   git push
   ```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "Deploy from GitHub"
   - Select your repo

3. **Set Environment Variables:**
   - `ADMIN_PASSWORD`: Your secure password
   - `SERVICE_ACCOUNT_JSON`: Paste entire JSON content from your service account file

4. **Access & Start:**
   - Open your Railway URL
   - Login with your password
   - Click **▶️ Play** to start the scheduler

📖 See [RAILWAY_SETUP.md](RAILWAY_SETUP.md) for detailed Railway setup instructions.

### Option 3: Docker

```bash
# Build
docker build -t swap .

# Run web interface
docker run -p 5000:5000 \
  -e ADMIN_PASSWORD='your_password' \
  -e SERVICE_ACCOUNT_JSON='{"type":"service_account",...}' \
  swap
```

Access at http://localhost:5000

---

## 🎮 Using the Dashboard

Once you're logged in, you'll see:

### Status Section
- **Green circle ▶️**: Scheduler is running (auto-sync every hour)
- **Red circle ⏸️**: Scheduler is stopped (manual sync only)

### Control Buttons

| Button | Action |
|--------|--------|
| **▶️ Play** | Start automatic hourly sync |
| **⏸️ Pause** | Stop automatic sync |
| **🔄 Sync Now** | Run sync immediately |

### Info Display
- **Last Sync**: When the last sync occurred
- **Status**: Success ✓, Error ✗, or No sync yet
- **Message**: Details about the sync result

---

## 🔐 Security

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ADMIN_PASSWORD` | ✅ Yes | Password to access the web interface |
| `SERVICE_ACCOUNT_FILE` | One of these | Path to service account JSON file |
| `SERVICE_ACCOUNT_JSON` | One of these | Service account JSON content (for Railway) |
| `SECRET_KEY` | Optional | Flask session secret (auto-generated if not set) |

**Important:** 
- Never commit your service account JSON to git
- Use strong passwords for production
- Railway encrypts all environment variables

---

## ⏰ How the Scheduler Works

When **Playing** (▶️):
- Runs sync automatically every hour at :00 minutes
- Continues running until you click **Pause**
- Survives app restarts on Railway

When **Paused** (⏸️):
- No automatic syncs
- You can still run manual syncs with **Sync Now**

**Note:** After Railway deployments, you need to click Play again.

---

## 📊 What Gets Synced

The app syncs from your Google Sheet to Google Calendar:

- **Work shifts** with times → Calendar events with start/end times
- **All-day events** (AL, OFF, TR, etc.) → All-day calendar events
- **Multiple users** → Separate calendars per user
- **Automatic sharing** → Calendars shared with specified emails

Configuration is in `aio.py`:
- Line 29: `SPREADSHEET_ID`
- Lines 32-50: `USERS` array

---

## 🔧 Customization

### Change Sync Frequency

Edit `web.py` line 426:
```python
# Every hour at :00
CronTrigger(minute=0)

# Every 30 minutes
CronTrigger(minute="0,30")

# Every 4 hours
CronTrigger(minute=0, hour="*/4")
```

### Add More Users

Edit `aio.py` lines 32-50, add to `USERS` array:
```python
{
    "CALENDAR_NAME": "New Person's Rota",
    "USER_NAME": "NameInSheet",
    "EMAILS_TO_SHARE": ["email@example.com"],
}
```

### Change Timezone

Default is `Europe/Dublin`. To change:

1. Edit `web.py` line 26:
   ```python
   scheduler = BackgroundScheduler(timezone=pytz.timezone("Your/Timezone"))
   ```

2. Edit `aio.py` sync timezone in lines 576, 617, 652:
   ```python
   timezone="Your/Timezone"
   ```

---

## 🐛 Troubleshooting

### Can't login
- Check `ADMIN_PASSWORD` is set correctly
- Clear browser cookies

### Sync fails
- Verify service account JSON is valid
- Check Google Sheets & Calendar APIs are enabled
- Ensure service account has access to the spreadsheet
- View detailed errors in Railway logs or terminal output

### Scheduler not starting
- Check Railway logs for errors
- Ensure no Python syntax errors
- Try manual sync first to verify credentials work

### Events not appearing
- Verify the `SPREADSHEET_ID` is correct
- Check the `USER_NAME` matches exactly what's in the sheet
- Ensure calendar sharing emails are correct

---

## 📁 Project Files

```
swap/
├── aio.py                 # Core sync logic
├── web.py                 # Flask web interface
├── requirements.txt       # Python dependencies
├── start.sh              # Local quick start script
├── Procfile              # Railway/Heroku deployment
├── railway.json          # Railway configuration
├── runtime.txt           # Python version
├── dockerfile            # Docker container
├── .dockerignore         # Docker ignore patterns
├── README.md             # Project overview
├── DEPLOYMENT.md         # Detailed deployment guide
├── RAILWAY_SETUP.md      # Railway-specific setup
└── QUICKSTART.md         # This file!
```

---

## 💡 Tips

1. **Start Local First**: Test everything locally before deploying to Railway
2. **Check Logs**: Railway logs show detailed sync progress and errors
3. **Test Manual Sync**: Before starting the scheduler, test with "Sync Now"
4. **Monitor First Run**: Watch the dashboard during the first sync to catch any issues
5. **Service Account**: Share your spreadsheet with the service account email address

---

## 🆘 Need Help?

1. **Local Testing**: Run `./start.sh` and check terminal output
2. **Railway Logs**: View in Railway dashboard → Deployments → Logs
3. **Manual Sync**: Test with command line: `python aio.py`
4. **Google APIs**: Check [Google Cloud Console](https://console.cloud.google.com/) for API quotas

---

## 🎯 Next Steps

1. ✅ Set up your environment variables
2. ✅ Test locally with `./start.sh`
3. ✅ Deploy to Railway
4. ✅ Login to your dashboard
5. ✅ Click **▶️ Play** to start the scheduler
6. ✅ Verify events appear in Google Calendar

**You're all set!** 🎉

Built with ❤️ for shift workers everywhere. Happy swapping! 🔄✨

