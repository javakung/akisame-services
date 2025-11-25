# akisame-services

A FastAPI service to extract Open Graph (OG) tags from any URL.

## Features

- Extract OG tags from any URL
- Automatic URL validation
- Async HTTP client for efficient fetching
- Health check endpoint

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Start the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET /og-tags

Extract OG tags from a URL.

**Query Parameters:**
- `url` (required): The URL to fetch OG tags from

**Example:**
```bash
curl "http://localhost:8000/og-tags?url=https://github.com"
```

**Response:**
```json
{
  "url": "https://github.com/",
  "og_tags": {
    "title": "GitHub · Build and ship software on a single, collaborative platform",
    "description": "...",
    "image": "...",
    "type": "object",
    "site_name": "GitHub",
    "url": "https://github.com/"
  }
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## API Documentation

Once the server is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc