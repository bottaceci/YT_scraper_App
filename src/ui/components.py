from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

import flet as ft

from models import RunSummary
from ui.theme import (
    CARD_PADDING,
    FONT_DISPLAY,
    SPACE_XS,
    SPACE_SM,
    SPACE_MD,
    SPACE_LG,
    TEXT_XS,
    TEXT_MD,
    TEXT_LG,
    TEXT_XL,
    TEXT_MUTED_COLOR,
    TEXT_SOFT_COLOR,
)

def build_page_header(
    title: str,
    subtitle: str,
    right_content: ft.Control | None = None,
) -> ft.Control:
    title_block = ft.Column(
        spacing=SPACE_XS,
        controls=[
            ft.Text(
                title,
                size=TEXT_XL,
                font_family=FONT_DISPLAY,
            ),
            ft.Text(
                subtitle,
                size=TEXT_MD,
                color=TEXT_SOFT_COLOR,
            ),
        ],
    )

    if right_content is None:
        content = title_block
    else:
        content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(expand=True, content=title_block),
                right_content,
            ],
        )

    return ft.Container(
        padding=ft.Padding.only(bottom=SPACE_SM),
        content=content,
    )


def build_section_header(title: str) -> ft.Control:
    return ft.Text(
        title,
        size=TEXT_LG,
        font_family=FONT_DISPLAY,
    )

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
            padding=CARD_PADDING,
            content=ft.Column(
                spacing=SPACE_SM,
                controls=[
                    ft.Text(
                        item.get("title", "Untitled video"),
                        size=TEXT_MD,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Text(
                        " • ".join(subtitle_parts),
                        size=TEXT_XS,
                        color=TEXT_MUTED_COLOR,
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
            padding=CARD_PADDING,
            content=ft.Column(
                spacing=SPACE_MD,
                controls=[header, *cards] if cards else [header, ft.Text("No items saved in this run.")],
            ),
        )
    )


def build_channel_group(title: str, items: list[dict[str, Any]]) -> ft.Control:
    return ft.Column(
        spacing=SPACE_SM,
        controls=[
            ft.Text(title, size=TEXT_LG, weight=ft.FontWeight.W_600),
            *[build_video_card(item) for item in items],
        ],
    )


def build_current_results(summary: RunSummary) -> ft.Control:
    new_items = summary.items
    if not new_items:
        return ft.Column(
            spacing=SPACE_SM,
            controls=[ft.Text("No new videos found in this run.")],
        )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in new_items:
        grouped[item.get("channel_title", "Unknown channel")].append(item)

    return ft.Column(
        spacing=SPACE_MD,
        controls=[
            build_channel_group(channel_title, grouped[channel_title])
            for channel_title in sorted(grouped.keys(), key=str.lower)
        ],
    )