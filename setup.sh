#!/bin/bash

# Enterprise Search Telegram Bot Setup Script
set -e

echo "🚀 Setting up Enterprise Search Telegram Bot..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment configuration..."
    cp .env.example .env
    echo "📝 Please edit .env with your configuration values:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - BACKEND_BASE_URL" 
    echo "   - BACKEND_API_KEY"
    echo "   - ALLOWED_USER_IDS"
    echo ""
fi

# Check if Redis is running
if ! command -v redis-cli &> /dev/null; then
    echo "📦 Redis CLI not found. Installing Redis..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y redis-server
    elif command -v brew &> /dev/null; then
        brew install redis
    else
        echo "⚠️ Please install Redis manually"
    fi
fi

# Start Redis if not running
if ! redis-cli ping &> /dev/null; then
    echo "🔄 Starting Redis..."
    if command -v systemctl &> /dev/null; then
        sudo systemctl start redis
    elif command -v brew &> /dev/null; then
        brew services start redis
    else
        echo "⚠️ Please start Redis manually"
    fi
fi

# Test Redis connection
if redis-cli ping &> /dev/null; then
    echo "✅ Redis connection successful"
else
    echo "❌ Redis connection failed"
fi

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads

# Set permissions
chmod 755 uploads

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python main.py"
echo ""
echo "🔧 For development with ngrok:"
echo "1. Install ngrok: https://ngrok.com/"
echo "2. Run: ngrok http 8000"
echo "3. Update TELEGRAM_WEBHOOK_URL in .env with ngrok URL"
echo "4. Set WEBHOOK_MODE=true in .env"
echo ""
