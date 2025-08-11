#!/bin/bash
# Enterprise Search Telegram Bot - Run Script

echo "🚀 Starting Enterprise Search Telegram Bot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Run setup check
echo "🔍 Running setup check..."
python check_setup.py

if [ $? -eq 0 ]; then
    echo "✅ Setup check passed! Starting bot..."
    python start_bot.py
else
    echo "❌ Setup check failed. Please fix the issues above."
    exit 1
fi