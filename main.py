from __future__ import annotations

import flet as ft

from ui.channels_tab import ChannelsTab
from ui.watch_tab import WatchTab
from ui.chron_research_tab import ChronResearchTab
from ui.theme import (
    ACCENT_COLOR,
    BORDER_COLOR,
    TEXT_MUTED_COLOR,
    apply_page_theme,
)

def main(page: ft.Page) -> None:
    apply_page_theme(page)

    watch_tab = WatchTab(page)
    channels_tab = ChannelsTab(
        page=page,
        on_channels_changed=watch_tab.refresh_channel_count,
        on_channel_added=watch_tab.refresh_feeds,
    )
    search_tab = ChronResearchTab(page)

    page.add(
        ft.Tabs(
            length=3,
            selected_index=0,
            animation_duration=200,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        label_color=ACCENT_COLOR,
                        unselected_label_color=TEXT_MUTED_COLOR,
                        indicator_color=ACCENT_COLOR,
                        overlay_color=ft.Colors.TRANSPARENT,
                        divider_color=BORDER_COLOR,
                        tabs=[
                            ft.Tab(label="Watch", icon=ft.Icons.VIDEO_LIBRARY_OUTLINED),
                            ft.Tab(label="Channels", icon=ft.Icons.LIST_ALT_OUTLINED),
                            ft.Tab(label="Search", icon=ft.Icons.HISTORY),
                        ]
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.TabBarView(
                            expand=True,
                            controls=[
                                watch_tab.build(),
                                channels_tab.build(),
                                search_tab.build(),
                            ],
                        ),
                    ),
                ],
            ),
            expand=1,
        )
    )

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")