from __future__ import annotations

import flet as ft

APP_TITLE = "Channel Watcher"

WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 840
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 680

PAGE_PADDING = 20
CONTENT_MAX_WIDTH = 1100

SPACE_XS = 6
SPACE_SM = 10
SPACE_MD = 14
SPACE_LG = 18
SPACE_XL = 24
SPACE_2XL = 32

RADIUS_SM = 10
RADIUS_MD = 14
RADIUS_LG = 18

TEXT_XS = 12
TEXT_SM = 14
TEXT_MD = 16
TEXT_LG = 32
TEXT_XL = 46

CARD_PADDING = 12
SECTION_PADDING = 10

TEXT_MUTED_COLOR = ft.Colors.BLUE_GREY_400
TEXT_SOFT_COLOR = ft.Colors.BLUE_GREY_300

SURFACE_COLOR = ft.Colors.with_opacity(0.03, ft.Colors.WHITE)
SURFACE_ELEVATED_COLOR = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
BORDER_COLOR = ft.Colors.with_opacity(0.08, ft.Colors.WHITE)

SUCCESS_COLOR = ft.Colors.GREEN_300
WARNING_COLOR = ft.Colors.AMBER_300
DANGER_COLOR = ft.Colors.RED_300

FONT_BODY = "Inter"
FONT_DISPLAY = "PixelifySans"


def apply_page_theme(page: ft.Page) -> None:
    page.title = APP_TITLE
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = PAGE_PADDING
    page.scroll = ft.ScrollMode.AUTO

    page.window.width = WINDOW_WIDTH
    page.window.height = WINDOW_HEIGHT
    page.window.min_width = WINDOW_MIN_WIDTH
    page.window.min_height = WINDOW_MIN_HEIGHT

    page.fonts = {
        "Inter": "assets/fonts/Inter/Inter_18pt-Regular.ttf",
        "Inter-SemiBold": "assets/fonts/Inter/Inter_18pt-SemiBold.ttf",
        "PixelifySans": "assets/fonts/PixelifySans/PixelifySans-Regular.ttf",
        "PixelifySans-SemiBold": "assets/fonts/PixelifySans/PixelifySans-SemiBold.ttf",
    }

    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        font_family=FONT_BODY,
        visual_density=ft.VisualDensity.COMPACT,
        card_theme=ft.CardTheme(
            color=SURFACE_ELEVATED_COLOR,
            margin=0,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_MD),
        ),
        divider_theme=ft.DividerTheme(color=BORDER_COLOR, thickness=1),
    )