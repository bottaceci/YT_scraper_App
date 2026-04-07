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

BG_COLOR = "#0b1020"
SURFACE_COLOR = "#121a2b"
SURFACE_ELEVATED_COLOR = "#182235"
BORDER_COLOR = "#27324a"

TEXT_COLOR = "#f3f7ff"
TEXT_MUTED_COLOR = "#8fa3bf"
TEXT_SOFT_COLOR = "#b8c7dc"

ACCENT_COLOR = "#37f3c8"
ACCENT_STRONG_COLOR = "#19c7ff"

SUCCESS_COLOR = "#57e389"
WARNING_COLOR = "#ffb84d"
DANGER_COLOR = "#ff6b81"

FONT_BODY = "Inter"
FONT_DISPLAY = "PixelifySans"

PRIMARY_BUTTON_STYLE = ft.ButtonStyle(
    bgcolor=ACCENT_COLOR,
    color=BG_COLOR,
    padding=ft.Padding.symmetric(horizontal=18, vertical=14),
    shape=ft.RoundedRectangleBorder(radius=12),
)

SUBTLE_BUTTON_STYLE = ft.ButtonStyle(
    color=ACCENT_STRONG_COLOR,
    padding=ft.Padding.symmetric(horizontal=14, vertical=12),
    shape=ft.RoundedRectangleBorder(radius=12),
)


def apply_page_theme(page: ft.Page) -> None:
    page.title = APP_TITLE
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = PAGE_PADDING
    #page.scroll = ft.ScrollMode.HIDDEN
    page.bgcolor = BG_COLOR

    page.window.width = WINDOW_WIDTH
    page.window.height = WINDOW_HEIGHT
    page.window.min_width = WINDOW_MIN_WIDTH
    page.window.min_height = WINDOW_MIN_HEIGHT

    page.fonts = {
        "Inter": "fonts/Inter/Inter_18pt-Regular.ttf",
        "Inter-SemiBold": "fonts/Inter/Inter_18pt-SemiBold.ttf",
        "PixelifySans": "fonts/PixelifySans/PixelifySans-Regular.ttf",
        "PixelifySans-SemiBold": "fonts/PixelifySans/PixelifySans-SemiBold.ttf",
    }

    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ACCENT_COLOR,
            secondary=ACCENT_STRONG_COLOR,
            surface=SURFACE_COLOR,
            error=DANGER_COLOR,
            on_primary=BG_COLOR,
            on_secondary=BG_COLOR,
            on_surface=TEXT_COLOR,
            on_error=TEXT_COLOR,
        ),
        font_family=FONT_BODY,
        visual_density=ft.VisualDensity.COMPACT,
        scaffold_bgcolor=BG_COLOR,
        card_theme=ft.CardTheme(
            color=SURFACE_ELEVATED_COLOR,
            margin=0,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_MD),
        ),
        divider_theme=ft.DividerTheme(
            color=BORDER_COLOR, 
            thickness=1,
        ),
    )