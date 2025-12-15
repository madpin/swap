#!/usr/bin/env python3
"""
S.W.A.P. Web Interface
A simple web interface with scheduler controls for the Shift-Workers Arrangement Platform
"""

import os
import logging
from datetime import datetime
from functools import wraps
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Import the main sync function from aio.py
from aio import main as sync_main

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Scheduler
scheduler = BackgroundScheduler(timezone=pytz.timezone("Europe/Dublin"))
scheduler_running = False

# Get password from environment variable
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

# Sync status tracking
last_sync_time = None
last_sync_status = None
last_sync_message = None


def check_auth():
    """Check if user is authenticated"""
    return session.get("authenticated", False)


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_auth():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def run_sync():
    """Run the calendar sync"""
    global last_sync_time, last_sync_status, last_sync_message
    logger.info("Starting scheduled sync...")
    try:
        sync_main()
        last_sync_time = datetime.now()
        last_sync_status = "success"
        last_sync_message = "Sync completed successfully"
        logger.info("Sync completed successfully")
    except Exception as e:
        last_sync_time = datetime.now()
        last_sync_status = "error"
        last_sync_message = str(e)
        logger.error(f"Sync failed: {e}", exc_info=True)


# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>S.W.A.P. - Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 400px;
            width: 100%;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:active {
            transform: translateY(0);
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #c33;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔄 S.W.A.P.</h1>
        <p class="subtitle">Shift-Workers Arrangement Platform</p>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required autofocus>
            </div>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>S.W.A.P. - Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 5px;
        }
        .subtitle {
            color: #666;
            font-size: 0.9em;
        }
        .logout-btn {
            float: right;
            padding: 8px 16px;
            background: #f44336;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 14px;
            transition: background 0.3s;
        }
        .logout-btn:hover {
            background: #d32f2f;
        }
        .card {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        .status-section {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        .status-indicator {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            flex-shrink: 0;
        }
        .status-running { background: #4caf50; }
        .status-stopped { background: #f44336; }
        .status-info {
            flex-grow: 1;
        }
        .status-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        .status-detail {
            color: #666;
            font-size: 0.9em;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }
        .btn {
            flex: 1;
            padding: 16px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn-play {
            background: #4caf50;
            color: white;
        }
        .btn-pause {
            background: #ff9800;
            color: white;
        }
        .btn-sync {
            background: #2196f3;
            color: white;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .info-section {
            border-top: 1px solid #e0e0e0;
            padding-top: 20px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .info-row:last-child {
            border-bottom: none;
        }
        .info-label {
            color: #666;
            font-weight: 500;
        }
        .info-value {
            color: #333;
            font-weight: 600;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge-success {
            background: #e8f5e9;
            color: #2e7d32;
        }
        .badge-error {
            background: #ffebee;
            color: #c62828;
        }
        .badge-none {
            background: #f5f5f5;
            color: #757575;
        }
        .alert {
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #e8f5e9;
            color: #2e7d32;
            border-left: 4px solid #4caf50;
        }
        .alert-error {
            background: #ffebee;
            color: #c62828;
            border-left: 4px solid #f44336;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
            <h1>🔄 S.W.A.P. Dashboard</h1>
            <p class="subtitle">Shift-Workers Arrangement Platform</p>
        </div>

        <div class="card">
            <div class="status-section">
                <div class="status-indicator {% if scheduler_running %}status-running{% else %}status-stopped{% endif %}">
                    {% if scheduler_running %}▶️{% else %}⏸️{% endif %}
                </div>
                <div class="status-info">
                    <div class="status-title">
                        Scheduler is {% if scheduler_running %}Running{% else %}Stopped{% endif %}
                    </div>
                    <div class="status-detail">
                        {% if scheduler_running %}
                        Automatic sync every hour at :00
                        {% else %}
                        Click Play to start automatic sync
                        {% endif %}
                    </div>
                </div>
            </div>

            <div class="controls">
                <button class="btn btn-play" onclick="startScheduler()" {% if scheduler_running %}disabled{% endif %}>
                    ▶️ Play
                </button>
                <button class="btn btn-pause" onclick="stopScheduler()" {% if not scheduler_running %}disabled{% endif %}>
                    ⏸️ Pause
                </button>
                <button class="btn btn-sync" onclick="runSync()">
                    🔄 Sync Now
                </button>
            </div>

            <div class="info-section">
                <div class="info-row">
                    <span class="info-label">Last Sync:</span>
                    <span class="info-value">{{ last_sync_time or 'Never' }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Status:</span>
                    <span class="info-value">
                        {% if last_sync_status == 'success' %}
                        <span class="status-badge badge-success">✓ Success</span>
                        {% elif last_sync_status == 'error' %}
                        <span class="status-badge badge-error">✗ Error</span>
                        {% else %}
                        <span class="status-badge badge-none">— No sync yet</span>
                        {% endif %}
                    </span>
                </div>
                {% if last_sync_message %}
                <div class="info-row">
                    <span class="info-label">Message:</span>
                    <span class="info-value">{{ last_sync_message }}</span>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        function startScheduler() {
            fetch('/api/scheduler/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    }
                });
        }

        function stopScheduler() {
            fetch('/api/scheduler/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    }
                });
        }

        function runSync() {
            if (confirm('Run sync now? This may take a few minutes.')) {
                fetch('/api/sync', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        location.reload();
                    });
            }
        }

        // Auto-refresh every 30 seconds to update status
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
"""


@app.route("/")
@login_required
def index():
    """Dashboard page"""
    global scheduler_running, last_sync_time, last_sync_status, last_sync_message
    
    last_sync_formatted = None
    if last_sync_time:
        last_sync_formatted = last_sync_time.strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        scheduler_running=scheduler_running,
        last_sync_time=last_sync_formatted,
        last_sync_status=last_sync_status,
        last_sync_message=last_sync_message,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
        return render_template_string(LOGIN_TEMPLATE, error="Invalid password")
    return render_template_string(LOGIN_TEMPLATE)


@app.route("/logout")
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/scheduler/start", methods=["POST"])
@login_required
def api_start_scheduler():
    """Start the scheduler"""
    global scheduler_running
    if not scheduler_running:
        # Schedule to run every hour at :00
        scheduler.add_job(
            run_sync,
            CronTrigger(minute=0),
            id="sync_job",
            replace_existing=True,
        )
        if not scheduler.running:
            scheduler.start()
        scheduler_running = True
        logger.info("Scheduler started")
    return jsonify({"success": True})


@app.route("/api/scheduler/stop", methods=["POST"])
@login_required
def api_stop_scheduler():
    """Stop the scheduler"""
    global scheduler_running
    if scheduler_running:
        try:
            scheduler.remove_job("sync_job")
        except:
            pass
        scheduler_running = False
        logger.info("Scheduler stopped")
    return jsonify({"success": True})


@app.route("/api/sync", methods=["POST"])
@login_required
def api_sync():
    """Run sync immediately"""
    try:
        run_sync()
        return jsonify({"success": True, "message": "Sync completed successfully"})
    except Exception as e:
        logger.error(f"Manual sync failed: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Sync failed: {str(e)}"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting S.W.A.P. web interface on port {port}")
    logger.info(f"Admin password: {'Set from ADMIN_PASSWORD env var' if os.environ.get('ADMIN_PASSWORD') else 'Using default (CHANGE THIS!)'}")
    app.run(host="0.0.0.0", port=port, debug=False)

