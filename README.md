# youtube-transcribed

A minimal FastAPI service that accepts a YouTube URL and returns the full video transcript as plain text.

## Endpoint

### `GET /transcript`

| Parameter   | Required | Default | Description                         |
|-------------|----------|---------|-------------------------------------|
| `url`       | yes      |         | YouTube URL or video ID             |
| `languages` | no       | `en`    | Language priority list (repeatable) |

**Example:**

```bash
curl "http://localhost:8000/transcript?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Response:**

```json
{
  "video_id": "dQw4w9WgXcQ",
  "language": "English",
  "language_code": "en",
  "is_generated": false,
  "transcript": "..."
}
```

**Error codes:**

| Status | Meaning                                    |
|--------|--------------------------------------------|
| 400    | Invalid URL or video ID                    |
| 401    | Missing or invalid API key                 |
| 404    | Video unavailable or no transcript found   |
| 422    | Transcripts disabled for this video        |
| 502    | Could not retrieve transcript from YouTube |

## Authentication

Authentication is optional. Set the `API_KEYS` environment variable to a comma-separated list of keys to enable it:

```
API_KEYS=key1,key2,key3
```

When set, requests must include:

```
Authorization: Bearer <key>
```

If `API_KEYS` is unset or empty, all requests are allowed.

## Running locally

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive docs at http://localhost:8000/docs.

## Docker

```bash
docker build -t youtube-transcribed .
docker run -p 8000:8000 -e API_KEYS=yourkey youtube-transcribed
```
