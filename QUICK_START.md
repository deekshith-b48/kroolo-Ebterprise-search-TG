# 🚀 Quick Start Guide

## ✅ Setup Complete!

Your Enterprise Search Telegram Bot is ready to run. All checks have passed:

- ✅ Environment variables configured
- ✅ Dependencies installed  
- ✅ Redis connection working
- ✅ Bot token validated
- ✅ Authorized users configured

## 🏃 Running the Bot

### Option 1: Simple Start (Recommended)
```bash
./run.sh
```

### Option 2: Manual Start
```bash
source venv/bin/activate
python start_bot.py
```

### Option 3: Using Main Entry Point
```bash
source venv/bin/activate
python main.py
```

## 👥 Authorized Users

- **User ID**: `6463220788` (Regular User)
- **Admin ID**: `7213265972` (Admin User)

## 🔧 Configuration

Your bot is configured with:
- **Backend**: `https://92e1553c37e8.ngrok-free.app`
- **Mode**: Polling (not webhook)
- **Redis**: `localhost:6379`
- **Max File Size**: 50MB
- **Search Results**: 10 per query

## 📱 Bot Commands

Once running, users can interact with:

- `/start` - Welcome and setup
- `/help` - Show all commands
- `/search <query>` - AI-powered search
- `/connect` - Connect data sources
- `/upload` - Upload files
- `/sources` - View connected sources
- `/status` - Check system status

## 🔍 Testing the Bot

1. Start the bot with `./run.sh`
2. Open Telegram and find your bot
3. Send `/start` to begin
4. Try `/help` to see all commands
5. Use `/search test query` to test search

## 🛠️ Troubleshooting

If you encounter issues:

1. **Check setup**: `python check_setup.py`
2. **Verify Redis**: `redis-cli ping`
3. **Check logs**: Bot shows detailed logging
4. **Backend connection**: Ensure ngrok URL is accessible

## 📊 Admin Features

Admin users can:
- `/admin stats` - View system statistics
- `/admin users` - Manage authorized users
- Access to all user management features

## 🔄 Development

- **Debug mode**: Set `DEBUG=true` in `.env`
- **Log level**: Adjust `LOG_LEVEL` in `.env`
- **Webhook mode**: Set `WEBHOOK_MODE=true` for production

## 🎯 Next Steps

1. **Connect your backend**: Ensure your ngrok backend is running
2. **Add data sources**: Use `/connect` to link Google Drive, Slack, etc.
3. **Upload documents**: Use `/upload` to add searchable content
4. **Test search**: Try natural language queries

Your bot is ready to provide enterprise search capabilities! 🎉