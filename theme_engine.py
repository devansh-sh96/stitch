"""
theme_engine.py - Dynamic Modern Glassmorphic Theme Engine with Accent Color Customization
Provides live stylesheet generators with soft rounded corners, glow effects, and customizable palettes.
"""

from typing import Dict

THEME_PRESETS = {
    "Panda Jade 🎋": {
        "accent": "#10b981",
        "accent_hover": "#059669",
        "accent_glow": "rgba(16, 185, 129, 0.35)",
        "accent_light": "#6ee7b7",
        "accent_dark": "#064e3b",
        "accent_subtle": "#065f46"
    },
    "Cyber Indigo 🔮": {
        "accent": "#6366f1",
        "accent_hover": "#4f46e5",
        "accent_glow": "rgba(99, 102, 241, 0.35)",
        "accent_light": "#a5b4fc",
        "accent_dark": "#1e1b4b",
        "accent_subtle": "#312e81"
    },
    "Electric Cyan ⚡": {
        "accent": "#06b6d4",
        "accent_hover": "#0891b2",
        "accent_glow": "rgba(6, 182, 212, 0.35)",
        "accent_light": "#67e8f9",
        "accent_dark": "#164e63",
        "accent_subtle": "#155e75"
    },
    "Sakura Pink 🌸": {
        "accent": "#ec4899",
        "accent_hover": "#db2777",
        "accent_glow": "rgba(236, 72, 153, 0.35)",
        "accent_light": "#f472b6",
        "accent_dark": "#500724",
        "accent_subtle": "#831843"
    },
    "Dragon Crimson 🥋": {
        "accent": "#ef4444",
        "accent_hover": "#dc2626",
        "accent_glow": "rgba(239, 68, 68, 0.35)",
        "accent_light": "#fca5a5",
        "accent_dark": "#450a0a",
        "accent_subtle": "#7f1d1d"
    },
    "Sunset Gold 🍯": {
        "accent": "#f59e0b",
        "accent_hover": "#d97706",
        "accent_glow": "rgba(245, 158, 11, 0.35)",
        "accent_light": "#fcd34d",
        "accent_dark": "#451a03",
        "accent_subtle": "#78350f"
    },
}

DEFAULT_THEME = "Panda Jade 🎋"


class ThemeManager:
    """Manages active accent color and generates unified Qt stylesheets."""
    _current_theme_name = DEFAULT_THEME

    @classmethod
    def get_current_theme_name(cls) -> str:
        return cls._current_theme_name

    @classmethod
    def set_theme(cls, theme_name: str):
        if theme_name in THEME_PRESETS:
            cls._current_theme_name = theme_name

    @classmethod
    def get_colors(cls) -> Dict[str, str]:
        return THEME_PRESETS.get(cls._current_theme_name, THEME_PRESETS[DEFAULT_THEME])

    @classmethod
    def get_main_stylesheet(cls) -> str:
        c = cls.get_colors()
        return f"""
            QMainWindow {{
                background-color: #0c0d11;
                color: #f4f4f5;
            }}
            QWidget#DockSidebarLeft {{
                background-color: #121318;
                border-right: 1px solid #1f2029;
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
            }}
            QWidget#CenterHub {{
                background-color: #0c0d11;
            }}
            QWidget#SidebarRight {{
                background-color: #121318;
                border-left: 1px solid #1f2029;
                border-top-right-radius: 16px;
                border-bottom-right-radius: 16px;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QLineEdit {{
                background-color: #171821;
                color: #ffffff;
                border: 1px solid #282a36;
                border-radius: 14px;
                padding: 10px 16px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {c['accent']};
            }}
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                background-color: #171821;
                color: #94a3b8;
                padding: 8px 16px;
                border-radius: 12px;
                margin-right: 6px;
                font-size: 12px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {c['accent']};
                color: #ffffff;
            }}
            QScrollBar:vertical {{
                background: #121318;
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: #282a36;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['accent']};
            }}
            QScrollBar:horizontal {{
                background: #121318;
                height: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:horizontal {{
                background: #282a36;
                border-radius: 3px;
            }}
        """
