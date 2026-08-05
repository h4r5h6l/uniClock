from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

try:
    from . import kwin
except ImportError:
    kwin = None

from .clock_widget import ClockWidget
from .config import CONFIG_PATH, MAX_CLOCKS, MAX_RADIUS, MIN_RADIUS, save_config
from .settings_window import SettingsWindow


class ClockManager(QObject):
    def __init__(self, cfg, config_path=CONFIG_PATH):
        super().__init__()
        self.cfg = cfg
        self.config_path = config_path
        self.window = None
        self.settings = None
        self._spawn_window()

    def _timezones(self):
        return [c.get("timezone", "") for c in self.cfg["clocks"]]

    def _spawn_window(self):
        widget = ClockWidget(
            radius=self.cfg["radius"],
            color=self.cfg["color"],
            keep_above=self.cfg["keep_above"],
            smooth=self.cfg["smooth"],
            timezones=self._timezones(),
        )
        widget.settingsRequested.connect(self.open_settings)
        widget.keepAboveChanged.connect(self.set_keep_above)
        pos = self._corner_position(widget)
        if pos:
            widget.move(pos[0], pos[1])
        widget.show()
        self.window = widget
        if kwin and kwin.supported():
            if pos:
                QTimer.singleShot(600, lambda: kwin.place_at(pos[0], pos[1]))
            if self.cfg["keep_above"]:
                QTimer.singleShot(500, lambda: kwin.set_keep_above(True))
            if self.cfg["on_all_desktops"]:
                QTimer.singleShot(700, lambda: kwin.set_on_all_desktops(True))

    def _corner_position(self, widget):
        screen = QApplication.primaryScreen()
        if screen is None:
            return None
        margin = 12
        area = screen.availableGeometry()
        return (
            area.right() - widget.width() - margin,
            area.bottom() - widget.height() - margin,
        )

    def add_clock(self):
        if len(self.cfg["clocks"]) >= MAX_CLOCKS:
            return
        self.cfg["clocks"].append({"timezone": ""})
        self.window.set_timezones(self._timezones())
        self.save()

    def remove_clock(self, index):
        if index <= 0 or index >= len(self.cfg["clocks"]):
            return
        self.cfg["clocks"].pop(index)
        self.window.set_timezones(self._timezones())
        self.save()

    def set_radius(self, radius):
        radius = max(MIN_RADIUS, min(MAX_RADIUS, radius))
        self.cfg["radius"] = radius
        self.window.set_radius(radius)
        self.save()

    def set_color(self, color):
        self.cfg["color"] = color
        self.window.set_color(color)
        self.save()

    def set_smooth(self, smooth):
        smooth = bool(smooth)
        self.cfg["smooth"] = smooth
        self.window.set_smooth(smooth)
        self.save()

    def set_keep_above(self, keep_above):
        keep_above = bool(keep_above)
        self.cfg["keep_above"] = keep_above
        self.window.set_keep_above(keep_above)
        if kwin:
            kwin.set_keep_above(keep_above)
        self.save()

    def set_on_all_desktops(self, enabled):
        enabled = bool(enabled)
        self.cfg["on_all_desktops"] = enabled
        if kwin:
            kwin.set_on_all_desktops(enabled)
        self.save()

    def set_timezone(self, index, timezone):
        if index < 0 or index >= len(self.cfg["clocks"]):
            return
        self.cfg["clocks"][index]["timezone"] = timezone or ""
        self.window.set_timezone(index, timezone)
        self.save()

    def open_settings(self):
        if self.settings is not None:
            self.settings.activateWindow()
            self.settings.raise_()
            return
        self.settings = SettingsWindow(self)
        self.settings.closed.connect(self._on_settings_closed)
        if self.window:
            geometry = self.window.frameGeometry()
            self.settings.move(geometry.right() + 12, geometry.top())
        self.settings.show()

    def _on_settings_closed(self):
        self.save()
        self.settings.deleteLater()
        self.settings = None

    def save(self):
        save_config(self.cfg, self.config_path)
