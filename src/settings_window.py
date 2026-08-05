from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .config import (
    COLORS,
    COMMON_TIMEZONES,
    LOCAL_LABEL,
    MAX_CLOCKS,
    MAX_RADIUS,
    MIN_RADIUS,
)


class SettingsWindow(QWidget):
    closed = Signal()

    def __init__(self, manager):
        super().__init__()
        self._manager = manager
        self._tz_combos = []
        self.setWindowTitle("Minimal Clock — Settings")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.radius_slider = QSlider(Qt.Horizontal)
        self.radius_slider.setRange(MIN_RADIUS, MAX_RADIUS)
        self.radius_slider.setValue(manager.cfg["radius"])
        self.radius_label = QLabel(str(manager.cfg["radius"]))
        radius_row = QHBoxLayout()
        radius_row.addWidget(self.radius_slider)
        radius_row.addWidget(self.radius_label)
        form.addRow("Radius:", radius_row)

        self.color_combo = QComboBox()
        self.color_combo.addItems(list(COLORS.keys()))
        self.color_combo.setCurrentText(manager.cfg["color"])
        form.addRow("Color:", self.color_combo)

        self.smooth_check = QCheckBox("Smooth seconds")
        self.smooth_check.setChecked(manager.cfg["smooth"])
        form.addRow(self.smooth_check)

        self.above_check = QCheckBox("Always on top")
        self.above_check.setChecked(manager.cfg["keep_above"])
        form.addRow(self.above_check)

        self.alldesktops_check = QCheckBox("Show on all desktops")
        self.alldesktops_check.setChecked(manager.cfg["on_all_desktops"])
        form.addRow(self.alldesktops_check)
        layout.addLayout(form)

        layout.addWidget(QLabel("Clocks:"))
        self.clocks_box = QVBoxLayout()
        layout.addLayout(self.clocks_box)
        self.add_button = QPushButton("Add second clock")
        layout.addWidget(self.add_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self._rebuild_clock_rows()

        self.radius_slider.valueChanged.connect(self._on_radius)
        self.color_combo.currentTextChanged.connect(self._on_color)
        self.smooth_check.toggled.connect(self._on_smooth)
        self.above_check.toggled.connect(self._on_above)
        self.alldesktops_check.toggled.connect(self._on_all_desktops)
        self.add_button.clicked.connect(self._on_add)

    def _rebuild_clock_rows(self):
        while self.clocks_box.count():
            item = self.clocks_box.takeAt(0)
            row = item.layout()
            if row is not None:
                while row.count():
                    sub = row.takeAt(0)
                    widget = sub.widget()
                    if widget is not None:
                        widget.deleteLater()
                row.deleteLater()
        self._tz_combos = []
        for i, clock_cfg in enumerate(self._manager.cfg["clocks"]):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"Clock {i + 1}"))
            combo = QComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.NoInsert)
            tz_val = clock_cfg.get("timezone", "")
            for tz in COMMON_TIMEZONES:
                combo.addItem(tz if tz else LOCAL_LABEL)
            if tz_val and tz_val not in COMMON_TIMEZONES:
                combo.addItem(tz_val)
            combo.blockSignals(True)
            combo.setCurrentIndex(combo.findText(tz_val if tz_val else LOCAL_LABEL))
            combo.blockSignals(False)
            combo.currentTextChanged.connect(lambda text, idx=i: self._on_timezone(idx, text))
            row.addWidget(combo, 1)
            if i > 0:
                remove_button = QPushButton("Remove")
                remove_button.clicked.connect(lambda _, idx=i: self._on_remove(idx))
                row.addWidget(remove_button)
            self.clocks_box.addLayout(row)
            self._tz_combos.append(combo)
        self.add_button.setEnabled(len(self._manager.cfg["clocks"]) < MAX_CLOCKS)

    def _on_radius(self, value):
        self.radius_label.setText(str(value))
        self._manager.set_radius(value)

    def _on_color(self, name):
        self._manager.set_color(name)

    def _on_smooth(self, checked):
        self._manager.set_smooth(checked)

    def _on_above(self, checked):
        self._manager.set_keep_above(checked)

    def _on_all_desktops(self, checked):
        self._manager.set_on_all_desktops(checked)

    def _on_timezone(self, index, text):
        self._manager.set_timezone(index, "" if text == LOCAL_LABEL else text.strip())

    def _on_add(self):
        self._manager.add_clock()
        self._rebuild_clock_rows()

    def _on_remove(self, index):
        self._manager.remove_clock(index)
        self._rebuild_clock_rows()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
