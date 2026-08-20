"""
ui.py - Ultra-Modern Clean Minimalist Workspace Hub & Desktop Companion (Panda Po Edition)
Features:
- Left Dock: Icon-only running app toggles + App Usage & Screen Time Tracker box
- Center Hub: Minimal App Icon + App Name only launch cards with soft rounded corners
- Right Panel: Panda Po Mascot, Stitch Groq Llama Assistant, and Live Accent Color Customizer
- Desktop Pet: Floating Panda Po with hover excitement & horizontal slide shelf dock
"""

import os
import sys
import threading
from typing import List, Dict, Any, Optional

from PySide6 import QtCore, QtGui, QtWidgets

# Backend & Modules
from getting_data import (
    get_running_applications,
    get_installed_applications,
    launch_application,
    AppIconCache,
    AppUsageTracker,
)
from pixel_pet import PixelBearWidget, StitchDesktopPet
from spotlight_tray import StitchSpotlightTray
from theme_engine import ThemeManager, THEME_PRESETS
from stich_agent import (
    generate_text,
    load_needs_data,
    load_appset_data,
    log_user_need,
    add_appset_recommendation,
)


class RunningIconToggle(QtWidgets.QFrame):
    """Icon-only toggle button for currently running applications on the left dock."""
    def __init__(self, app_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.app_info = app_info
        self.setFixedSize(52, 52)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        title = app_info.get("title") or app_info.get("name", "App")
        pname = app_info.get("process_name", "")
        mem = app_info.get("mem_mb", 0)
        self.setToolTip(f"<b>{title}</b><br><span style='color:#94a3b8;'>{pname} • {mem} MB</span><br><span style='color:#10b981;'>Click to Focus</span>")

        self.apply_style()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        # App Icon
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setScaledContents(True)

        icon_path = app_info.get("exe") or app_info.get("process_name")
        icon = AppIconCache.get_instance().get_icon_for_path(icon_path)
        self.icon_label.setPixmap(icon.pixmap(32, 32))
        layout.addWidget(self.icon_label)

    def apply_style(self):
        c = ThemeManager.get_colors()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #171821;
                border: 1.5px solid #282a36;
                border-radius: 14px;
            }}
            QFrame:hover {{
                background-color: #212330;
                border: 1.5px solid {c['accent']};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            hwnd = self.app_info.get("hwnd")
            exe = self.app_info.get("exe") or self.app_info.get("process_name")
            launch_application(exe, hwnd=hwnd)
            event.accept()
        else:
            super().mousePressEvent(event)


class MinimalAppCard(QtWidgets.QFrame):
    """Minimal Card featuring App Icon + App Name Only with soft corners."""
    def __init__(self, app_data: Dict[str, Any], is_running: bool = False, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.is_running = is_running
        self.setFixedHeight(56)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        self.apply_style()

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        # App Icon
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(34, 34)
        self.icon_label.setScaledContents(True)

        icon_path = app_data.get("icon_path") or app_data.get("target")
        icon = AppIconCache.get_instance().get_icon_for_path(icon_path)
        self.icon_label.setPixmap(icon.pixmap(34, 34))
        layout.addWidget(self.icon_label)

        # App Name Only
        name = app_data.get("name", "App")
        self.title_label = QtWidgets.QLabel(name)
        self.title_label.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Minimal Launch Toggle Button
        c = ThemeManager.get_colors()
        self.btn_toggle = QtWidgets.QPushButton("● Launch" if not is_running else "● Focus")
        self.btn_toggle.setFixedSize(70, 30)
        self.btn_toggle.setCursor(QtCore.Qt.PointingHandCursor)
        btn_bg = c["accent_dark"] if not is_running else c["accent"]
        btn_color = c["accent_light"] if not is_running else "#ffffff"

        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_color};
                border: 1px solid {c['accent']};
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
                color: #ffffff;
            }}
        """)
        self.btn_toggle.clicked.connect(self._launch)
        layout.addWidget(self.btn_toggle)

    def apply_style(self):
        c = ThemeManager.get_colors()
        border_color = c["accent"] if self.is_running else "#282a36"
        bg_color = "#171821" if not self.is_running else "#162822"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 14px;
            }}
            QFrame:hover {{
                background-color: #212330;
                border: 1px solid {c['accent']};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._launch()
            event.accept()
        else:
            super().mousePressEvent(event)

    def _launch(self):
        target = self.app_data.get("target", "")
        launch_application(target)


class StitchWorkspaceWindow(QtWidgets.QMainWindow):
    """
    Complete Ultra-Modern Workspace Hub with Panda Po Mascot,
    Minimal Icon Dock, App Screen Time Tracker, and Live Theme Accent Engine.
    """
    data_refreshed_signal = QtCore.Signal(object, object, object)
    chat_reply_signal = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stitch Workspace Hub & Desktop Companion (Panda Po)")
        self.resize(1260, 780)
        self.setMinimumSize(1040, 660)

        # Data stores
        self.all_installed_apps: List[Dict[str, Any]] = []
        self.running_apps_list: List[Dict[str, Any]] = []
        self.active_category_filter = "All"

        # Connect Signals
        self.data_refreshed_signal.connect(self._on_data_refreshed)
        self.chat_reply_signal.connect(self._on_chat_reply_received)

        # Desktop Pet & Horizontal Slide Shelf
        self.spotlight_tray = StitchSpotlightTray()
        self.spotlight_tray.open_hub_requested.connect(self._restore_and_show)
        self.desktop_pet = StitchDesktopPet(spotlight_tray=self.spotlight_tray)
        self.desktop_pet.open_dashboard_requested.connect(self._restore_and_show)

        # Central Widget
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.main_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(12)

        # Build Panels
        self.build_left_dock()
        self.build_center_hub()
        self.build_right_panel()

        # Apply Initial Global Stylesheet
        self.apply_theme_stylesheet()

        # Background Timers (Running apps & Foreground time tracking)
        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self._trigger_background_refresh)
        self.refresh_timer.start(3000)

        self.usage_timer = QtCore.QTimer(self)
        self.usage_timer.timeout.connect(self._tick_usage)
        self.usage_timer.start(2000)

        self._initial_load()

    def apply_theme_stylesheet(self):
        self.setStyleSheet(ThemeManager.get_main_stylesheet())
        self.spotlight_tray.apply_theme()

    def _tick_usage(self):
        AppUsageTracker.get_instance().tick_foreground()

    # ==============================================================
    # 1. LEFT DOCK: ICON-ONLY RUNNING APPS + USAGE TIME TRACKER BOX
    # ==============================================================
    def build_left_dock(self):
        self.left_dock = QtWidgets.QWidget(self.centralwidget)
        self.left_dock.setObjectName("DockSidebarLeft")
        self.left_dock.setFixedWidth(200)

        layout = QtWidgets.QVBoxLayout(self.left_dock)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        # Header Title
        h_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("⚡ RUNNING")
        title.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;")
        h_row.addWidget(title)

        self.running_badge = QtWidgets.QLabel("0")
        c = ThemeManager.get_colors()
        self.running_badge.setStyleSheet(f"""
            background-color: {c['accent']};
            color: #000000;
            border-radius: 8px;
            padding: 1px 6px;
            font-size: 10px;
            font-weight: bold;
        """)
        h_row.addWidget(self.running_badge)
        h_row.addStretch()
        layout.addLayout(h_row)

        # Scrollable Icon Toggles Dock
        self.dock_scroll = QtWidgets.QScrollArea()
        self.dock_scroll.setWidgetResizable(True)
        self.dock_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.dock_container = QtWidgets.QWidget()
        self.dock_layout = QtWidgets.QVBoxLayout(self.dock_container)
        self.dock_layout.setContentsMargins(0, 0, 0, 0)
        self.dock_layout.setSpacing(8)
        self.dock_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        self.dock_scroll.setWidget(self.dock_container)
        layout.addWidget(self.dock_scroll, stretch=1)

        # ==========================================================
        # 📊 APP USAGE & SCREEN TIME TRACKER BOX
        # ==========================================================
        self.usage_box = QtWidgets.QFrame()
        self.usage_box.setStyleSheet("""
            QFrame {
                background-color: #171821;
                border: 1px solid #282a36;
                border-radius: 14px;
                padding: 8px;
            }
        """)
        usage_layout = QtWidgets.QVBoxLayout(self.usage_box)
        usage_layout.setContentsMargins(8, 8, 8, 8)
        usage_layout.setSpacing(6)

        u_header = QtWidgets.QHBoxLayout()
        u_title = QtWidgets.QLabel("📊 App Screen Time")
        u_title.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold;")
        u_header.addWidget(u_title)
        usage_layout.addLayout(u_header)

        self.usage_list_layout = QtWidgets.QVBoxLayout()
        self.usage_list_layout.setSpacing(4)
        usage_layout.addLayout(self.usage_list_layout)

        layout.addWidget(self.usage_box)
        self.main_layout.addWidget(self.left_dock)

    def _render_usage_box(self, top_apps: List[Dict[str, Any]]):
        while self.usage_list_layout.count():
            item = self.usage_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        c = ThemeManager.get_colors()
        for item in top_apps[:4]:
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(4)

            name_lbl = QtWidgets.QLabel(item["name"][:10])
            name_lbl.setStyleSheet("color: #e2e8f0; font-size: 10px; font-weight: 600;")
            row.addWidget(name_lbl)
            row.addStretch()

            dur_lbl = QtWidgets.QLabel(item["duration_str"])
            dur_lbl.setStyleSheet(f"color: {c['accent_light']}; font-size: 10px; font-weight: bold;")
            row.addWidget(dur_lbl)

            self.usage_list_layout.addLayout(row)

            # Mini Progress Bar
            pbar = QtWidgets.QProgressBar()
            pbar.setFixedHeight(3)
            pbar.setTextVisible(False)
            pbar.setValue(item["percent"])
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #282a36;
                    border: none;
                    border-radius: 1px;
                }}
                QProgressBar::chunk {{
                    background-color: {c['accent']};
                    border-radius: 1px;
                }}
            """)
            self.usage_list_layout.addWidget(pbar)

    # ==============================================================
    # 2. CENTER HUB: MINIMAL APP CARDS (ICON + NAME ONLY)
    # ==============================================================
    def build_center_hub(self):
        self.center_hub = QtWidgets.QWidget(self.centralwidget)
        self.center_hub.setObjectName("CenterHub")

        layout = QtWidgets.QVBoxLayout(self.center_hub)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Header Bar
        top_bar = QtWidgets.QHBoxLayout()
        title_box = QtWidgets.QVBoxLayout()
        title_box.setSpacing(2)

        main_title = QtWidgets.QLabel("Workspace Hub")
        main_title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 800;")
        title_box.addWidget(main_title)

        sub_desc = QtWidgets.QLabel("Single-click to open or toggle any application")
        sub_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        title_box.addWidget(sub_desc)
        top_bar.addLayout(title_box)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Search Bar with soft rounded pill corners
        self.app_search_box = QtWidgets.QLineEdit()
        self.app_search_box.setPlaceholderText("🔍 Type to search any app, tool, or shortcut...")
        self.app_search_box.textChanged.connect(self._render_app_grid)
        layout.addWidget(self.app_search_box)

        # Category Filter Tabs (Pill Buttons)
        self.cat_filter_row = QtWidgets.QHBoxLayout()
        self.cat_filter_row.setSpacing(6)

        categories = ["All", "Development", "Productivity", "Media & Audio", "Communication", "AI & Tools", "Tools"]
        self.cat_buttons = {}
        for cat in categories:
            btn = QtWidgets.QPushButton(cat)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            btn.setCheckable(True)
            if cat == "All":
                btn.setChecked(True)

            self._style_cat_button(btn, cat == "All")
            btn.clicked.connect(lambda _, c=cat: self._set_category_filter(c))
            self.cat_buttons[cat] = btn
            self.cat_filter_row.addWidget(btn)

        self.cat_filter_row.addStretch()
        layout.addLayout(self.cat_filter_row)

        # Scrollable App Cards Grid
        self.grid_scroll = QtWidgets.QScrollArea()
        self.grid_scroll.setWidgetResizable(True)

        self.grid_container = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.grid_scroll.setWidget(self.grid_container)
        layout.addWidget(self.grid_scroll, stretch=1)

        self.main_layout.addWidget(self.center_hub, stretch=2)

    def _style_cat_button(self, btn: QtWidgets.QPushButton, is_checked: bool):
        c = ThemeManager.get_colors()
        bg = c["accent"] if is_checked else "#171821"
        color = "#ffffff" if is_checked else "#94a3b8"
        border = c["accent"] if is_checked else "#282a36"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: #ffffff;
                border: 1px solid {c['accent']};
            }}
        """)

    # ==============================================================
    # 3. RIGHT PANEL: PANDA PO MASCOT + ACCENT SELECTOR + STITCH AI
    # ==============================================================
    def build_right_panel(self):
        self.right_panel = QtWidgets.QWidget(self.centralwidget)
        self.right_panel.setObjectName("SidebarRight")
        self.right_panel.setFixedWidth(360)

        layout = QtWidgets.QVBoxLayout(self.right_panel)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(12)

        # Mascot Header Card (Panda Po)
        self.mascot_card = QtWidgets.QFrame()
        c = ThemeManager.get_colors()
        self.mascot_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent_dark']}, stop:1 #171821);
                border: 1.5px solid {c['accent']};
                border-radius: 16px;
                padding: 8px;
            }}
        """)
        mascot_layout = QtWidgets.QHBoxLayout(self.mascot_card)
        mascot_layout.setContentsMargins(6, 6, 6, 6)
        mascot_layout.setSpacing(10)

        # Animated Pixel Panda Po Mascot
        self.mascot_avatar = PixelBearWidget(pixel_size=3, parent=self.right_panel)
        mascot_layout.addWidget(self.mascot_avatar)

        mascot_text = QtWidgets.QVBoxLayout()
        mascot_text.setSpacing(2)

        m_title = QtWidgets.QLabel("Stitch • Panda Po 🐼")
        m_title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        mascot_text.addWidget(m_title)

        m_sub = QtWidgets.QLabel("Kung Fu Workspace Advisor")
        m_sub.setStyleSheet(f"color: {c['accent_light']}; font-size: 10px;")
        mascot_text.addWidget(m_sub)

        # Toggle Desktop Pet Mode Button
        self.btn_toggle_pet = QtWidgets.QPushButton("🐾 Launch Desktop Pet")
        self.btn_toggle_pet.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_toggle_pet.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: #000000;
                border-radius: 10px;
                padding: 5px 10px;
                font-size: 11px;
                font-weight: bold;
                margin-top: 4px;
            }}
            QPushButton:hover {{ background-color: {c['accent_light']}; }}
        """)
        self.btn_toggle_pet.clicked.connect(self._toggle_desktop_pet_mode)
        mascot_text.addWidget(self.btn_toggle_pet)

        mascot_layout.addLayout(mascot_text)
        layout.addWidget(self.mascot_card)

        # Accent Color Switcher Row
        theme_row = QtWidgets.QHBoxLayout()
        t_label = QtWidgets.QLabel("🎨 Accent:")
        t_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        theme_row.addWidget(t_label)

        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(list(THEME_PRESETS.keys()))
        self.theme_combo.setCurrentText(ThemeManager.get_current_theme_name())
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #171821;
                color: #ffffff;
                border: 1px solid #282a36;
                border-radius: 10px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo, stretch=1)
        layout.addLayout(theme_row)

        # Tabs: Chat, Needs, Appset
        self.right_tabs = QtWidgets.QTabWidget()

        # Tab 1: Chat
        chat_tab = QtWidgets.QWidget()
        chat_layout = QtWidgets.QVBoxLayout(chat_tab)
        chat_layout.setContentsMargins(0, 6, 0, 0)
        chat_layout.setSpacing(6)

        self.chat_display = QtWidgets.QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #171821;
                color: #f4f4f5;
                border: 1px solid #282a36;
                border-radius: 12px;
                padding: 8px;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        chat_layout.addWidget(self.chat_display)

        # Chat Input Row
        input_row = QtWidgets.QHBoxLayout()
        self.chat_input = QtWidgets.QLineEdit()
        self.chat_input.setPlaceholderText("Ask Stitch or state a problem...")
        self.chat_input.returnPressed.connect(self._on_send_chat)
        input_row.addWidget(self.chat_input)

        self.btn_send = QtWidgets.QPushButton("Send")
        self.btn_send.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: #000000;
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {c['accent_light']}; }}
        """)
        self.btn_send.clicked.connect(self._on_send_chat)
        input_row.addWidget(self.btn_send)

        chat_layout.addLayout(input_row)
        self.right_tabs.addTab(chat_tab, "💬 Chat")

        # Tab 2: Needs Log
        self.needs_tab = QtWidgets.QWidget()
        needs_layout = QtWidgets.QVBoxLayout(self.needs_tab)
        needs_layout.setContentsMargins(0, 6, 0, 0)
        self.needs_display = QtWidgets.QTextEdit()
        self.needs_display.setReadOnly(True)
        self.needs_display.setStyleSheet("background-color: #171821; color: #f4f4f5; border: 1px solid #282a36; border-radius: 12px; padding: 8px; font-size: 11px;")
        needs_layout.addWidget(self.needs_display)
        self.right_tabs.addTab(self.needs_tab, "📋 Needs")

        # Tab 3: Appset
        self.appset_tab = QtWidgets.QWidget()
        appset_layout = QtWidgets.QVBoxLayout(self.appset_tab)
        appset_layout.setContentsMargins(0, 6, 0, 0)
        self.appset_display = QtWidgets.QTextEdit()
        self.appset_display.setReadOnly(True)
        self.appset_display.setStyleSheet("background-color: #171821; color: #f4f4f5; border: 1px solid #282a36; border-radius: 12px; padding: 8px; font-size: 11px;")
        appset_layout.addWidget(self.appset_display)
        self.right_tabs.addTab(self.appset_tab, "⭐ Appset")

        layout.addWidget(self.right_tabs)
        self.main_layout.addWidget(self.right_panel)

    def _on_theme_changed(self, theme_name: str):
        ThemeManager.set_theme(theme_name)
        self.apply_theme_stylesheet()

        # Update dynamic cards and buttons
        c = ThemeManager.get_colors()
        self.running_badge.setStyleSheet(f"background-color: {c['accent']}; color: #000000; border-radius: 8px; padding: 1px 6px; font-size: 10px; font-weight: bold;")
        self.mascot_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent_dark']}, stop:1 #171821);
                border: 1.5px solid {c['accent']};
                border-radius: 16px;
                padding: 8px;
            }}
        """)
        self.btn_toggle_pet.setStyleSheet(f"background-color: {c['accent']}; color: #000000; border-radius: 10px; padding: 5px 10px; font-size: 11px; font-weight: bold; margin-top: 4px;")
        self.btn_send.setStyleSheet(f"background-color: {c['accent']}; color: #000000; border-radius: 12px; padding: 8px 14px; font-weight: bold;")

        for cat, btn in self.cat_buttons.items():
            self._style_cat_button(btn, cat == self.active_category_filter)

        self._render_app_grid()

    # ==============================================================
    # LOGIC & DATA HANDLING
    # ==============================================================
    def _initial_load(self):
        self.chat_display.append(
            "🐼 <b>Stitch (Panda Po):</b> Skadoosh! Welcome to your clean workspace hub. "
            "Single-click any card to launch, check your screen time on the left, or launch the desktop pet!"
        )
        self._refresh_needs_tab()
        self._refresh_appset_tab()
        self._trigger_background_refresh()

    def _trigger_background_refresh(self):
        def worker():
            running = get_running_applications()
            installed = get_installed_applications()
            usage = AppUsageTracker.get_instance().get_top_used_apps(4)
            self.data_refreshed_signal.emit(running, installed, usage)

        threading.Thread(target=worker, daemon=True).start()

    def _on_data_refreshed(self, running: List[Dict[str, Any]], installed: List[Dict[str, Any]], usage: List[Dict[str, Any]]):
        self.running_apps_list = running
        self.all_installed_apps = installed
        self.running_badge.setText(str(len(running)))

        # 1. Update Left Dock Icon Toggles
        while self.dock_layout.count():
            item = self.dock_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for app in running[:14]:
            toggle = RunningIconToggle(app)
            self.dock_layout.addWidget(toggle)

        # 2. Update Usage Screen Time Box
        self._render_usage_box(usage)

        # 3. Update Center Grid
        self._render_app_grid()

    def _render_app_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = self.app_search_box.text().strip().lower()
        running_names = {a.get("process_name", "").lower() for a in self.running_apps_list}

        filtered = []
        for app in self.all_installed_apps:
            if self.active_category_filter != "All" and app.get("category") != self.active_category_filter:
                continue
            if query:
                name_match = query in app.get("name", "").lower()
                tag_match = query in app.get("tags", "").lower()
                cat_match = query in app.get("category", "").lower()
                if not (name_match or tag_match or cat_match):
                    continue

            filtered.append(app)

        for idx, app in enumerate(filtered[:36]):
            target = app.get("target", "").lower()
            is_active = any(r in target for r in running_names) if running_names else False
            card = MinimalAppCard(app, is_running=is_active)
            row = idx // 2
            col = idx % 2
            self.grid_layout.addWidget(card, row, col)

    def _set_category_filter(self, category: str):
        self.active_category_filter = category
        for cat, btn in self.cat_buttons.items():
            btn.setChecked(cat == category)
            self._style_cat_button(btn, cat == category)
        self._render_app_grid()

    def _on_send_chat(self):
        msg = self.chat_input.text().strip()
        if not msg:
            return

        self.chat_input.clear()
        self.chat_display.append(f"<br><b>You:</b> {msg}")
        self.mascot_avatar.set_excited(True)

        def worker():
            reply = generate_text(msg)
            self.chat_reply_signal.emit(reply)

        threading.Thread(target=worker, daemon=True).start()

    def _on_chat_reply_received(self, reply: str):
        self.mascot_avatar.set_excited(False)
        self.chat_display.append(f"🐼 <b>Stitch (Po):</b> {reply}<br>")
        self._refresh_needs_tab()
        self._refresh_appset_tab()

    def _refresh_needs_tab(self):
        data = load_needs_data()
        problems = data.get("problems", [])
        html = f"<b>Persistent Needs ({len(problems)})</b><br><hr>"
        for p in reversed(problems):
            html += f"• <b>[{p.get('category', 'General')}] {p.get('title', '')}</b><br>"
            if p.get("recommended_apps"):
                html += f"  <span style='color:#10b981;'>Apps: {', '.join(p['recommended_apps'])}</span><br>"
            html += "<br>"
        self.needs_display.setHtml(html)

    def _refresh_appset_tab(self):
        data = load_appset_data()
        recs = data.get("recommendations", [])
        html = f"<b>App Recommendations ({len(recs)})</b><br><hr>"
        for r in recs:
            html += f"• <b>{r.get('name')}</b> <span style='color:#10b981;'>({r.get('category')})</span><br>"
            html += f"  <span style='color:#94a3b8;'>{r.get('description', '')}</span><br><br>"
        self.appset_display.setHtml(html)

    def _toggle_desktop_pet_mode(self):
        if self.desktop_pet.isVisible():
            self.desktop_pet.hide()
            self.btn_toggle_pet.setText("🐾 Launch Desktop Pet")
        else:
            self.desktop_pet.show()
            self.desktop_pet.raise_()
            self.btn_toggle_pet.setText("🐾 Dismiss Desktop Pet")

    def _restore_and_show(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Stitch Workspace Hub")
    window = StitchWorkspaceWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()