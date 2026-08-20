"""
spotlight_tray.py - Sleek Horizontal Slide-In Shelf & Quick App Dock
Anchored directly to the left of Panda Po (Stitch).
Features a compact search box, horizontal row of app icon toggles,
soft rounded glassmorphic corners, and smooth horizontal slide animations.
"""

import threading
from typing import List, Dict, Any, Optional
from PySide6 import QtCore, QtGui, QtWidgets

from getting_data import get_installed_applications, launch_application, AppIconCache, get_running_statuses
from stich_agent import generate_text
from theme_engine import ThemeManager


class HorizontalAppToggle(QtWidgets.QFrame):
    """Compact 1-Click App Icon Button with soft rounded corners and running status glow."""
    launched = QtCore.Signal(str)

    def __init__(self, app_data: Dict[str, Any], is_running: bool = False, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.is_running = is_running
        self.setFixedSize(46, 46)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        name = app_data.get("name", "App")
        cat = app_data.get("category", "General")
        self.setToolTip(f"<b>{name}</b><br><span style='color:#94a3b8;'>{cat}</span>" + ("<br><span style='color:#10b981;'>● Running</span>" if is_running else ""))

        self._apply_style()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setScaledContents(True)

        icon_path = app_data.get("icon_path") or app_data.get("target")
        icon = AppIconCache.get_instance().get_icon_for_path(icon_path)
        self.icon_label.setPixmap(icon.pixmap(28, 28))
        layout.addWidget(self.icon_label)

    def _apply_style(self):
        c = ThemeManager.get_colors()
        border = c["accent"] if self.is_running else "#282a36"
        bg = "#1f2029" if not self.is_running else "#162b24"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1.5px solid {border};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: #282a36;
                border: 1.5px solid {c['accent']};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            target = self.app_data.get("target", "")
            launch_application(target)
            self.launched.emit(target)
            event.accept()
        else:
            super().mousePressEvent(event)


class StitchSpotlightTray(QtWidgets.QWidget):
    """
    Floating Horizontal Shelf Dock that slides in directly to the left of Panda Po.
    """
    open_hub_requested = QtCore.Signal()
    ai_reply_signal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_apps: List[Dict[str, Any]] = []

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setFixedHeight(68)
        self.setFixedWidth(560)

        self.ai_reply_signal.connect(self._on_ai_reply)

        # Main Layout
        outer_layout = QtWidgets.QHBoxLayout(self)
        outer_layout.setContentsMargins(4, 4, 4, 4)

        self.container = QtWidgets.QWidget(self)
        self.container.setObjectName("ShelfContainer")
        self.shelf_layout = QtWidgets.QHBoxLayout(self.container)
        self.shelf_layout.setContentsMargins(12, 6, 12, 6)
        self.shelf_layout.setSpacing(10)
        outer_layout.addWidget(self.container)

        # 1. Compact Search Box on the Left
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search apps...")
        self.search_box.setFixedWidth(145)
        self.search_box.textChanged.connect(self._on_filter_changed)
        self.search_box.returnPressed.connect(self._on_search_submitted)
        self.shelf_layout.addWidget(self.search_box)

        # Divider
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.VLine)
        divider.setStyleSheet("background-color: #282a36; width: 1px;")
        self.shelf_layout.addWidget(divider)

        # 2. Horizontal Scroll Area for App Toggles
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.dock_content = QtWidgets.QWidget()
        self.dock_layout = QtWidgets.QHBoxLayout(self.dock_content)
        self.dock_layout.setContentsMargins(0, 0, 0, 0)
        self.dock_layout.setSpacing(8)
        self.dock_layout.addStretch()

        self.scroll_area.setWidget(self.dock_content)
        self.shelf_layout.addWidget(self.scroll_area, stretch=1)

        # 3. Quick Action Buttons
        self.btn_dash = QtWidgets.QPushButton("🖥️")
        self.btn_dash.setFixedSize(36, 36)
        self.btn_dash.setToolTip("Open Full Workspace Hub")
        self.btn_dash.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_dash.clicked.connect(self._on_open_hub)
        self.shelf_layout.addWidget(self.btn_dash)

        self.btn_close = QtWidgets.QPushButton("✕")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setToolTip("Close Shelf")
        self.btn_close.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.hide)
        self.shelf_layout.addWidget(self.btn_close)

        # Slide Animation Engine
        self.slide_anim = QtCore.QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(220)
        self.slide_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        self.apply_theme()
        self.refresh_apps()

    def apply_theme(self):
        c = ThemeManager.get_colors()
        self.container.setStyleSheet(f"""
            QWidget#ShelfContainer {{
                background-color: rgba(18, 19, 24, 0.96);
                border: 1.5px solid {c['accent']};
                border-radius: 20px;
            }}
            QLineEdit {{
                background-color: #171821;
                color: #ffffff;
                border: 1px solid #282a36;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {c['accent']};
            }}
            QPushButton {{
                background-color: #1f2029;
                color: #f4f4f5;
                border: 1px solid #282a36;
                border-radius: 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
                color: #ffffff;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
        """)

    def refresh_apps(self):
        self.all_apps = get_installed_applications()
        self._populate_dock(self.all_apps)

    def _populate_dock(self, apps: List[Dict[str, Any]]):
        while self.dock_layout.count() > 1:
            item = self.dock_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for app in apps[:16]:
            toggle = HorizontalAppToggle(app)
            toggle.launched.connect(lambda _: self.hide())
            self.dock_layout.insertWidget(self.dock_layout.count() - 1, toggle)

    def _on_filter_changed(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate_dock(self.all_apps)
            return

        filtered = [
            app for app in self.all_apps
            if query in app.get("name", "").lower() or query in app.get("tags", "").lower() or query in app.get("category", "").lower()
        ]
        self._populate_dock(filtered)

    def _on_search_submitted(self):
        query = self.search_box.text().strip()
        if not query:
            return

        exact_matches = [a for a in self.all_apps if a.get("name", "").lower() == query.lower()]
        if exact_matches:
            launch_application(exact_matches[0]["target"])
            self.hide()
            return

        # Direct prompt query
        def run_agent():
            reply = generate_text(query)
            self.ai_reply_signal.emit(reply)

        threading.Thread(target=run_agent, daemon=True).start()

    def _on_ai_reply(self, reply: str):
        self.search_box.setToolTip(reply[:200])

    def _on_open_hub(self):
        self.hide()
        self.open_hub_requested.emit()

    def position_to_left_of(self, pet_rect: QtCore.QRect):
        target_x = max(10, pet_rect.left() - self.width() - 12)
        target_y = pet_rect.top() + (pet_rect.height() - self.height()) // 2
        self.move(target_x, target_y)

    def toggle_shelf(self, pet_rect: QtCore.QRect):
        if self.isVisible():
            self.hide()
        else:
            self.apply_theme()
            target_x = max(10, pet_rect.left() - self.width() - 12)
            target_y = pet_rect.top() + (pet_rect.height() - self.height()) // 2

            # Start slightly further to the right for a smooth horizontal slide effect
            start_x = pet_rect.left() - self.width() + 30
            self.move(start_x, target_y)

            self.search_box.clear()
            self.refresh_apps()
            self.show()
            self.raise_()
            self.activateWindow()
            self.search_box.setFocus()

            # Smooth horizontal slide animation
            self.slide_anim.stop()
            self.slide_anim.setStartValue(QtCore.QPoint(start_x, target_y))
            self.slide_anim.setEndValue(QtCore.QPoint(target_x, target_y))
            self.slide_anim.start()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)
