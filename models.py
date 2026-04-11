from __future__ import annotations

from dataclasses import dataclass, field
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
    updated_channel_state: ChannelState
    error: dict[str, str] | None = None

@dataclass
class RunSummary:
    checked_at: str
    channel_count: int
    new_count: int
    items: list[dict[str, Any]]
    errors: list[dict[str, str]]
    used_legacy_dict: bool

@dataclass
class ChannelState:
    channel_title: str
    urls: list[str] = field(default_factory=list)
    last_checked: str | None = None

@dataclass
class SuccessfulRun:
    checked_at: str
    new_count: int
    items: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class ChannelConfig:
    channel_id: str
    label: str

@dataclass
class SearchResult:
    query: str
    searched_at: str
    res_count: int
    items: list[dict[str, Any]] = field(default_factory=list)