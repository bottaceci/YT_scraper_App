from dataclasses import dataclass
from typing import Any

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

@dataclass
class RunSummary:
    checked_at: str
    channel_count: int
    new_count: int
    items: list[dict[str, Any]]
    errors: list[dict[str, str]]
    used_legacy_dict: bool