from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import flet as ft

import channel_store


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

        self.channels_list = ft.Column(spacing=10)

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

        self.channel_status_text = ft.Text("")

        self._content = ft.Container(
            padding=10,
            content=ft.Column(
                spacing=18,
                controls=[
                    ft.Text("Channels", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text("Manage the list of YouTube channels tracked by the app."),
                    self.show_add_channel_button,
                    ft.Row(
                        controls=[
                            self.new_channel_id_field,
                            self.confirm_add_channel_button,
                            self.cancel_add_channel_button,
                        ]
                    ),
                    self.channel_status_text,
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
        self.new_channel_id_field.visible = is_visible
        self.confirm_add_channel_button.visible = is_visible
        self.cancel_add_channel_button.visible = is_visible

        if not is_visible:
            self.new_channel_id_field.value = ""
            self.channel_status_text.value = ""

        self.page.update()

    def open_add_channel_form(self, e: ft.ControlEvent) -> None:
        self.set_add_channel_mode(True)

    def cancel_add_channel_form(self, e: ft.ControlEvent) -> None:
        self.set_add_channel_mode(False)

    def load_channels_view(self) -> None:
        self.channels_list.controls.clear()

        channels = channel_store.list_channels()

        if not channels:
            self.channels_list.controls.append(ft.Text("No channels configured yet."))
            self.page.update()
            return

        for channel in channels:
            self.channels_list.controls.append(
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
            self.channel_status_text.value = f"Could not remove channel: {exc}"
            self.page.update()
            return

        if self.on_channels_changed:
            self.on_channels_changed()

        self.load_channels_view()
        self.channel_status_text.value = "Channel removed successfully."
        self.page.update()

    async def save_new_channel(self, e: ft.ControlEvent) -> None:
        raw_channel_id = (self.new_channel_id_field.value or "").strip()

        if not raw_channel_id:
            self.channel_status_text.value = "Please enter a channel ID."
            self.page.update()
            return

        self.confirm_add_channel_button.disabled = True
        self.cancel_add_channel_button.disabled = True
        self.show_add_channel_button.disabled = True
        self.new_channel_id_field.disabled = True
        self.channel_status_text.value = "Resolving channel..."
        self.page.update()

        try:
            await asyncio.to_thread(channel_store.add_channel_by_id, raw_channel_id)
        except Exception as exc:
            self.channel_status_text.value = f"Could not add channel: {exc}"
            self.confirm_add_channel_button.disabled = False
            self.cancel_add_channel_button.disabled = False
            self.show_add_channel_button.disabled = False
            self.new_channel_id_field.disabled = False
            self.page.update()
            return

        if self.on_channels_changed:
            self.on_channels_changed()

        self.load_channels_view()
        self.set_add_channel_mode(False)

        self.confirm_add_channel_button.disabled = False
        self.cancel_add_channel_button.disabled = False
        self.show_add_channel_button.disabled = False
        self.new_channel_id_field.disabled = False

        self.channel_status_text.value = "Channel added successfully. Creating baseline..."
        self.page.update()

        if self.on_channel_added:
            await self.on_channel_added()

        self.channel_status_text.value = "Channel added successfully."
        self.page.update()