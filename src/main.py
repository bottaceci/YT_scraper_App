from __future__ import annotations

import flet as ft

from ui.channels_tab import ChannelsTab
from ui.watch_tab import WatchTab

def main(page: ft.Page) -> None:
    page.title = "Channel Watcher"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window.width = 1100
    page.window.height = 800
    page.scroll = ft.ScrollMode.AUTO

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