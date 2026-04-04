from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

import flet as ft

from models import RunSummary


def format_timestamp(value: str | None) -> str:
    if not value:
        return "Unknown time"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


def build_video_card(item: dict[str, Any]) -> ft.Control:
    subtitle_parts = [item.get("channel_title", "Unknown channel")]
    if item.get("published"):
        subtitle_parts.append(item["published"])

    return ft.Card(
        content=ft.Container(
            padding=12,
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(
                        item.get("title", "Untitled video"),
                        size=16,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Text(
                        " • ".join(subtitle_parts),
                        size=12,
                        color=ft.Colors.BLUE_GREY_400,
                    ),
                    ft.TextButton(
                        content="Open video",
                        icon=ft.Icons.OPEN_IN_NEW,
                        url=item.get("url", ""),
                    ),
                ],
            ),
        )
    )


def build_history_block(run: dict[str, Any]) -> ft.Control:
    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text(
                f"Run with new videos: {format_timestamp(run.get('checked_at'))}",
                weight=ft.FontWeight.W_600,
            ),
            ft.Text(f"{run.get('new_count', 0)} new"),
        ],
    )

    items = run.get("items", [])
    cards = [build_video_card(item) for item in items]

    return ft.Card(
        content=ft.Container(
            padding=12,
            content=ft.Column(
                spacing=10,
                controls=[header, *cards] if cards else [header, ft.Text("No items saved in this run.")],
            ),
        )
    )


def build_channel_group(title: str, items: list[dict[str, Any]]) -> ft.Control:
    return ft.Column(
        spacing=8,
        controls=[
            ft.Text(title, size=18, weight=ft.FontWeight.W_600),
            *[build_video_card(item) for item in items],
        ],
    )


def build_current_results(summary: RunSummary) -> ft.Control:
    new_items = summary.items
    if not new_items:
        return ft.Column(
            spacing=10,
            controls=[ft.Text("No new videos found in this run.")],
        )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in new_items:
        grouped[item.get("channel_title", "Unknown channel")].append(item)

    return ft.Column(
        spacing=14,
        controls=[
            build_channel_group(channel_title, grouped[channel_title])
            for channel_title in sorted(grouped.keys(), key=str.lower)
        ],
    )