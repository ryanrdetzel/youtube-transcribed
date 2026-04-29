import asyncio
import os
import re
from urllib.parse import parse_qs, urlparse

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    InvalidVideoId,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig

app = FastAPI(title="youtube-transcribed")


def _proxy_config() -> GenericProxyConfig | WebshareProxyConfig | None:
    webshare_user = os.environ.get("WEBSHARE_PROXY_USERNAME", "").strip()
    webshare_pass = os.environ.get("WEBSHARE_PROXY_PASSWORD", "").strip()
    if webshare_user and webshare_pass:
        return WebshareProxyConfig(proxy_username=webshare_user, proxy_password=webshare_pass)
    url = os.environ.get("PROXY_URL", "").strip()
    if url:
        return GenericProxyConfig(http_url=url, https_url=url)
    return None

_bearer = HTTPBearer(auto_error=False)


def _load_keys() -> set[str]:
    raw = os.environ.get("API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


def require_api_key(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> None:
    keys = _load_keys()
    if not keys:
        return
    if not credentials or credentials.credentials not in keys:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def extract_video_id(url_or_id: str) -> str:
    url_or_id = url_or_id.strip()
    if re.match(r"^[A-Za-z0-9_-]{11}$", url_or_id):
        return url_or_id
    parsed = urlparse(url_or_id)
    if parsed.hostname == "youtu.be":
        vid = parsed.path.lstrip("/").split("/")[0]
        if vid:
            return vid
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
    raise ValueError(f"Could not extract video ID from: {url_or_id!r}")


TRANSCRIPT_TIMEOUT = float(os.environ.get("TRANSCRIPT_TIMEOUT", "30"))


def _fetch(video_id: str, languages: list[str]):
    transcript = YouTubeTranscriptApi(proxy_config=_proxy_config()).fetch(video_id, languages=languages)
    return transcript


@app.get("/transcript")
async def get_transcript(
    url: str = Query(..., description="YouTube URL or video ID"),
    languages: list[str] = Query(default=["en"], description="Language priority list"),
    _: None = Depends(require_api_key),
):
    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    loop = asyncio.get_event_loop()
    try:
        transcript = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: _fetch(video_id, languages)),
            timeout=TRANSCRIPT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Transcript fetch timed out")
    except InvalidVideoId:
        raise HTTPException(status_code=400, detail="Invalid video ID")
    except VideoUnavailable:
        raise HTTPException(status_code=404, detail="Video is unavailable")
    except TranscriptsDisabled:
        raise HTTPException(status_code=422, detail="Transcripts are disabled for this video")
    except NoTranscriptFound:
        raise HTTPException(status_code=404, detail="No transcript found in requested languages")
    except CouldNotRetrieveTranscript as e:
        raise HTTPException(status_code=502, detail=str(e))

    text = " ".join(snippet.text for snippet in transcript)
    return {
        "video_id": transcript.video_id,
        "language": transcript.language,
        "language_code": transcript.language_code,
        "is_generated": transcript.is_generated,
        "transcript": text,
    }
