"""
pixel_pet.py - Pixelated Panda Po Mascot (Kung Fu Panda) & Floating Desktop Pet Overlay
Features custom pixel art for Panda Po, kung fu animations, idle breathing,
blinking, hover excitement physics, floating particles (hearts, stars, dumplings, bamboo),
and horizontal shelf trigger.
"""

import math
import random
from typing import Optional, List, Tuple
from PySide6 import QtCore, QtGui, QtWidgets


# Pixel Palette for Panda Po (Kung Fu Panda)
PALETTE = {
    ".": None,                    # Transparent
    "B": QtGui.QColor("#0f172a"),  # Deep Black / Outline / Ears
    "E": QtGui.QColor("#1e293b"),  # Dark Eye Patches / Arms
    "W": QtGui.QColor("#ffffff"),  # Pure White Fur / Belly
    "G": QtGui.QColor("#e2e8f0"),  # Light Grey Fur Shadow
    "J": QtGui.QColor("#10b981"),  # Jade Green Kung Fu Eye Iris
    "P": QtGui.QColor("#34d399"),  # Bright Jade Sparkle
    "N": QtGui.QColor("#020617"),  # Nose & Pupils
    "R": QtGui.QColor("#f43f5e"),  # Rosy Cheek Blush
    "Y": QtGui.QColor("#f59e0b"),  # Golden Kung Fu Headband / Belt
    "H": QtGui.QColor("#fb7185"),  # Pink Heart
    "S": QtGui.QColor("#facc15"),  # Star Gold
    "D": QtGui.QColor("#fef08a"),  # Dumpling Yellow-White
    "Z": QtGui.QColor("#059669"),  # Bamboo Green
}

# 16x16 Pixel Art Matrices for Panda Po
PANDA_IDLE_1 = [
    "....BB....BB....",
    "...BEEB..BEEB...",
    "..BEEEEBBEEEEB..",
    "..BWWWWWWWWWWBB.",
    ".BWYYYYYYYYYYWB.",
    ".BWEEWWWWWWEEWB.",
    ".BWEJNWWWWEJNWGB",
    ".BWENPWWWENPWGB.",
    ".BWWNNWWWWNNWGB.",
    ".BWRRWWNNWWRRGB.",
    ".BWWWWWNNWWWWGB.",
    "..BEEWWWWWWEEB..",
    ".BEEBWWWWWWBEGB.",
    ".BEBWYYYYYYWBGB.",
    "..BB.BEEEEB.BB..",
    "......BBBB......",
]

PANDA_IDLE_2 = [
    "....BB....BB....",
    "...BEEB..BEEB...",
    "..BEEEEBBEEEEB..",
    "..BWWWWWWWWWWBB.",
    ".BWYYYYYYYYYYWB.",
    ".BWEEWWWWWWEEWB.",
    ".BWEJNWWWWEJNWGB",
    ".BWENPWWWENPWGB.",
    ".BWWNNWWWWNNWGB.",
    ".BWRRWWNNWWRRGB.",
    ".BWWWWWNNWWWWGB.",
    "..BEEWWWWWWEEB..",
    ".BEEBWWWWWWBEGB.",
    ".BEBWYYYYYYWBGB.",
    "..BB..BBBB..BB..",
    "................",
]

PANDA_BLINK = [
    "....BB....BB....",
    "...BEEB..BEEB...",
    "..BEEEEBBEEEEB..",
    "..BWWWWWWWWWWBB.",
    ".BWYYYYYYYYYYWB.",
    ".BWEEWWWWWWEEWB.",
    ".BWEWWWWWWWWEWGB",
    ".BWENWWWWWENWGB.",
    ".BWWNNWWWWNNWGB.",
    ".BWRRWWNNWWRRGB.",
    ".BWWWWWNNWWWWGB.",
    "..BEEWWWWWWEEB..",
    ".BEEBWWWWWWBEGB.",
    ".BEBWYYYYYYWBGB.",
    "..BB.BEEEEB.BB..",
    "......BBBB......",
]

PANDA_EXCITED_1 = [
    "...BBB....BBB...",
    "..BEEEB..BEEEB..",
    ".BEEEEEBBEEEEB..",
    ".BWWWWWWWWWWWWBB",
    "BWYYYYYYYYYYYYWB",
    "BWEEWWWWWWWWEEWB",
    "BWEPPNWWWWWEPPNB",
    "BWENPNWWWWWENPNB",
    "BWWNNWWNNWWNNWGB",
    "BWRRRWWNNWWRRRGB",
    ".BWWWWWWWWWWWWGB",
    "..BEEBWWWWWBEEB.",
    ".BEEBWYYYYYWBEEB",
    "..BB.BEEEEB..BB.",
    "......BBBB......",
    "................",
]

PANDA_EXCITED_2 = [
    "...BBB....BBB...",
    "..BEEEB..BEEEB..",
    ".BEEEEEBBEEEEB..",
    ".BWWWWWWWWWWWWBB",
    "BWYYYYYYYYYYYYWB",
    "BWEEWWWWWWWWEEWB",
    "BWEPPNWWWWWEPPNB",
    "BWENPNWWWWWENPNB",
    "BWWNNWWNNWWNNWGB",
    "BWRRRWWNNWWRRRGB",
    ".BWWWWWWWWWWWWGB",
    ".BEEBWWWWWWWBEEB",
    "..BB.BWYYYYWB.BB",
    ".....BEEEEB.....",
    "......BBBB......",
    "................",
]


class PandaParticle:
    """Floating particle spawned during excitement (Hearts, Stars, Dumplings, Bamboo)."""
    def __init__(self, x: float, y: float, ptype: str = "heart"):
        self.x = x
        self.y = y
        self.ptype = ptype
        self.vx = random.uniform(-0.9, 0.9)
        self.vy = random.uniform(-2.5, -1.3)
        self.alpha = 255
        self.size = random.randint(4, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha = max(0, self.alpha - 8)

    def is_alive(self) -> bool:
        return self.alpha > 0


class PixelBearWidget(QtWidgets.QWidget):
    """
    Renders Panda Po (Kung Fu Panda) with high-DPI procedural pixel art,
    idle stance breathing, blinking, kung-fu hover celebrations, and custom scaling.
    """
    clicked = QtCore.Signal()
    hover_changed = QtCore.Signal(bool)

    def __init__(self, pixel_size: int = 5, parent=None):
        super().__init__(parent)
        self.pixel_size = pixel_size
        self.state = "idle"  # 'idle', 'excited', 'blink'
        self.frame_index = 0
        self.is_hovered = False
        self.particles: List[PandaParticle] = []

        self.setMouseTracking(True)
        self.setAttribute(QtCore.Qt.WA_Hover, True)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        w = 16 * self.pixel_size + 24
        h = 16 * self.pixel_size + 24
        self.setFixedSize(w, h)

        self.anim_timer = QtCore.QTimer(self)
        self.anim_timer.timeout.connect(self._on_tick)
        self.anim_timer.start(80)

        self._tick_count = 0

    def set_excited(self, excited: bool):
        if self.is_hovered != excited:
            self.is_hovered = excited
            self.state = "excited" if excited else "idle"
            self.hover_changed.emit(excited)
            self.update()

    def enterEvent(self, event):
        self.set_excited(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.set_excited(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
            for _ in range(6):
                self._spawn_particle()
        super().mousePressEvent(event)

    def _spawn_particle(self):
        cx = self.width() / 2 + random.uniform(-16, 16)
        cy = self.height() / 2 - 8
        r = random.random()
        if r < 0.35:
            ptype = "heart"
        elif r < 0.65:
            ptype = "star"
        elif r < 0.85:
            ptype = "dumpling"
        else:
            ptype = "bamboo"
        self.particles.append(PandaParticle(cx, cy, ptype))

    def _on_tick(self):
        self._tick_count += 1

        if self.is_hovered and random.random() < 0.4:
            self._spawn_particle()

        for p in self.particles[:]:
            p.update()
            if not p.is_alive():
                self.particles.remove(p)

        if self.state == "excited":
            self.frame_index = 0 if (self._tick_count // 2) % 2 == 0 else 1
        elif self.state == "idle":
            if self._tick_count % 55 in (0, 1, 2):
                self.frame_index = 2
            else:
                self.frame_index = 0 if (self._tick_count // 8) % 2 == 0 else 1

        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)

        if self.state == "excited":
            frame = PANDA_EXCITED_1 if self.frame_index == 0 else PANDA_EXCITED_2
        elif self.frame_index == 2:
            frame = PANDA_BLINK
        else:
            frame = PANDA_IDLE_1 if self.frame_index == 0 else PANDA_IDLE_2

        bounce_y = 0
        bounce_x = 0
        if self.state == "excited":
            bounce_y = -4 if self.frame_index == 1 else 0
            bounce_x = 1 if (self._tick_count % 4) in (0, 1) else -1

        ox = (self.width() - 16 * self.pixel_size) // 2 + bounce_x
        oy = (self.height() - 16 * self.pixel_size) // 2 + 10 + bounce_y

        # Soft drop shadow
        painter.setBrush(QtGui.QColor(0, 0, 0, 50))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(ox + 2 * self.pixel_size, oy + 14 * self.pixel_size, 12 * self.pixel_size, 3 * self.pixel_size)

        # Draw Pixel Grid
        for r, row in enumerate(frame):
            for c, char in enumerate(row):
                color = PALETTE.get(char)
                if color:
                    painter.fillRect(
                        ox + c * self.pixel_size,
                        oy + r * self.pixel_size,
                        self.pixel_size,
                        self.pixel_size,
                        color
                    )

        # Render floating particles
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        for p in self.particles:
            if p.ptype == "heart":
                painter.setBrush(QtGui.QColor(244, 63, 94, p.alpha))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(int(p.x), int(p.y), p.size, p.size)
                painter.drawEllipse(int(p.x + p.size * 0.6), int(p.y), p.size, p.size)
            elif p.ptype == "star":
                painter.setBrush(QtGui.QColor(250, 204, 21, p.alpha))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawRect(int(p.x), int(p.y), p.size, p.size)
            elif p.ptype == "dumpling":
                painter.setBrush(QtGui.QColor(254, 240, 138, p.alpha))
                painter.setPen(QtGui.QColor(217, 119, 6, p.alpha))
                painter.drawEllipse(int(p.x), int(p.y), p.size + 2, p.size)
            elif p.ptype == "bamboo":
                painter.setBrush(QtGui.QColor(16, 185, 129, p.alpha))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawRoundedRect(int(p.x), int(p.y), 4, 8, 2, 2)

        painter.end()


class StitchDesktopPet(QtWidgets.QWidget):
    """
    Floating, frameless, translucent Desktop Pet Window (Panda Po).
    Stays always on top, draggable, and opens the horizontal slide shelf to the left of Po.
    """
    pet_clicked = QtCore.Signal()
    open_dashboard_requested = QtCore.Signal()

    def __init__(self, spotlight_tray=None, parent=None):
        super().__init__(parent)
        self.spotlight_tray = spotlight_tray
        self._drag_pos = None

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.SubWindow
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, False)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        # Panda Po widget with crisp 6px pixel grid
        self.bear_widget = PixelBearWidget(pixel_size=6, parent=self)
        self.bear_widget.clicked.connect(self._on_bear_clicked)
        layout.addWidget(self.bear_widget)

        self.setFixedSize(self.bear_widget.size())
        self._position_default()

    def _position_default(self):
        screen = QtGui.QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.right() - self.width() - 40
            y = geom.bottom() - self.height() - 60
            self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == QtCore.Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton and self._drag_pos is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            # If shelf is open, update its position relative to pet
            if self.spotlight_tray and self.spotlight_tray.isVisible():
                self.spotlight_tray.position_to_left_of(self.geometry())
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _on_bear_clicked(self):
        self.pet_clicked.emit()
        if self.spotlight_tray:
            self.spotlight_tray.toggle_shelf(pet_rect=self.geometry())

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #121318;
                color: #f4f4f5;
                border: 1px solid #282a36;
                border-radius: 12px;
                padding: 6px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #10b981;
                color: #ffffff;
            }
        """)

        action_search = menu.addAction("🎋 Toggle Horizontal Slide Shelf")
        action_dash = menu.addAction("🖥️ Open Workspace Hub")
        menu.addSeparator()
        action_reset = menu.addAction("📍 Reset Po Position")
        action_hide = menu.addAction("💤 Sleep Po")
        menu.addSeparator()
        action_quit = menu.addAction("❌ Exit")

        chosen = menu.exec(pos)
        if chosen == action_search:
            self._on_bear_clicked()
        elif chosen == action_dash:
            self.open_dashboard_requested.emit()
        elif chosen == action_reset:
            self._position_default()
        elif chosen == action_hide:
            self.hide()
        elif chosen == action_quit:
            QtWidgets.QApplication.quit()
