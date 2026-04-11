from __future__ import annotations

import asyncio
from dataclasses import asdict, is_dataclass
from typing import Any

import flet as ft

from youtube_search import main as run_youtube_search
from ui.theme import (
    SECTION_PADDING,
    SPACE_SM,
    SPACE_MD,
    SPACE_LG,
    TEXT_XS,
    TEXT_MUTED_COLOR,
    PRIMARY_BUTTON_STYLE,
    SUBTLE_BUTTON_STYLE,
)
from ui.components import (
    build_empty_state,
    build_error_block,
    build_info_block,
    build_page_header,
    build_section_header,
    build_video_card,
)

DEFAULT_TARGET = 20
DEFAULT_MAX_PAGES = 5
DEFAULT_MIN_SECONDS = 120
DEFAULT_CANDIDATE_LIMIT = 200


class ChronResearchTab:
    def __init__(self, page: ft.Page) -> None:
        self.page = page

        self.results_list = ft.Column(spacing=SPACE_MD)
        self.search_feedback = ft.Column(spacing=SPACE_SM)

        self.query_field = ft.TextField(
            label="Search...",
            hint_text="Write your query here",
            expand=True,
            on_submit=self.run_search,
        )

        self.search_button = ft.IconButton(
            icon=ft.Icons.SEARCH,
            tooltip="Search",
            on_click=self.run_search,
        )

        self.cancel_search_button = ft.TextButton(
            content="Cancel",
            style=SUBTLE_BUTTON_STYLE,
            on_click=self.cancel_search_form,
        )

        self.advanced_options_button = ft.FilledButton(
            content="Advanced Options",
            icon=ft.Icons.ADD,
            style=PRIMARY_BUTTON_STYLE,
            on_click=self.open_advanced_options_form,
        )

        self.num_videos_field = ft.TextField(
            label="Num. videos",
            value=str(DEFAULT_TARGET),
            visible=False,
            expand=True,
        )

        self.max_pages_field = ft.TextField(
            label="Max pages",
            value=str(DEFAULT_MAX_PAGES),
            visible=False,
            expand=True,
        )

        self.min_sec_field = ft.TextField(
            label="Min. duration",
            value=str(DEFAULT_MIN_SECONDS),
            visible=False,
            expand=True,
        )

        self.max_candidates_field = ft.TextField(
            label="Max. candidates",
            value=str(DEFAULT_CANDIDATE_LIMIT),
            visible=False,
            expand=True,
        )

        self.advanced_options_form = ft.Card(
            visible=False,
            content=ft.Container(
                padding=SECTION_PADDING,
                content=ft.Column(
                    spacing=SPACE_SM,
                    controls=[
                        ft.Text("Advanced Options", weight=ft.FontWeight.W_600),
                        ft.Text(
                            "Finetune these options not to waste resources",
                            size=TEXT_XS,
                            color=TEXT_MUTED_COLOR,
                        ),
                        ft.Row(
                            spacing=SPACE_SM,
                            controls=[
                                self.num_videos_field,
                                self.max_pages_field,
                                self.min_sec_field,
                                self.max_candidates_field,
                            ],
                        ),
                    ],
                ),
            ),
        )

        self.search_form = ft.Card(
            content=ft.Container(
                padding=SECTION_PADDING,
                content=ft.Column(
                    spacing=SPACE_SM,
                    controls=[
                        ft.Row(
                            spacing=SPACE_SM,
                            controls=[
                                self.query_field,
                                self.search_button,
                                self.cancel_search_button,
                            ],
                        ),
                        self.advanced_options_button,
                    ],
                ),
            ),
        )

        self._content = ft.Container(
            expand=True,
            padding=SECTION_PADDING,
            content=ft.Column(
                expand=True,
                spacing=SPACE_LG,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        padding=ft.Padding.only(right=16),
                        content=ft.Column(
                            spacing=SPACE_LG,
                            controls=[
                                build_page_header(
                                    title="Chronological Research",
                                    subtitle="Look up YouTube videos in chronological order.",
                                ),
                                self.search_form,
                                self.advanced_options_form,
                                self.search_feedback,
                                ft.Divider(),
                                self.results_list,
                            ],
                        ),
                    ),
                ],
            ),
        )

        self.show_idle_feedback()

    def build(self) -> ft.Control:
        return self._content

    def set_advanced_options_mode(self, is_visible: bool) -> None:
        self.advanced_options_form.visible = is_visible
        self.num_videos_field.visible = is_visible
        self.max_pages_field.visible = is_visible
        self.min_sec_field.visible = is_visible
        self.max_candidates_field.visible = is_visible
        self.advanced_options_button.visible = not is_visible
        self.page.update()

    def set_loading(self, is_loading: bool) -> None:
        self.query_field.disabled = is_loading
        self.search_button.disabled = is_loading
        self.cancel_search_button.disabled = is_loading
        self.advanced_options_button.disabled = is_loading
        self.num_videos_field.disabled = is_loading
        self.max_pages_field.disabled = is_loading
        self.min_sec_field.disabled = is_loading
        self.max_candidates_field.disabled = is_loading

    def clear_feedback(self) -> None:
        self.search_feedback.controls.clear()

    def clear_results(self) -> None:
        self.results_list.controls.clear()

    def show_idle_feedback(self) -> None:
        self.clear_feedback()
        self.search_feedback.controls.append(
            build_info_block(
                title="Look something up!",
                message="Run a search to see matching YouTube videos here.",
                icon=ft.Icons.MANAGE_SEARCH,
            )
        )

    def show_progress_feedback(self) -> None:
        self.clear_feedback()
        self.search_feedback.controls.append(
            build_info_block(
                title="Search in progress...",
                message="Querying YouTube and building your result list.",
                icon=ft.Icons.HOURGLASS_TOP,
            )
        )

    def show_error_feedback(self, message: str) -> None:
        self.clear_feedback()
        self.search_feedback.controls.append(
            build_error_block(
                title="Search failed",
                message=message,
            )
        )

    def _read_positive_int(self, field: ft.TextField, default: int) -> int:
        raw = (field.value or "").strip()

        if not raw:
            field.value = str(default)
            return default

        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{field.label} must be an integer.") from exc

        if value <= 0:
            raise ValueError(f"{field.label} must be greater than zero.")

        field.value = str(value)
        return value

    def _reset_form(self) -> None:
        self.query_field.value = ""
        self.num_videos_field.value = str(DEFAULT_TARGET)
        self.max_pages_field.value = str(DEFAULT_MAX_PAGES)
        self.min_sec_field.value = str(DEFAULT_MIN_SECONDS)
        self.max_candidates_field.value = str(DEFAULT_CANDIDATE_LIMIT)

    def _normalize_video_item(self, item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            return item

        if is_dataclass(item):
            data = asdict(item)
            if isinstance(data, dict):
                return data

        return {
            "channel_id": getattr(item, "channel_id", ""),
            "channel_title": getattr(item, "channel_title", "Unknown channel"),
            "title": getattr(item, "title", "Untitled video"),
            "url": getattr(item, "url", ""),
            "published": getattr(item, "published", None),
        }

    def show_results(self, result: Any) -> None:
        self.clear_results()

        items = getattr(result, "items", []) or []

        if not items:
            query = getattr(result, "query", "your query")
            self.results_list.controls.append(
                build_empty_state(
                    title="No results found",
                    message=f"No videos matched '{query}' with the current settings.",
                    icon=ft.Icons.SEARCH_OFF,
                )
            )
            return

        self.results_list.controls.append(
            build_section_header(f"Results ({len(items)})")
        )

        self.results_list.controls.extend(
            build_video_card(self._normalize_video_item(item))
            for item in items
        )

    def open_advanced_options_form(self, e: ft.ControlEvent) -> None:
        self.set_advanced_options_mode(True)

    def cancel_search_form(self, e: ft.ControlEvent) -> None:
        self._reset_form()
        self.set_advanced_options_mode(False)
        self.clear_results()
        self.show_idle_feedback()
        self.page.update()

    async def run_search(self, e: ft.ControlEvent | None = None) -> None:
        query = (self.query_field.value or "").strip()

        if not query:
            self.clear_results()
            self.show_error_feedback("Insert a search query first.")
            self.page.update()
            return

        try:
            target = self._read_positive_int(self.num_videos_field, DEFAULT_TARGET)
            max_pages = self._read_positive_int(self.max_pages_field, DEFAULT_MAX_PAGES)
            min_seconds = self._read_positive_int(self.min_sec_field, DEFAULT_MIN_SECONDS)
            candidate_limit = self._read_positive_int(
                self.max_candidates_field,
                DEFAULT_CANDIDATE_LIMIT,
            )
        except ValueError as exc:
            self.clear_results()
            self.show_error_feedback(str(exc))
            self.page.update()
            return

        self.clear_results()
        self.set_loading(True)
        self.show_progress_feedback()
        self.page.update()

        try:
            result = await asyncio.to_thread(
                run_youtube_search,
                query=query,
                target=target,
                max_pages=max_pages,
                min_seconds=min_seconds,
                candidate_limit=candidate_limit,
                debug=False,
            )
        except Exception as exc:
            self.clear_results()
            self.show_error_feedback(str(exc))
            self.set_loading(False)
            self.page.update()
            return

        self.show_results(result)
        self.clear_feedback()
        self.set_loading(False)
        self.page.update()