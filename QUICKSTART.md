# 🚀 Quick Start Guide - Required Inputs

## Step 1: Create Your Telegram Bot

1. **Message @BotFather on Telegram:**
   - Send `/newbot`
   - Choose a name: `Enterprise Search Bot`
   - Choose a username: `YourCompanySearchBot` (must end with 'bot')
   - **Copy the bot token** (looks like: `123456789:ABCDEF...`)

2. **Get your Telegram User ID:**
   - Message @userinfobot on Telegram
   - **Copy your user ID** (a number like: `123456789`)

## Step 2: Setup Your Backend (ngrok for development)

If you have an existing Enterprise Search backend:

1. **Install ngrok:**
   ```bash
   # Download from https://ngrok.com/download
   # Or install via package manager
   ```

2. **Start your backend** (if not already running)

3. **Expose with ngrok:**
   ```bash
   ngrok http <your-backend-port>
   # Example: ngrok http 3000
   # Copy the https URL (like: https://abc123.ngrok.io)
   ```

If you DON'T have a backend yet, we can use mock mode for testing.

## Step 3: Configure Environment

Copy and edit your configuration:

```bash
cd /home/darktunnel/Enterprise-search-TG
cp .env.example .env
```

**Edit .env with these REQUIRED values:**

```bash
# === REQUIRED CONFIGURATION ===

# 1. Telegram Bot Token (from Step 1)
TELEGRAM_BOT_TOKEN=123456789:ABCDEF1234567890abcdef1234567890ABC

# 2. Your Telegram User ID (from Step 1)
ALLOWED_USER_IDS=123456789
ADMIN_USER_IDS=123456789

# 3. Backend URL (from Step 2, or use mock)
BACKEND_BASE_URL=https://abc123.ngrok.io
# OR for testing without backend:
# BACKEND_BASE_URL=http://localhost:8001

# 4. Simple secrets (you can use any random strings)
BACKEND_API_KEY=your-secret-api-key-12345
BACKEND_JWT_SECRET=your-jwt-secret-67890
TELEGRAM_WEBHOOK_SECRET=webhook-secret-abcde

# 5. Development settings
WEBHOOK_MODE=false  # Start with polling mode
DEBUG=true
FILE_STORAGE_TYPE=local

# === OPTIONAL (keep defaults) ===
REDIS_URL=redis://localhost:6379
LOCAL_STORAGE_PATH=./uploads
LOG_LEVEL=INFO
```

## Step 4: Quick Test Setup

**Option A: With Real Backend**
```bash
# Make sure your backend is running and exposed via ngrok
./dev.sh run
```

**Option B: Mock Mode (for testing without backend)**
```bash
# This will run with simulated backend responses
BACKEND_BASE_URL=http://localhost:8001 ./dev.sh run
```

## Step 5: Test Your Bot

1. **Find your bot on Telegram** using the username you created
2. **Send `/start`** - you should get a welcome message
3. **Try `/search test query`** - should work even without real backend

## Example Complete .env File

Here's a working example with mock values:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=6123456789:AAEaBcDefGhIjKlMnOpQrStUvWxYz123456
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok.io/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=my-webhook-secret-123

# Backend Configuration  
BACKEND_BASE_URL=https://def456.ngrok.io
BACKEND_API_KEY=my-api-key-67890
BACKEND_JWT_SECRET=my-jwt-secret-abcdef

# Authentication (your Telegram user ID)
ALLOWED_USER_IDS=987654321
ADMIN_USER_IDS=987654321

# Simple defaults
REDIS_URL=redis://localhost:6379
FILE_STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./uploads
WEBHOOK_MODE=false
DEBUG=true
LOG_LEVEL=INFO
```

## Need Help Getting These Values?

### 🤖 Telegram Bot Token
- Go to [@BotFather](https://t.me/botfather)
- Send `/newbot` and follow instructions
- Copy the token that looks like: `123456789:ABCdefGHijklMNopqrsTUVwxyz`

### 👤 Your User ID  
- Go to [@userinfobot](https://t.me/userinfobot)
- Send any message
- Copy the number shown as your ID

### 🌐 Backend URL
- If you have ngrok: run `ngrok http <port>` and copy the https URL
- If no backend: use `http://localhost:8001` for mock mode
- If hosted elsewhere: use your actual backend URL

### 🔑 API Keys
- These can be any random strings for development
- For production, use proper secret generation

Ready to start? Run:
```bash
./setup.sh  # Install dependencies
# Edit .env with your values
./dev.sh run  # Start the bot
```
