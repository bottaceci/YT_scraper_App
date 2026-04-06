from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import flet as ft

import channel_store
from ui.theme import (
    SECTION_PADDING,
    SPACE_SM,
    SPACE_LG,
    TEXT_XS,
    TEXT_XL,
    TEXT_MUTED_COLOR,
)
from ui.components import (
    build_empty_state,
    build_error_block,
    build_info_block,
    build_page_header,
    build_success_block,
)


class ChannelsTab:
    def __init__(
        self,
        page: ft.Page,
        on_channels_changed: Callable[[], None] | None = None,
        on_channel_added: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self.page = page
        self.on_channels_changed = on_channels_changed
        self.on_channel_added = on_channel_added

        self.channels_list = ft.Column(spacing=SPACE_SM)

        self.show_add_channel_button = ft.FilledButton(
            content="Add channel",
            icon=ft.Icons.ADD,
            on_click=self.open_add_channel_form,
        )

        self.new_channel_id_field = ft.TextField(
            label="YouTube channel ID",
            hint_text="Paste the channel ID here",
            visible=False,
            expand=True,
        )

        self.confirm_add_channel_button = ft.FilledButton(
            content="Save",
            icon=ft.Icons.SAVE,
            visible=False,
            on_click=self.save_new_channel,
        )

        self.cancel_add_channel_button = ft.TextButton(
            content="Cancel",
            visible=False,
            on_click=self.cancel_add_channel_form,
        )

        self.add_channel_form = ft.Card(
            visible=False,
            content=ft.Container(
                padding=SECTION_PADDING,
                content=ft.Column(
                    spacing=SPACE_SM,
                    controls=[
                        ft.Text("Add a channel", weight=ft.FontWeight.W_600),
                        ft.Text(
                            "Paste a YouTube channel ID. The app will resolve the title automatically and create the initial baseline.",
                            size=TEXT_XS,
                            color=TEXT_MUTED_COLOR,
                        ),
                        ft.Row(
                            spacing=SPACE_SM,
                            controls=[
                                self.new_channel_id_field,
                                self.confirm_add_channel_button,
                                self.cancel_add_channel_button,
                            ],
                        ),
                    ],
                ),
            ),
        )

        self.channel_feedback = ft.Column(spacing=SPACE_SM)

        self._content = ft.Container(
            padding=SECTION_PADDING,
            content=ft.Column(
                spacing=SPACE_LG,
                controls=[
                    build_page_header(
                        title="Channels",
                        subtitle="Manage the YouTube channels tracked by the app.",
                    ),
                    self.show_add_channel_button,
                    self.add_channel_form,
                    self.channel_feedback,
                    ft.Divider(),
                    self.channels_list,
                ],
            ),
        )

        self.load_channels_view()

    def build(self) -> ft.Control:
        return self._content

    def refresh(self) -> None:
        self.load_channels_view()

    def set_add_channel_mode(self, is_visible: bool) -> None:
        self.add_channel_form.visible = is_visible
        self.new_channel_id_field.visible = is_visible
        self.confirm_add_channel_button.visible = is_visible
        self.cancel_add_channel_button.visible = is_visible

        self.show_add_channel_button.visible = not is_visible

        if not is_visible:
            self.new_channel_id_field.value = ""
            self.clear_feedback()

        self.page.update()

    async def open_add_channel_form(self, e: ft.ControlEvent) -> None:
        self.set_add_channel_mode(True)
        await self.new_channel_id_field.focus()

    def cancel_add_channel_form(self, e: ft.ControlEvent) -> None:
        self.set_add_channel_mode(False)

    def load_channels_view(self) -> None:
        self.channels_list.controls.clear()

        channels = channel_store.list_channels()

        if not channels:
            self.channels_list.controls.append(
                build_empty_state(
                    title="No channels yet",
                    message="Add a YouTube channel ID to start tracking uploads.",
                    icon=ft.Icons.SUBSCRIPTIONS_OUTLINED,
                )
            )
            self.page.update()
            return

        for channel in channels:
            self.channels_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=SECTION_PADDING,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(channel.label, weight=ft.FontWeight.W_600),
                                        ft.Text(
                                            channel.channel_id,
                                            size=TEXT_XS,
                                            color=TEXT_MUTED_COLOR,
                                        ),
                                    ],
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    tooltip="Remove channel",
                                    on_click=lambda e, channel_id=channel.channel_id: self.delete_channel(channel_id),
                                ),
                            ],
                        ),
                    )
                )
            )

        self.page.update()

    def delete_channel(self, channel_id: str) -> None:
        try:
            channel_store.remove_channel(channel_id)
        except Exception as exc:
            self.show_error("Could not remove channel", str(exc))
            return

        if self.on_channels_changed:
            self.on_channels_changed()

        self.load_channels_view()
        self.show_success("Channel removed", "The channel was removed successfully.")

    async def save_new_channel(self, e: ft.ControlEvent) -> None:
        raw_channel_id = (self.new_channel_id_field.value or "").strip()

        if not raw_channel_id:
            self.show_error("Missing channel ID", "Please enter a YouTube channel ID before saving.")
            return

        self.confirm_add_channel_button.disabled = True
        self.cancel_add_channel_button.disabled = True
        self.show_add_channel_button.disabled = True
        self.new_channel_id_field.disabled = True
        self.show_info(
            "Resolving channel",
            "Looking up the channel title and preparing the initial baseline.",
        )

        try:
            await asyncio.to_thread(channel_store.add_channel_by_id, raw_channel_id)
        except Exception as exc:
            self.confirm_add_channel_button.disabled = False
            self.cancel_add_channel_button.disabled = False
            self.show_add_channel_button.disabled = False
            self.new_channel_id_field.disabled = False
            self.show_error("Could not add channel", str(exc))
            return

        if self.on_channels_changed:
            self.on_channels_changed()

        self.load_channels_view()
        self.set_add_channel_mode(False)

        self.confirm_add_channel_button.disabled = False
        self.cancel_add_channel_button.disabled = False
        self.show_add_channel_button.disabled = False
        self.new_channel_id_field.disabled = False

        self.show_info(
            "Channel added",
            "The channel was saved successfully. Creating the initial baseline now.",
        )

        if self.on_channel_added:
            await self.on_channel_added()

        self.show_success(
            "Channel added",
            "The channel was added successfully and the initial baseline has been created.",
        )

    def clear_feedback(self) -> None:
        self.channel_feedback.controls.clear()


    def show_info(self, title: str, message: str) -> None:
        self.channel_feedback.controls.clear()
        self.channel_feedback.controls.append(build_info_block(title, message))
        self.page.update()


    def show_success(self, title: str, message: str) -> None:
        self.channel_feedback.controls.clear()
        self.channel_feedback.controls.append(build_success_block(title, message))
        self.page.update()


    def show_error(self, title: str, message: str) -> None:
        self.channel_feedback.controls.clear()
        self.channel_feedback.controls.append(build_error_block(title, message))
        self.page.update()