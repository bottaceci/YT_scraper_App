from __future__ import annotations

import flet as ft

from ui.channels_tab import ChannelsTab
from ui.watch_tab import WatchTab
from ui.theme import apply_page_theme

def main(page: ft.Page) -> None:
    apply_page_theme(page)

    watch_tab = WatchTab(page)
    channels_tab = ChannelsTab(
        page=page,
        on_channels_changed=watch_tab.refresh_channel_count,
        on_channel_added=watch_tab.refresh_feeds,
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
                                watch_tab.build(),
                                channels_tab.build(),
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