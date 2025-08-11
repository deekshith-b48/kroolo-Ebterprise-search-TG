# Deployment Guide - Enterprise Search Telegram Bot

## Overview

This guide covers deployment options for the Enterprise Search Telegram Bot, from development setup to production deployment.

## Prerequisites

- Python 3.11+
- Redis server
- Telegram Bot Token
- Backend API access
- Domain name (for webhook mode)

## Development Setup

### Quick Start

1. **Clone and setup:**
```bash
git clone <repository>
cd Enterprise-search-TG
./setup.sh
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your values
```

3. **Run in polling mode:**
```bash
./dev.sh polling
```

### Development with ngrok

For webhook testing in development:

1. **Install ngrok:**
```bash
# Download from https://ngrok.com/
# Or install via package manager
brew install ngrok  # macOS
sudo apt-get install ngrok  # Ubuntu
```

2. **Start ngrok tunnel:**
```bash
./dev.sh ngrok
# Note the https URL (e.g., https://abc123.ngrok.io)
```

3. **Update configuration:**
```bash
# In .env file:
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok.io/telegram/webhook
WEBHOOK_MODE=true
```

4. **Start bot:**
```bash
./dev.sh webhook
```

## Production Deployment

### Option 1: Docker Deployment

#### Single Container

```bash
# Build image
docker build -t enterprise-search-bot .

# Run with environment file
docker run -d \
  --name search-bot \
  --env-file .env \
  -p 8000:8000 \
  enterprise-search-bot
```

#### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Update configuration
docker-compose restart bot
```

**Production docker-compose.yml:**
```yaml
version: '3.8'

services:
  bot:
    image: your-registry/enterprise-search-bot:latest
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - BACKEND_BASE_URL=${BACKEND_BASE_URL}
      - REDIS_URL=redis://redis:6379
      - WEBHOOK_MODE=true
    ports:
      - "8000:8000"
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - bot
    restart: unless-stopped

volumes:
  redis_data:
```

### Option 2: Cloud Platform Deployment

#### Heroku

1. **Create app:**
```bash
heroku create your-bot-name
```

2. **Add Redis addon:**
```bash
heroku addons:create heroku-redis:mini
```

3. **Set environment variables:**
```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set BACKEND_BASE_URL=your_backend_url
heroku config:set WEBHOOK_MODE=true
heroku config:set TELEGRAM_WEBHOOK_URL=https://your-bot-name.herokuapp.com/telegram/webhook
```

4. **Deploy:**
```bash
git push heroku main
```

#### AWS ECS

1. **Create task definition:**
```json
{
  "family": "enterprise-search-bot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "bot",
      "image": "your-registry/enterprise-search-bot:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "WEBHOOK_MODE", "value": "true"},
        {"name": "REDIS_URL", "value": "redis://elasticache-endpoint:6379"}
      ],
      "secrets": [
        {"name": "TELEGRAM_BOT_TOKEN", "valueFrom": "arn:aws:secretsmanager:..."}
      ]
    }
  ]
}
```

2. **Create service with load balancer and auto-scaling**

#### Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/enterprise-search-bot

# Deploy to Cloud Run
gcloud run deploy enterprise-search-bot \
  --image gcr.io/PROJECT_ID/enterprise-search-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars WEBHOOK_MODE=true \
  --set-env-vars REDIS_URL=redis://redis-ip:6379
```

### Option 3: VPS Deployment

#### Ubuntu/Debian Server

1. **Install dependencies:**
```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv redis-server nginx certbot
```

2. **Setup application:**
```bash
# Clone repository
git clone <repository> /opt/enterprise-search-bot
cd /opt/enterprise-search-bot

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values
```

3. **Create systemd service:**
```ini
# /etc/systemd/system/search-bot.service
[Unit]
Description=Enterprise Search Telegram Bot
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/enterprise-search-bot
Environment=PATH=/opt/enterprise-search-bot/venv/bin
ExecStart=/opt/enterprise-search-bot/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

4. **Configure nginx:**
```nginx
# /etc/nginx/sites-available/search-bot
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

5. **Enable SSL:**
```bash
sudo certbot --nginx -d your-domain.com
```

6. **Start services:**
```bash
sudo systemctl enable redis-server
sudo systemctl enable search-bot
sudo systemctl start search-bot
sudo systemctl enable nginx
```

## Configuration Management

### Environment Variables

**Required:**
- `TELEGRAM_BOT_TOKEN` - Bot token from BotFather
- `BACKEND_BASE_URL` - Your backend API URL
- `BACKEND_API_KEY` - Backend authentication key

**Optional:**
- `TELEGRAM_WEBHOOK_URL` - For webhook mode
- `REDIS_URL` - Redis connection string
- `ALLOWED_USER_IDS` - Comma-separated user IDs
- `SENTRY_DSN` - Error tracking

### Secrets Management

#### Using HashiCorp Vault
```bash
# Store secrets
vault kv put secret/search-bot \
  telegram_token="your_token" \
  backend_key="your_key"

# Retrieve in startup script
export TELEGRAM_BOT_TOKEN=$(vault kv get -field=telegram_token secret/search-bot)
```

#### Using AWS Secrets Manager
```python
# In your application
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

## Monitoring and Logging

### Health Checks

The bot provides a health endpoint:
```bash
curl http://your-domain.com/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "webhook_mode": true
}
```

### Logging

Configure structured logging in production:

```python
# .env
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn
```

### Metrics

Monitor key metrics:
- Message processing rate
- Backend response times
- Error rates
- Redis connection status

## Security Considerations

### Network Security

1. **Firewall rules:**
```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

2. **Rate limiting in nginx:**
```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    
    server {
        location /telegram/webhook {
            limit_req zone=api burst=5;
        }
    }
}
```

### Application Security

1. **Webhook secret verification**
2. **JWT token validation**
3. **Input sanitization**
4. **File upload restrictions**

### Backup Strategy

1. **Redis data backup:**
```bash
# Daily backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb /backup/redis-$(date +%Y%m%d).rdb
```

2. **Application backup:**
```bash
# Backup configuration and logs
tar -czf /backup/app-$(date +%Y%m%d).tar.gz \
  /opt/enterprise-search-bot/.env \
  /opt/enterprise-search-bot/logs/
```

## Scaling Considerations

### Horizontal Scaling

For high-traffic deployments:

1. **Load balancer configuration**
2. **Redis clustering**
3. **Stateless bot instances**
4. **Shared file storage**

### Performance Optimization

1. **Connection pooling**
2. **Response caching**
3. **Async processing**
4. **CDN for static assets**

## Troubleshooting

### Common Issues

1. **Bot not responding:**
   - Check webhook URL accessibility
   - Verify token validity
   - Check Redis connection

2. **Backend connection failures:**
   - Verify backend URL and API key
   - Check network connectivity
   - Review authentication logs

3. **File upload issues:**
   - Check file size limits
   - Verify storage permissions
   - Review temporary directory space

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
./dev.sh run
```

### Log Analysis

```bash
# Follow application logs
tail -f logs/bot.log

# Search for errors
grep ERROR logs/bot.log

# Monitor webhook requests
grep "webhook" logs/bot.log | tail -20
```
