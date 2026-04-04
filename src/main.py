from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any

import flet as ft

import scraper
from models import RunSummary, ChannelState
import storage
import channel_store


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
    channels = channel_store.list_channels()

    channels_list = ft.Column(spacing=10)

    show_add_channel_button = ft.FilledButton(
        content="Add channel",
        icon=ft.Icons.ADD,
    )

    new_channel_id_field = ft.TextField(
        label="YouTube channel ID",
        hint_text="Paste the channel ID here",
        visible=False,
        expand=True,
    )

    confirm_add_channel_button = ft.FilledButton(
        content="Save",
        icon=ft.Icons.SAVE,
        visible=False,
    )

    cancel_add_channel_button = ft.TextButton(
        content="Cancel",
        visible=False,
    )

    channel_status_text = ft.Text("")

    status_text = ft.Text("Ready to check feeds.")
    summary_text = ft.Text(f"Watching {len(channels)} channels.")
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

    def set_add_channel_mode(is_visible: bool) -> None:
        new_channel_id_field.visible = is_visible
        confirm_add_channel_button.visible = is_visible
        cancel_add_channel_button.visible = is_visible

        if not is_visible:
            new_channel_id_field.value = ""
            channel_status_text.value = ""

        page.update()


    def open_add_channel_form(e: ft.ControlEvent) -> None:
        set_add_channel_mode(True)


    def cancel_add_channel_form(e: ft.ControlEvent) -> None:
        set_add_channel_mode(False)


    def load_channels_view() -> None:
        channels_list.controls.clear()

        channels = channel_store.list_channels()

        if not channels:
            channels_list.controls.append(ft.Text("No channels configured yet."))
            page.update()
            return

        for channel in channels:
            channels_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(channel.label, weight=ft.FontWeight.W_600),
                                        ft.Text(
                                            channel.channel_id,
                                            size=12,
                                            color=ft.Colors.BLUE_GREY_400,
                                        ),
                                    ],
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    tooltip="Remove channel",
                                    on_click=lambda e, channel_id=channel.channel_id: delete_channel(channel_id),
                                ),
                            ],
                        ),
                    )
                )
            )

        page.update()

    def refresh_channel_cache() -> None:
        nonlocal channels
        channels = channel_store.list_channels()

    def delete_channel(channel_id: str) -> None:
        try:
            channel_store.remove_channel(channel_id)
        except Exception as exc:
            channel_status_text.value = f"Could not remove channel: {exc}"
            page.update()
            return

        refresh_channel_cache()
        load_channels_view()
        channel_status_text.value = "Channel removed successfully."
        page.update()
    
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

            total_channels = len(channels)
            updated_channels: dict[str, ChannelState] = {}
            new_items: list[dict[str, Any]] = []
            errors: list[dict[str, str]] = []

            for index, channel in enumerate(channels, start=1):
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
            summary_text.value = f"Watching {len(channels)} channels."
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

    async def save_new_channel(e: ft.ControlEvent) -> None:
        raw_channel_id = (new_channel_id_field.value or "").strip()

        if not raw_channel_id:
            channel_status_text.value = "Please enter a channel ID."
            page.update()
            return

        confirm_add_channel_button.disabled = True
        cancel_add_channel_button.disabled = True
        show_add_channel_button.disabled = True
        new_channel_id_field.disabled = True
        channel_status_text.value = "Resolving channel..."
        page.update()

        try:
            await asyncio.to_thread(channel_store.add_channel_by_id, raw_channel_id)
        except Exception as exc:
            channel_status_text.value = f"Could not add channel: {exc}"
            confirm_add_channel_button.disabled = False
            cancel_add_channel_button.disabled = False
            show_add_channel_button.disabled = False
            new_channel_id_field.disabled = False
            page.update()
            return

        refresh_channel_cache()
        load_channels_view()
        set_add_channel_mode(False)

        confirm_add_channel_button.disabled = False
        cancel_add_channel_button.disabled = False
        show_add_channel_button.disabled = False
        new_channel_id_field.disabled = False

        channel_status_text.value = "Channel added successfully. Creating baseline..."
        page.update()

        await refresh_feeds(e)

        channel_status_text.value = "Channel added successfully."
        page.update()

    refresh_button.on_click = refresh_feeds
    show_add_channel_button.on_click = open_add_channel_form
    cancel_add_channel_button.on_click = cancel_add_channel_form
    confirm_add_channel_button.on_click = save_new_channel

    current_results.controls.append(ft.Text("Click 'Check feeds now' to run the scraper."))
    load_history_view()
    load_channels_view()

    watch_tab_content = ft.Container(
        padding=10,
        content=ft.Column(
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

    channels_tab_content = ft.Container(
        padding=10,
        content=ft.Column(
            spacing=18,
            controls=[
                ft.Text("Channels", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Manage the list of YouTube channels tracked by the app."),
                show_add_channel_button,
                ft.Row(
                    controls=[
                        new_channel_id_field,
                        confirm_add_channel_button,
                        cancel_add_channel_button,
                    ]
                ),
                channel_status_text,
                ft.Divider(),
                channels_list,
            ],
        ),
    )

    page.add(
        ft.Tabs(
            length=2,
            selected_index=0,
            animation_duration=200,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Watch", icon=ft.Icons.VIDEO_LIBRARY_OUTLINED),
                            ft.Tab(label="Channels", icon=ft.Icons.LIST_ALT_OUTLINED),
                        ]
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.TabBarView(
                            expand=True,
                            controls=[
                                watch_tab_content,
                                channels_tab_content,
                            ],
                        ),
                    ),
                ],
            ),
            expand=1,
        )
    )


if __name__ == "__main__":
    ft.run(main)