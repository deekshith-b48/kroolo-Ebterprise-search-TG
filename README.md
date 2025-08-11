# Enterprise Search Telegram Bot

A Telegram bot that provides enterprise search capabilities with Perplexity-style responses and citations. The bot integrates with your ngrok-hosted Enterprise Search backend and Pipedream workflows.

## Features

- 🔍 **Smart Search**: AI-powered search with inline citations
- 📁 **Multi-Platform Integration**: Connect to Google Drive, Slack, Notion, and custom sources
- 📤 **File Upload**: Upload documents for indexing
- 🔄 **Real-time Sync**: Update sources and track processing jobs
- 🔐 **Secure**: Whitelist-based authentication with backend authorization
- 📊 **Admin Tools**: User management and system monitoring

## Architecture

```
Telegram → Bot → Auth → Orchestrator → Backend (ngrok) / Pipedream → Response → User
```

## Commands

- `/start` - Welcome and setup
- `/connect` - Connect to external platforms
- `/fetch` - Browse documents from connected sources
- `/search <query>` - Search with AI-powered responses
- `/upload` - Upload files for indexing
- `/process [doc_id]` - Process specific documents
- `/update [source_id]` - Sync data sources
- `/status [job_id]` - Check job status
- `/help` - Show available commands

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Set up Redis (for state management):
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install locally
sudo apt-get install redis-server
```

4. Run the bot:
```bash
python src/main.py
```

## Development

- **Framework**: Python with python-telegram-bot
- **Web Server**: FastAPI for webhooks and admin routes
- **State Storage**: Redis for conversation state
- **Authentication**: Whitelist + JWT tokens
- **File Storage**: S3-compatible or ngrok backend

## Testing

```bash
pytest tests/
```

## Deployment

The bot can be deployed using Docker or directly on cloud platforms. See `docker-compose.yml` for containerized deployment.
# kroolo-Ebterprise-search-TG
