# 🗓️ **S.W.A.P. — Shift-Workers Arrangement Platform**

> "_There is no spoon._" – The Matrix  
_(Schedules shouldn't bend you—bend them to your will!)_

S.W.A.P. simplifies life for shift workers by seamlessly syncing work rotas from Google Sheets directly into Google Calendar. Born out of love—to help Rachel manage her scheduling chaos effortlessly—it’s adaptable for anyone stuck dealing with messy, manual schedules.

---

## 🚧 **The Problem**

Shift schedules can quickly turn into chaos:

- 📉 Frustrating manual copying and updating.
- ⏱️ Missed appointments due to scheduling mistakes.
- 🌪️ Endless confusion about complex rotas and changes.

## 🦸‍♂️ **S.W.A.P. to the Rescue**

The Shift-Workers Arrangement Platform (S.W.A.P.) automates everything:

- 🌟 Parses shift data directly from Google Sheets.
- 🔄 Automatically syncs events with Google Calendar.
- 📆 Seamlessly maintains and updates your scheduling—_effortlessly_.

What started as a personal tool for Rachel has become an intuitive platform to help shift-workers everywhere gain back control.

---

## 🎯 **How It Works**

_Simplified workflow for busy people:_

| Step | Description                     | Tech Used               |
|------|---------------------------------|-------------------------|
| 1️⃣    | Read shifts listed in Sheets   | **Google Sheets API**   |
| 2️⃣    | Translate shifts to events     | **Python 3.10**         |
| 3️⃣    | Insert/update calendar events  | **Google Calendar API** |

---

## 📦 **Quick Installation**

_Go from zero to "Swapped" in minutes:_

**Requirements:**
- 📃 [Google Service Account credentials](https://developers.google.com/workspace/guides/create-credentials#service-account)
- 🔓 Enabled Sheets & Calendar APIs ([Google Cloud console](https://console.cloud.google.com/apis-dashboard))

### Option 1: Web Interface with Scheduler (Recommended)

Run the web interface with built-in scheduler and simple UI:

```bash
git clone https://github.com/madpin/swap.git
cd swap
pip install -r requirements.txt

# Set your credentials and password
export SERVICE_ACCOUNT_FILE='/path/to/service-account.json'
export ADMIN_PASSWORD='your_secure_password'

# Run the web interface!
python web.py
```

Then open `http://localhost:5000` in your browser and login with your password.

Features:
- 🎮 **Simple UI**: Play/Pause scheduler controls
- ⏰ **Auto-sync**: Runs every hour when scheduler is active
- 🔐 **Password Protected**: Secure with environment variable
- 📊 **Status Dashboard**: View last sync time and status

### Option 2: Command Line (One-time sync)

For a single manual sync:

```bash
# Set your credentials 
export SERVICE_ACCOUNT_FILE='/path/to/service-account.json'

# Run it!
python aio.py
```

That's it! Your work schedule syncs automatically. 🎉🙌

---

## 🚂 **Railway Deployment (Easiest!)**

Deploy to Railway with one click and get a hosted web interface:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

**Setup in Railway:**
1. Set environment variables:
   - `ADMIN_PASSWORD`: Your secure password
   - `SERVICE_ACCOUNT_JSON`: Paste your entire service account JSON
2. Deploy and access your dashboard
3. Click Play to start the scheduler!

📚 [Full Railway deployment guide](DEPLOYMENT.md)

## 🐳 **Docker Lovers, We've Got You Covered**

Want containerized & hassle-free deploys?

**Build and run:**
```bash
# Build the Docker image
docker build -t swap-rota-sync .

# Run the web interface
docker run \
  -p 5000:5000 \
  -e ADMIN_PASSWORD='your_password' \
  -v /path/to/your/service-account.json:/app/service-account.json \
  swap-rota-sync python web.py
```

Or run one-time sync:
```bash
docker run \
  -v /path/to/your/service-account.json:/app/service-account.json \
  swap-rota-sync
```

Let Docker manage your deployments while you relax (or perhaps watch some One Piece 🍿🏴‍☠️).

---

## 🛠️ **Customize It, Make it Yours**

S.W.A.P. was built to scale. Tweak this simple config for any worker in the script:

```python
USERS = [
    {
        "CALENDAR_NAME": "Rachel's Rota",
        "USER_NAME": "Rachel",
        "EMAILS_TO_SHARE": [
            "your.email@example.com"
        ],
    },
]
```

_Set your username, calendar names, and sharing emails to suite your workflow._

---

## 🧰 **Built with Good Stuff**

| Category | Technology                                      |
|----------|-------------------------------------------------|
| 🐍 Core  | Python 3.10                                     |
| 📄 APIs  | Google Sheets API, Google Calendar API          |
| 💻 Tools | Obsidian, Arc Browser                           |
| 🎯 Data  | Google Sheets                                   |
| 🐳 Deploy| Docker                                          |

---

## 💖 **Why "S.W.A.P."? Rachel, of course!**

Initially crafted with ❤️ to help my significant other Rachel avoid the chaos and frustration of manual schedule management. After all, what better motivation is there than making life easier for the ones we love?

> _Isaac Asimov's Three Laws of Robotics revised:_  
> 1. 🤖 Robots shall not harm loved ones' schedules.
> 2. 🤖 Robots shall support seamless automation for shift-workers… like Rachel.
> 3. 🤖 Robots must be efficient—so humans can spend more time together.

---

## 🤝 **Contributions are Golden!**

Want to enhance S.W.A.P.? We'd love to have you aboard! 🏴‍☠️

Here's your quick guide:
- 📌 Fork & clone
- 🔨 Build that awesome new feature (`git checkout -b my-awesome-feature`)
- ✅ Test rigorously
- 📤 Commit and push (`git push origin my-awesome-feature`)
- 🚀 Open a PR and let's merge that magic!

---

🗺️ **Built in Dublin**, fueled by pão de queijo, Sano Pizza, and refreshing walks near St. Patrick's Cathedral.

Thiago Pinto ([madpin](https://github.com/madpin)) 🇧🇷🇮🇪

Enjoy your productivity upgrade. Happy swapping! 🔄✨