import json
import os

from PySide6.QtGui import QColor

APP_NAME = "minimal-clock"
CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), APP_NAME
)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
MAX_CLOCKS = 2
MIN_RADIUS = 40
MAX_RADIUS = 300
PADDING = 8

COLORS = {
    "white": (255, 255, 255, 255),
    "black": (0, 0, 0, 255),
    "semi-transparent": (255, 255, 255, 110),
}

COMMON_TIMEZONES = [
    "", "UTC", "Europe/London", "Europe/Berlin", "Europe/Paris",
    "Europe/Moscow", "America/New_York", "America/Los_Angeles",
    "America/Sao_Paulo", "Africa/Johannesburg", "Asia/Dubai",
    "Asia/Kolkata", "Asia/Shanghai", "Asia/Tokyo", "Australia/Sydney",
]

LOCAL_LABEL = "Local time"


def default_config():
    return {
        "radius": 112,
        "color": "white",
        "keep_above": False,
        "on_all_desktops": True,
        "smooth": True,
        "clocks": [{"timezone": ""}],
    }


def load_config(path=None):
    cfg = default_config()
    try:
        with open(path or CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for key in ("radius", "color", "keep_above", "on_all_desktops", "smooth"):
            if key in data:
                cfg[key] = data[key]
        if isinstance(data.get("clocks"), list) and data["clocks"]:
            cfg["clocks"] = [
                {"timezone": str(c.get("timezone", ""))}
                for c in data["clocks"][:MAX_CLOCKS]
            ]
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg, path=None):
    path = path or CONFIG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    os.replace(tmp, path)


def size_from_radius(radius):
    return 2 * radius + 2 * PADDING


def radius_from_size(size):
    return max(MIN_RADIUS, min(MAX_RADIUS, size // 2 - PADDING))


def shadow_for_color(color_name):
    if color_name == "black":
        return QColor(255, 255, 255, 90)
    return QColor(0, 0, 0, 90)
