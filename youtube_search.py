from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from datetime import datetime

import requests

from models import VideoItem, SearchResult

SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"

def _now_iso() -> str:
    return datetime.now().astimezone().isoformat()

def log(enabled: bool, *args: object) -> None:
    if enabled:
        print(*args)


def read_text_file(path: str | Path) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {p}")
    return p.read_text(encoding="utf-8").strip()


def resolve_api_key(
    api_key: str | None = None,
    api_key_file: str | None = None,
) -> str:
    if api_key:
        return api_key.strip()

    if api_key_file:
        return read_text_file(api_key_file)

    env_key = os.getenv("YT_API_KEY", "").strip()
    if env_key:
        return env_key

    raise RuntimeError(
        "API key not found. Pass api_key, or api_key_file, or set YT_API_KEY."
    )


def iso8601_to_seconds(iso_duration: str) -> int:
    h = m = s = 0

    match = re.search(r"(\d+)H", iso_duration)
    if match:
        h = int(match.group(1))

    match = re.search(r"(\d+)M", iso_duration)
    if match:
        m = int(match.group(1))

    match = re.search(r"(\d+)S", iso_duration)
    if match:
        s = int(match.group(1))

    return h * 3600 + m * 60 + s


def api_error_message(payload: dict[str, Any]) -> str | None:
    error = payload.get("error")
    if not error:
        return None

    if isinstance(error, dict):
        code = error.get("code", "")
        message = error.get("message", "")
        status = error.get("status", "")
        return f"YouTube API error:\ncode: {code}\nmessage: {message}\nstatus: {status}"

    return f"YouTube API error: {error}"


def youtube_get(
    session: requests.Session,
    url: str,
    params: dict[str, Any],
    api_key: str,
) -> dict[str, Any]:
    params = dict(params)
    params["key"] = api_key

    response = session.get(url, params=params, timeout=30)

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        snippet = "\n".join(response.text.splitlines()[:60])
        raise RuntimeError(
            "Non-JSON response from YouTube API (first 60 lines):\n" + snippet
        ) from exc

    err = api_error_message(payload)
    if err:
        raise RuntimeError(err)

    response.raise_for_status()
    return payload


def search_page(
    session: requests.Session,
    api_key: str,
    query: str,
    page_token: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": query,
        "part": "snippet",
        "type": "video",
        "order": "date",
        "maxResults": 50,
        "fields": "nextPageToken,items(id/videoId)",
    }

    if page_token:
        params["pageToken"] = page_token

    return youtube_get(session, SEARCH_ENDPOINT, params, api_key)


def fetch_details(
    session: requests.Session,
    api_key: str,
    ids_csv: str,
) -> dict[str, Any]:
    params = {
        "part": "snippet,contentDetails",
        "id": ids_csv,
        "fields": (
            "items("
            "id,"
            "snippet(channelId,channelTitle,publishedAt,title),"
            "contentDetails(duration)"
            ")"
        ),
    }
    return youtube_get(session, VIDEOS_ENDPOINT, params, api_key)


def collect_candidate_ids(
    session: requests.Session,
    api_key: str,
    query: str,
    max_pages: int = 10,
    candidate_limit: int = 500,
    debug: bool = False,
) -> list[str]:
    candidate_ids: list[str] = []
    seen_ids: set[str] = set()
    page_token: str | None = None
    page = 0

    while page < max_pages and len(candidate_ids) < candidate_limit:
        page += 1
        payload = search_page(session, api_key, query, page_token)

        ids: list[str] = []
        for item in payload.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                ids.append(video_id)

        page_token = payload.get("nextPageToken")

        log(
            debug,
            f"page {page}: ids={len(ids)} nextToken={'yes' if page_token else 'no'}",
        )

        if not ids:
            break

        for vid in ids:
            if vid not in seen_ids:
                seen_ids.add(vid)
                candidate_ids.append(vid)
                if len(candidate_ids) >= candidate_limit:
                    break

        if not page_token:
            break

    log(debug, f"total candidates collected: {len(candidate_ids)}")
    return candidate_ids


def fetch_video_lookup(
    session: requests.Session,
    api_key: str,
    candidate_ids: list[str],
    debug: bool = False,
) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    batch_idx = 0

    for i in range(0, len(candidate_ids), 50):
        batch = candidate_ids[i:i + 50]
        ids_csv = ",".join(batch)
        batch_idx += 1

        payload = fetch_details(session, api_key, ids_csv)
        items = payload.get("items", [])

        log(
            debug,
            f"details batch {batch_idx}: requested={len(batch)} returned_items={len(items)}",
        )

        for item in items:
            vid = item.get("id")
            if vid:
                by_id[vid] = item

    log(debug, f"lookup size: {len(by_id)}")
    return by_id


def build_video_items(
    candidate_ids: list[str],
    by_id: dict[str, dict[str, Any]],
    target: int = 100,
    min_seconds: int = 120,
) -> list[VideoItem]:
    results: list[VideoItem] = []

    for vid in candidate_ids:
        item = by_id.get(vid)
        if not item:
            continue

        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})

        duration_iso = content_details.get("duration")
        if not duration_iso:
            continue

        duration_seconds = iso8601_to_seconds(duration_iso)
        if duration_seconds < min_seconds:
            continue

        channel_id = snippet.get("channelId", "")
        channel_title = snippet.get("channelTitle", "")
        title = snippet.get("title", "")
        published = snippet.get("publishedAt")
        url = f"https://www.youtube.com/watch?v={vid}"

        if not channel_id or not channel_title or not title:
            continue

        results.append(
            VideoItem(
                channel_id=channel_id,
                channel_title=channel_title,
                title=title,
                url=url,
                published=published,
            )
        )

        if len(results) >= target:
            break

    return results


def search_videos(
    query: str,
    *,
    target: int = 20,
    max_pages: int = 5,
    min_seconds: int = 120,
    candidate_limit: int = 200,
    debug: bool = False,
    api_key: str | None = None,
    api_key_file: str | None = None,
) -> list[VideoItem]:
    resolved_api_key = resolve_api_key(
        api_key=api_key,
        api_key_file=api_key_file,
    )

    with requests.Session() as session:
        candidate_ids = collect_candidate_ids(
            session=session,
            api_key=resolved_api_key,
            query=query,
            max_pages=max_pages,
            candidate_limit=candidate_limit,
            debug=debug,
        )

        if not candidate_ids:
            return []

        by_id = fetch_video_lookup(
            session=session,
            api_key=resolved_api_key,
            candidate_ids=candidate_ids,
            debug=debug,
        )

    return build_video_items(
        candidate_ids=candidate_ids,
        by_id=by_id,
        target=target,
        min_seconds=min_seconds,
    )


def main(
    query: str,
    *,
    target: int = 20,
    max_pages: int = 5,
    min_seconds: int = 120,
    candidate_limit: int = 200,
    debug: bool = False,
    api_key: str | None = None,
    api_key_file: str | None = r"C:\Users\botta\channel-watcher\secret\api_key.txt",
) -> SearchResult:
    
    items = search_videos(
        query=query,
        target=target,
        max_pages=max_pages,
        min_seconds=min_seconds,
        candidate_limit=candidate_limit,
        debug=debug,
        api_key=api_key,
        api_key_file=api_key_file,
    )

    return SearchResult(
        query=query,
        searched_at = _now_iso(),
        res_count=len(items),
        items=items
    )