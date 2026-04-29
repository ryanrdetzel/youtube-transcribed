# youtube-transcribed

A single-purpose FastAPI service that accepts a YouTube URL and returns the video transcript.

## Project structure

```
main.py        – entire app (FastAPI, auth, transcript endpoint)
pyproject.toml
Dockerfile
```

## Development

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API runs on http://localhost:8000. Interactive docs at http://localhost:8000/docs.

## Key facts

- Single endpoint: `GET /transcript?url=<youtube-url>`
- Uses `youtube-transcript-api` — no external API keys needed
- Auth: set `API_KEYS=key1,key2` env var to require `Authorization: Bearer <key>`; omit to disable auth
- Python 3.11+, FastAPI, uvicorn
- Deployed via Docker

## Adding features

Keep scope narrow: this service only fetches transcripts. Any analysis, summarization, or enrichment belongs in a separate service.
