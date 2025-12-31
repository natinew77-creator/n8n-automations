#!/bin/bash
echo "🚀 Starting DocuForge AI..."

# 1. Activate Python Environment (for AI scripts)
source ./venv/bin/activate

# 2. Check if dependencies are installed
if ! python3 -c "import clip" &> /dev/null; then
    echo "⚠️  Warning: CLIP not fully installed. Video ranking might be random."
else
    echo "✅ AI Ranking Engine Ready"
fi

# 3. Start n8n locally
echo "🌐 Launching n8n..."
export N8N_ user_management__jwt_secret="docuforge_secret_123" # Suppress setup wizard somewhat
./node_modules/.bin/n8n start --tunnel
