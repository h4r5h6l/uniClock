import math
from datetime import datetime
from zoneinfo import ZoneInfo

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from .config import COLORS, shadow_for_color, size_from_radius


class ClockWidget(QWidget):
    settingsRequested = Signal()
    keepAboveChanged = Signal(bool)

    def __init__(self, radius, color, keep_above, smooth, timezones=("",)):
        super().__init__()
        self._color_name = color if color in COLORS else "white"
        self._smooth = smooth
        self._radius = radius
        self._timezones = list(timezones) or [""]
        self._drag_offset = None
        self._shadow = shadow_for_color(self._color_name)

        self.setWindowTitle("Minimal Clock")
        self._apply_size()
        self.setWindowFlags(self._window_flags(keep_above))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(100 if smooth else 1000)

    def _window_flags(self, keep_above):
        flags = Qt.FramelessWindowHint | Qt.Tool
        if keep_above:
            flags |= Qt.WindowStaysOnTopHint
        return flags

    def _apply_size(self):
        face = size_from_radius(self._radius)
        gap = self._radius
        n = len(self._timezones)
        self.setFixedSize(face * n + gap * (n - 1), face)

    def set_radius(self, radius):
        self._radius = radius
        self._apply_size()
        self.update()

    def set_color(self, color_name):
        self._color_name = color_name if color_name in COLORS else "white"
        self._shadow = shadow_for_color(self._color_name)
        self.update()

    def set_smooth(self, smooth):
        self._smooth = smooth
        self._timer.start(100 if smooth else 1000)

    def set_keep_above(self, enabled):
        self.setWindowFlags(self._window_flags(enabled))
        self.show()

    def set_timezones(self, timezones):
        self._timezones = list(timezones) or [""]
        self._apply_size()
        self.update()

    def set_timezone(self, index, timezone):
        if 0 <= index < len(self._timezones):
            self._timezones[index] = timezone or ""
        self.update()

    def _now_for(self, timezone):
        if timezone:
            try:
                return datetime.now(ZoneInfo(timezone))
            except Exception:
                pass
        return datetime.now()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        hand_color = QColor(*COLORS[self._color_name])
        face = size_from_radius(self._radius)
        radius = self._radius
        gap = radius
        center_y = face / 2

        for i, timezone in enumerate(self._timezones):
            now = self._now_for(timezone)
            seconds = now.second + (now.microsecond / 1e6 if self._smooth else 0.0)
            minutes = now.minute + seconds / 60.0
            hours = now.hour % 12 + minutes / 60.0

            cx = i * (face + gap) + face / 2
            center = QPoint(cx, center_y)

            self._draw_circle(painter, center, radius, hand_color, 1.2)
            for hour in range(12):
                major = hour % 3 == 0
                self._draw_tick(painter, center, radius, hand_color, hour * 30.0,
                                0.92 if major else 0.95, 0.84, 2.5 if major else 1.5)

            self._draw_hand(painter, center, radius, hand_color, hours * 30.0, 0.42, 5.0)
            self._draw_hand(painter, center, radius, hand_color, minutes * 6.0, 0.62, 3.0)
            self._draw_hand(painter, center, radius, hand_color, seconds * 6.0, 0.74, 1.5)

            painter.setPen(Qt.NoPen)
            painter.setBrush(hand_color)
            painter.drawEllipse(center, 3, 3)
            painter.setBrush(Qt.NoBrush)

    def _draw_line(self, painter, start, end, color, width):
        """Draw a line with a shadow halo behind it (rounded caps)."""
        painter.setPen(QPen(self._shadow, width + 3.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(start, end)
        painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(start, end)

    def _draw_circle(self, painter, center, radius, color, width):
        painter.setPen(QPen(self._shadow, width + 3.0))
        painter.drawEllipse(center, radius, radius)
        painter.setPen(QPen(color, width))
        painter.drawEllipse(center, radius, radius)

    def _draw_tick(self, painter, center, radius, color, angle_deg, outer_ratio, inner_ratio, width):
        rad = math.radians(angle_deg - 90.0)
        cos, sin = math.cos(rad), math.sin(rad)
        cx, cy = center.x(), center.y()
        outer = QPoint(cx + cos * radius * outer_ratio, cy + sin * radius * outer_ratio)
        inner = QPoint(cx + cos * radius * inner_ratio, cy + sin * radius * inner_ratio)
        self._draw_line(painter, outer, inner, color, width)

    def _draw_hand(self, painter, center, radius, color, angle_deg, length, width):
        rad = math.radians(angle_deg - 90.0)
        tip = QPoint(center.x() + math.cos(rad) * radius * length,
                     center.y() + math.sin(rad) * radius * length)
        self._draw_line(painter, center, tip, color, width)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        handle = self.windowHandle()
        if handle is not None and handle.startSystemMove():
            return
        self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        settings_action = menu.addAction("Settings…")
        settings_action.triggered.connect(self.settingsRequested.emit)
        menu.addSeparator()
        above_action = menu.addAction("Always on top")
        above_action.setCheckable(True)
        above_action.setChecked(bool(self.windowFlags() & Qt.WindowStaysOnTopHint))
        above_action.toggled.connect(self.keepAboveChanged.emit)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.exec(event.globalPos())
