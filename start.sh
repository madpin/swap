#!/bin/bash
# Quick start script for S.W.A.P. web interface

echo "🔄 S.W.A.P. - Shift-Workers Arrangement Platform"
echo "================================================"
echo ""

# Check if SERVICE_ACCOUNT_FILE is set
if [ -z "$SERVICE_ACCOUNT_FILE" ] && [ -z "$SERVICE_ACCOUNT_JSON" ]; then
    echo "❌ Error: SERVICE_ACCOUNT_FILE or SERVICE_ACCOUNT_JSON must be set"
    echo ""
    echo "Example:"
    echo "  export SERVICE_ACCOUNT_FILE='/path/to/service-account.json'"
    echo "  export ADMIN_PASSWORD='your_password'"
    echo "  ./start.sh"
    exit 1
fi

# Check if ADMIN_PASSWORD is set
if [ -z "$ADMIN_PASSWORD" ]; then
    echo "⚠️  Warning: ADMIN_PASSWORD not set, using default 'changeme'"
    echo "   Set it with: export ADMIN_PASSWORD='your_password'"
    echo ""
    export ADMIN_PASSWORD="changeme"
fi

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found (.venv or venv)"
    echo "   Consider creating one with: python -m venv .venv"
    echo ""
fi

# Install dependencies if needed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Start the web server
echo "🚀 Starting web interface..."
echo "   URL: http://localhost:5000"
echo "   Password: $ADMIN_PASSWORD"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python web.py

