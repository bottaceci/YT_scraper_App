from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any

import flet as ft

import scraper
from models import RunSummary
import storage
from channels import CHANNELS


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


def main(page: ft.Page) -> None:
    page.title = "Channel Watcher"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window.width = 1100
    page.window.height = 800
    page.scroll = ft.ScrollMode.AUTO

    current_results = ft.Column(spacing=14)
    history_results = ft.Column(spacing=12)
    errors_column = ft.Column(spacing=8)

    status_text = ft.Text("Ready to check feeds.")
    summary_text = ft.Text(f"Watching {len(CHANNELS)} channels.")
    data_dir_text = ft.Text(
        f"Data folder: {storage.get_data_dir()}",
        size=12,
        color=ft.Colors.BLUE_GREY_400,
    )

    refresh_button = ft.FilledButton(content="Check feeds now", icon=ft.Icons.REFRESH)
    progress_bar = ft.ProgressBar(width=500, value=0, visible=False)
    progress_text = ft.Text("", size=12, color=ft.Colors.BLUE_GREY_400, visible=False)

    def set_loading(is_loading: bool, message: str | None = None) -> None:
        refresh_button.disabled = is_loading
        progress_bar.visible = is_loading
        progress_text.visible = is_loading

        if is_loading:
            progress_bar.value = 0
            progress_text.value = "Starting feed check..."
        else:
            progress_bar.value = 0
            progress_text.value = ""

        if message is not None:
            status_text.value = message

        page.update()

    def load_history_view() -> None:
        history_results.controls.clear()
        history = storage.load_history_data()
        runs = history.get("runs", [])

        if not runs:
            history_results.controls.append(ft.Text("No successful runs recorded yet."))
            return

        for run in runs:
            history_results.controls.append(build_history_block(run))

    def show_errors(errors: list[dict[str, Any]]) -> None:
        errors_column.controls.clear()

        if not errors:
            return

        errors_column.controls.append(
            ft.Text("Feed warnings", size=18, weight=ft.FontWeight.W_600)
        )

        for error in errors:
            errors_column.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text(
                                    error.get("channel_title", "Unknown channel"),
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text(error.get("error", "Unknown error")),
                            ],
                        ),
                    )
                )
            )

    def show_current_results(summary: RunSummary) -> None:
        current_results.controls.clear()

        new_items = summary.items
        if not new_items:
            current_results.controls.append(ft.Text("No new videos found in this run."))
            return

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in new_items:
            grouped[item.get("channel_title", "Unknown channel")].append(item)

        for channel_title in sorted(grouped.keys(), key=str.lower):
            current_results.controls.append(build_channel_group(channel_title, grouped[channel_title]))

    async def refresh_feeds(e: ft.ControlEvent) -> None:
        set_loading(True, "Checking feeds...")

        current_results.controls.clear()
        current_results.controls.append(ft.Text("Checking channels..."))
        errors_column.controls.clear()
        page.update()

        try:
            run_context = scraper.load_run_context()
            seen_channels = run_context["seen_channels"]
            legacy_seen_by_title = run_context["legacy_seen_by_title"]
            checked_at = run_context["checked_at"]

            total_channels = len(CHANNELS)
            updated_channels: dict[str, Any] = {}
            new_items: list[dict[str, Any]] = []
            errors: list[dict[str, str]] = []

            for index, channel in enumerate(CHANNELS, start=1):
                result = await asyncio.to_thread(
                    scraper.process_channel,
                    channel,
                    seen_channels,
                    legacy_seen_by_title,
                    checked_at,
                )

                updated_channels[result.channel_id] = result.updated_channel_state
                new_items.extend(result.new_items)

                if result.error:
                    errors.append(result.error)

                progress_bar.value = index / total_channels if total_channels else 0
                progress_text.value = f"Processed {index}/{total_channels}: {result.channel_title}"
                status_text.value = "Checking feeds..."
                page.update()

            summary = scraper.finalize_run(
                updated_channels=updated_channels,
                new_items=new_items,
                errors=errors,
                checked_at=checked_at,
                channel_count=total_channels,
                used_legacy_dict=bool(legacy_seen_by_title),
            )

        except Exception as exc:
            summary_text.value = f"Watching {len(CHANNELS)} channels."
            errors_column.controls.clear()
            current_results.controls.clear()
            current_results.controls.append(
                ft.Text("The run failed before results could be loaded.")
            )
            set_loading(False, f"Run failed: {exc}")
            return

        show_current_results(summary)
        show_errors(summary.errors)
        load_history_view()

        new_count = summary.new_count
        error_count = len(summary.errors)

        status_parts = []
        if new_count:
            status_parts.append(f"Found {new_count} new video(s).")
        else:
            status_parts.append("No new videos found.")

        if error_count:
            status_parts.append(f"{error_count} feed warning(s).")

        if summary.used_legacy_dict:
            status_parts.append("Imported your old dict.txt format for comparison on this run.")

        summary_text.value = (
            f"Last check: {format_timestamp(summary.checked_at)} | "
            f"Channels checked: {summary.channel_count} | "
            f"New videos: {summary.new_count} | "
            f"Warnings: {error_count}"
        )

        set_loading(False, " ".join(status_parts))

    refresh_button.on_click = refresh_feeds

    current_results.controls.append(ft.Text("Click 'Check feeds now' to run the scraper."))
    load_history_view()

    page.add(
        ft.Column(
            spacing=18,
            controls=[
                ft.Text("Channel Watcher", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Minimal Flet app for checking new videos across your saved channel list."),
                data_dir_text,
                ft.Row(spacing=12, controls=[refresh_button]),
                progress_bar,
                progress_text,
                status_text,
                summary_text,
                ft.Divider(),
                ft.Text("This run", size=22, weight=ft.FontWeight.W_600),
                current_results,
                errors_column,
                ft.Divider(),
                ft.Text("Recent successful runs (last 5)", size=22, weight=ft.FontWeight.W_600),
                history_results,
            ],
        )
    )


if __name__ == "__main__":
    ft.run(main)