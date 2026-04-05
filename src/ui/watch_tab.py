from __future__ import annotations

import asyncio
from typing import Any

import flet as ft

import channel_store
import scraper
import storage
from models import ChannelState, RunSummary
from ui.components import (
    build_current_results,
    build_history_block,
    build_page_header,
    build_section_header,
    format_timestamp,
)
from ui.theme import (
    SECTION_PADDING,
    SPACE_SM,
    SPACE_MD,
    SPACE_LG,
    TEXT_XS,
    TEXT_MD,
    TEXT_LG,
    TEXT_XL,
    TEXT_MUTED_COLOR,
)


class WatchTab:
    def __init__(self, page: ft.Page) -> None:
        self.page = page

        self.current_results = ft.Column(spacing=SPACE_MD)
        self.history_results = ft.Column(spacing=SPACE_SM)
        self.errors_column = ft.Column(spacing=SPACE_SM)

        self.status_text = ft.Text("Ready to check feeds.")
        self.summary_text = ft.Text(f"Watching {len(self.get_channels())} channels.")
        self.data_dir_text = ft.Text(
            f"Data folder: {storage.get_data_dir()}",
            size=TEXT_XS,
            color=TEXT_MUTED_COLOR,
        )

        self.refresh_button = ft.FilledButton(
            content="Check feeds now",
            icon=ft.Icons.REFRESH,
            on_click=self.refresh_feeds,
        )

        self.progress_bar = ft.ProgressBar(width=500, value=0, visible=False)
        self.progress_text = ft.Text("", size=TEXT_XS, color=TEXT_MUTED_COLOR, visible=False)

        self.current_results.controls.append(ft.Text("Click 'Check feeds now' to run the scraper."))
        self.load_history_view()

        self._content = ft.Container(
            padding=SECTION_PADDING,
            content=ft.Column(
                spacing=SPACE_LG,
                controls=[
                    build_page_header(
                        title="Channel Watcher",
                        subtitle="Check new uploads across your saved YouTube channels.",
                    ),
                    self.data_dir_text,
                    ft.Row(spacing=SPACE_SM, controls=[self.refresh_button]),
                    self.progress_bar,
                    self.progress_text,
                    self.status_text,
                    self.summary_text,
                    ft.Divider(),
                    build_section_header("This run"),
                    self.current_results,
                    self.errors_column,
                    ft.Divider(),
                    build_section_header("Recent successful runs (last 5)"),
                    self.history_results,
                ],
            ),
        )

    def build(self) -> ft.Control:
        return self._content

    def get_channels(self):
        return channel_store.list_channels()

    def refresh_channel_count(self) -> None:
        self.summary_text.value = f"Watching {len(self.get_channels())} channels."
        self.page.update()

    def set_loading(self, is_loading: bool, message: str | None = None) -> None:
        self.refresh_button.disabled = is_loading
        self.progress_bar.visible = is_loading
        self.progress_text.visible = is_loading

        if is_loading:
            self.progress_bar.value = 0
            self.progress_text.value = "Starting feed check..."
        else:
            self.progress_bar.value = 0
            self.progress_text.value = ""

        if message is not None:
            self.status_text.value = message

        self.page.update()

    def load_history_view(self) -> None:
        self.history_results.controls.clear()
        history = storage.load_history_data()
        runs = history.get("runs", [])

        if not runs:
            self.history_results.controls.append(ft.Text("No successful runs recorded yet."))
            return

        for run in runs:
            self.history_results.controls.append(build_history_block(run))

    def show_errors(self, errors: list[dict[str, Any]]) -> None:
        self.errors_column.controls.clear()

        if not errors:
            return

        self.errors_column.controls.append(
            build_section_header("Feed warnings")
        )

        for error in errors:
            self.errors_column.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=SECTION_PADDING,
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

    def show_current_results(self, summary: RunSummary) -> None:
        self.current_results.controls.clear()
        self.current_results.controls.append(build_current_results(summary))

    async def refresh_feeds(self, e: ft.ControlEvent | None = None) -> None:
        channels = self.get_channels()

        self.set_loading(True, "Checking feeds...")

        self.current_results.controls.clear()
        self.current_results.controls.append(ft.Text("Checking channels..."))
        self.errors_column.controls.clear()
        self.page.update()

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

                self.progress_bar.value = index / total_channels if total_channels else 0
                self.progress_text.value = f"Processed {index}/{total_channels}: {result.channel_title}"
                self.status_text.value = "Checking feeds..."
                self.page.update()

            summary = scraper.finalize_run(
                updated_channels=updated_channels,
                new_items=new_items,
                errors=errors,
                checked_at=checked_at,
                channel_count=total_channels,
                used_legacy_dict=bool(legacy_seen_by_title),
            )

        except Exception as exc:
            self.summary_text.value = f"Watching {len(channels)} channels."
            self.errors_column.controls.clear()
            self.current_results.controls.clear()
            self.current_results.controls.append(
                ft.Text("The run failed before results could be loaded.")
            )
            self.set_loading(False, f"Run failed: {exc}")
            return

        self.show_current_results(summary)
        self.show_errors(summary.errors)
        self.load_history_view()

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

        self.summary_text.value = (
            f"Last check: {format_timestamp(summary.checked_at)} | "
            f"Channels checked: {summary.channel_count} | "
            f"New videos: {summary.new_count} | "
            f"Warnings: {error_count}"
        )

        self.set_loading(False, " ".join(status_parts))