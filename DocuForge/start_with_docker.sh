#!/bin/bash
echo "🚀 Starting DocuForge AI (Docker Edition)..."

# 1. Activate Python Environment for AI Bridge
source ./venv/bin/activate

# 2. Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# 3. Cleanup Ports (Kill previous instances to avoid conflict)
echo "🧹 Cleaning up previous instances..."
docker-compose down 2>/dev/null
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

# 4. Start n8n in Docker (Detached)
echo "🐳 Starting n8n container..."
docker-compose up -d

# 5. Start AI Bridge Server (Foreground)
echo "✅ AI Bridge is starting on port 5001..."
echo "ℹ️  Keep this terminal open to maintain the AI connection."
echo "   (Press Ctrl+C to stop)"
echo ""
python3 scripts/docuforge_bridge.py
