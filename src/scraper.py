from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import feedparser

from storage import (
    load_legacy_seen_by_title,
    load_seen_data,
    record_successful_run,
    save_seen_data,
)


ROOT = "https://www.youtube.com/feeds/videos.xml?channel_id="


@dataclass
class VideoItem:
    channel_id: str
    channel_title: str
    title: str
    url: str
    published: str | None = None

@dataclass
class ChannelCheckResult:
    channel_id: str
    channel_title: str
    new_items: list[dict[str, Any]]
    updated_channel_state: dict[str, Any]
    error: dict[str, str] | None = None


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def parse_channel(channel_id: str, fallback_label: str) -> tuple[str, list[VideoItem], str | None]:
    url = ROOT + channel_id
    feed = feedparser.parse(url)

    channel_title = feed.feed.get("title") or fallback_label
    items: list[VideoItem] = []
    error_message: str | None = None

    if getattr(feed, "bozo", False) and not getattr(feed, "entries", None):
        error_message = str(getattr(feed, "bozo_exception", "Unknown feed parsing error"))

    for entry in feed.entries:
        items.append(
            VideoItem(
                channel_id=channel_id,
                channel_title=channel_title,
                title=entry.get("title", "Untitled video"),
                url=entry.get("link", ""),
                published=entry.get("published"),
            )
        )

    return channel_title, items, error_message


def load_run_context() -> dict[str, Any]:
    seen_data = load_seen_data()
    seen_channels = seen_data.get("channels", {})

    legacy_seen_by_title: dict[str, list[str]] = {}
    if not seen_channels:
        legacy_seen_by_title = load_legacy_seen_by_title()

    return {
        "seen_channels": seen_channels,
        "legacy_seen_by_title": legacy_seen_by_title,
        "checked_at": _now_iso(),
    }


def process_channel(
    channel: dict[str, str],
    seen_channels: dict[str, Any],
    legacy_seen_by_title: dict[str, list[str]],
    checked_at: str,
) -> dict[str, Any]:
    channel_id = channel["id"]
    fallback_label = channel["label"]

    previous_channel_state = seen_channels.get(channel_id, {})

    channel_title, items, error_message = parse_channel(channel_id, fallback_label)
    current_urls = [item.url for item in items if item.url]

    old_urls: list[str] | None = None
    if channel_id in seen_channels:
        old_urls = [str(url) for url in previous_channel_state.get("urls", [])]
    elif channel_title in legacy_seen_by_title:
        old_urls = [str(url) for url in legacy_seen_by_title[channel_title]]

    new_items: list[dict[str, Any]] = []
    if old_urls is not None:
        old_url_set = set(old_urls)
        for item in items:
            if item.url and item.url not in old_url_set:
                new_items.append(asdict(item))

    fetch_succeeded = bool(items) or not error_message

    if fetch_succeeded:
        updated_channel_state = {
            "channel_title": channel_title,
            "urls": current_urls,
            "last_checked": checked_at,
        }
    else:
        updated_channel_state = {
            "channel_title": previous_channel_state.get("channel_title", channel_title),
            "urls": [str(url) for url in previous_channel_state.get("urls", [])],
            "last_checked": previous_channel_state.get("last_checked"),
        }

    error_payload: dict[str, str] | None = None
    if error_message:
        error_payload = {
            "channel_id": channel_id,
            "channel_title": channel_title,
            "error": error_message,
        }

    return ChannelCheckResult(
        channel_id=channel_id,
        channel_title=channel_title,
        new_items=new_items,
        updated_channel_state=updated_channel_state,
        error=error_payload,
    )


def finalize_run(
    updated_channels: dict[str, Any],
    new_items: list[dict[str, Any]],
    errors: list[dict[str, str]],
    checked_at: str,
    channel_count: int,
    used_legacy_dict: bool,
) -> dict[str, Any]:
    new_items.sort(key=lambda item: (item["channel_title"].lower(), item["title"].lower()))

    seen_payload = {
        "version": 1,
        "channels": updated_channels,
    }
    save_seen_data(seen_payload)

    run_summary = {
        "checked_at": checked_at,
        "channel_count": channel_count,
        "new_count": len(new_items),
        "items": new_items,
        "errors": errors,
        "used_legacy_dict": used_legacy_dict,
    }

    if new_items:
        record_successful_run(
            {
                "checked_at": checked_at,
                "new_count": len(new_items),
                "items": new_items,
            }
        )

    return run_summary