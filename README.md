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

**Quickstart commands:**
```bash
git clone https://github.com/madpin/swap.git
cd swap
pip install -r requirements.txt

# The script uses this path by default.
export SERVICE_ACCOUNT_FILE='/Users/tpinto/madpin/swap/service-account.json'

# Run it!
python aio.py
```

That's it! Your work schedule syncs automatically. 🎉🙌

### Replace events from an old rota

When switching to a different rota file, run one full overwrite:

```bash
python aio.py --overwrite-events
```

This deletes events created by S.W.A.P., including events from versions that
predate ownership tagging, then rebuilds the calendar from the current sheet.
Other calendar events are left unchanged. Normal runs also remove old S.W.A.P.
events from dates that are present in the rota but blank for that user.

For Docker or cron, set the equivalent environment variable:

```bash
docker run --rm \
  -e SWAP_OVERWRITE_EVENTS=true \
  -v /Users/tpinto/madpin/swap/service-account.json:/app/service-account.json:ro \
  ghcr.io/madpin/swap
```

Use overwrite only for the first run after changing rota files; subsequent runs
can use the normal command.

---

## 🐳 **Docker Lovers, We've Got You Covered**

Want containerized & hassle-free deploys?

**Pull and run:**
```bash
# Pull the pre-built image
docker pull ghcr.io/madpin/swap

# Run the container with your service account
docker run \
  -v /Users/tpinto/madpin/swap/service-account.json:/app/service-account.json:ro \
  ghcr.io/madpin/swap
```

Let Docker manage your deployments while you relax (or perhaps watch some One Piece 🍿🏴‍☠️).

---

## ⏰ **Automated Daily Sync with Cron**

Want S.W.A.P. to run automatically every day? Set up a cron job!

**Create the log directory:**
```bash
mkdir -p /root/.config/swap/logs
```

**Add to your crontab:**
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6:00 AM
0 6 * * * docker run --rm -v /Users/tpinto/madpin/swap/service-account.json:/app/service-account.json:ro ghcr.io/madpin/swap >> /root/.config/swap/logs/swap-$(date +\%Y\%m\%d).log 2>&1
```

This will:
- 🕕 Run S.W.A.P. every day at 6:00 AM
- 📝 Save logs to `/root/.config/swap/logs/swap-YYYYMMDD.log`
- 📊 Capture both stdout and stderr for debugging

**Tip:** Adjust the time (`0 6 * * *`) to match your preference. Use [crontab.guru](https://crontab.guru/) to customize the schedule!

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
