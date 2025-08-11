# Enterprise Search Telegram Bot - API Documentation

## Overview

The Enterprise Search Telegram Bot provides a conversational interface for searching across multiple data sources with AI-powered responses and citations. This document describes the bot's API endpoints, commands, and integration patterns.

## Bot Commands

### Core Commands

#### `/start`
Initialize the bot and show welcome message with quick action buttons.

**Response:** Welcome message with inline keyboard for quick access to main features.

#### `/help`
Display comprehensive help information about available commands and usage.

**Response:** Formatted help text with examples and command descriptions.

#### `/search <query>`
Perform AI-powered search across connected data sources.

**Parameters:**
- `query` (required): Natural language search query

**Example:**
```
/search quarterly revenue growth in Q2
```

**Response:** Formatted answer with inline citations and source links.

#### `/connect`
Connect to external data sources (Google Drive, Slack, Notion, etc.).

**Response:** Interactive platform selection menu.

#### `/upload`
Upload files for indexing and search.

**Usage:** Send the command, then upload a file in the next message.

**Supported formats:** PDF, DOC, DOCX, TXT, images, audio files

#### `/fetch`
Browse and select documents from connected sources.

**Response:** Paginated list of documents with selection options.

### Advanced Commands

#### `/update [source_id] [mode]`
Sync data from connected sources.

**Parameters:**
- `source_id` (optional): Specific source to update
- `mode` (optional): `incremental` (default) or `full`

**Example:**
```
/update drive_source_123 full
```

#### `/process <document_id> [operations]`
Process specific documents with AI operations.

**Parameters:**
- `document_id` (required): Document identifier
- `operations` (optional): Comma-separated list (summarize, index, extract)

**Example:**
```
/process doc_456 summarize,index
```

#### `/status <job_id>`
Check the status of background processing jobs.

**Parameters:**
- `job_id` (required): Job identifier returned from async operations

### Admin Commands

#### `/admin`
Access administrative functions (admin users only).

**Subcommands:**
- `stats` - System statistics
- `users` - List authorized users
- `add_user <user_id>` - Add user to whitelist
- `remove_user <user_id>` - Remove user from whitelist

## Backend API Integration

### Authentication

All backend requests include authentication headers:

```http
Authorization: Bearer <jwt_token>
X-Bot-User-ID: <telegram_user_id>
X-API-Key: <backend_api_key>
```

### API Endpoints

#### Connect Platform
```http
POST /api/connect
Content-Type: application/json

{
  "user_id": 123456789,
  "platform": "drive|slack|notion|custom",
  "params": {}
}
```

**Response:**
```json
{
  "status": "success",
  "connection_id": "conn_123",
  "oauth_url": "https://oauth.provider.com/authorize?..."
}
```

#### Get Sources
```http
GET /api/sources?user_id=123456789
```

**Response:**
```json
{
  "sources": [
    {
      "id": "source_123",
      "name": "Google Drive",
      "type": "drive",
      "status": "connected",
      "last_sync": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### Search
```http
POST /api/search
Content-Type: application/json

{
  "user_id": 123456789,
  "query": "quarterly revenue growth",
  "top_k": 10,
  "source_filters": ["drive:123", "slack:456"],
  "include_citations": true
}
```

**Response:**
```json
{
  "answer": "Revenue grew 12% in Q2, driven by APAC expansion [1][2]",
  "citations": [
    {
      "id": 1,
      "title": "Q2 Financial Report",
      "url": "https://drive.google.com/file/d/123",
      "snippet": "APAC revenue increased by 25%...",
      "doc_id": "doc_789"
    }
  ],
  "meta": {
    "elapsed_ms": 342,
    "sources_searched": 3
  }
}
```

#### Upload File
```http
POST /api/upload
Content-Type: multipart/form-data

file: <file_data>
user_id: 123456789
metadata: {"filename": "report.pdf", "tags": ["financial"]}
```

**Response:**
```json
{
  "document_id": "doc_123",
  "job_id": "job_456",
  "status": "processing"
}
```

#### Job Status
```http
GET /api/job-status?job_id=job_456&user_id=123456789
```

**Response:**
```json
{
  "job_id": "job_456",
  "status": "completed|running|failed",
  "progress": 100,
  "message": "Processing completed successfully",
  "result": {}
}
```

## Webhook Integration

### Telegram Webhooks

The bot can receive updates via webhooks for production deployment:

```http
POST /telegram/webhook
X-Telegram-Bot-Api-Secret-Token: <webhook_secret>
Content-Type: application/json

{
  "update_id": 123,
  "message": {
    "message_id": 456,
    "from": {"id": 123456789, "first_name": "User"},
    "chat": {"id": 123456789, "type": "private"},
    "text": "/search test query"
  }
}
```

### Backend Job Callbacks

Backend can notify the bot when jobs complete:

```http
POST /api/job-callback
Content-Type: application/json

{
  "job_id": "job_456",
  "status": "completed",
  "result": {
    "documents_processed": 5,
    "errors": []
  }
}
```

## Response Formats

### Search Response Format

The bot formats search responses in a Perplexity-style layout:

```
🔍 **Search Results**

[AI-generated answer with inline citations [1][2]]

📚 **Sources:**
[1] [Document Title](https://example.com/doc1) — Brief snippet excerpt...
[2] [Another Document](https://example.com/doc2) — Another brief excerpt...
```

### Error Handling

All errors are presented to users in a friendly format:

```
❌ **Error Title**

Error description with actionable guidance.

Use /help for assistance or contact support.
```

### Status Updates

Background job status is communicated clearly:

```
🔄 **Processing Started**

Job ID: `job_123`
Operation: Document indexing

Use `/status job_123` to check progress.
```

## Rate Limiting

- Search: 10 requests per minute per user
- Upload: 5 files per hour per user
- Admin commands: No limit for admin users

## Error Codes

| Code | Description | Action |
|------|-------------|---------|
| 401  | Unauthorized user | Add user to whitelist |
| 403  | Insufficient permissions | Contact admin |
| 429  | Rate limit exceeded | Wait and retry |
| 500  | Backend error | Check backend status |
| 503  | Service unavailable | Retry later |

## Development

### Testing with curl

Search example:
```bash
curl -X POST "https://your-backend.ngrok.io/api/search" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "query": "test search",
    "top_k": 5
  }'
```

### Mock Responses

For development, the bot supports mock responses when backend is unavailable:

```json
{
  "answer": "Mock search result for development [1]",
  "citations": [
    {"id": 1, "title": "Mock Document", "url": "#", "snippet": "Test snippet"}
  ]
}
```
