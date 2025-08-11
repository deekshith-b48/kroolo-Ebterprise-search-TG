## 📝 COPY THESE EXACT STEPS:

### Step 1: Get Telegram Bot Token
1. Open Telegram, search for @BotFather
2. Send: /newbot
3. Name: Enterprise Search Bot
4. Username: yourname_search_bot
5. COPY THE TOKEN (looks like: 6123456789:AAF...)

### Step 2: Get Your User ID  
1. Open Telegram, search for @userinfobot
2. Send any message
3. COPY YOUR USER ID (a number like: 987654321)

### Step 3: Edit Configuration
Run this command to edit your config:
```bash
nano .env
```

Replace these 3 lines:
```
TELEGRAM_BOT_TOKEN=paste_your_bot_token_here
ALLOWED_USER_IDS=paste_your_user_id_here  
ADMIN_USER_IDS=paste_your_user_id_here
```

### Step 4: Test Bot (Mock Mode)
```bash
# Set up test environment  
source venv/bin/activate

# Run bot in test mode (no backend needed)
python main.py
```

### Step 5: Test on Telegram
1. Find your bot by its username
2. Send: /start
3. You should get a welcome message!

## 🚀 QUICK START (Copy & Paste):

```bash
# 1. Edit config
nano .env

# 2. Start bot  
source venv/bin/activate
python main.py
```

When you see "Bot started in polling mode" - your bot is ready!

## ⚡ EXAMPLE WORKING CONFIG:

Here's what your .env should look like (with YOUR values):

```
TELEGRAM_BOT_TOKEN=6123456789:AAEaBcDefGhIjKlMnOpQrStUvWxYz123456
ALLOWED_USER_IDS=987654321
ADMIN_USER_IDS=987654321  
BACKEND_BASE_URL=https://your-backend.ngrok.io
BACKEND_API_KEY=test-api-key-123
BACKEND_JWT_SECRET=test-jwt-secret-456
WEBHOOK_MODE=false
DEBUG=true
```

Replace the first 3 values with YOUR actual values from Telegram!
