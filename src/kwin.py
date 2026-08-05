import os
import tempfile

from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage
from PySide6.QtWidgets import QApplication

_KDE_SERVICE = "org.kde.KWin"
_SCRIPTING_PATH = "/Scripting"
_SCRIPTING_IFACE = "org.kde.kwin.Scripting"
_SCRIPT_IFACE = "org.kde.kwin.Script"
_CAPTION = "Minimal Clock"

_PLACE_JS = """
function isClock(w) {
    return w.caption === '%(caption)s'
        || (w.resourceName === 'minimal_clock')
        || (w.resourceClass === 'minimal_clock');
}
function place(w) {
    if (!isClock(w)) return;
    var g = w.frameGeometry;
    w.frameGeometry = {x: %(x)d, y: %(y)d, width: g.width, height: g.height};
}
workspace.windowAdded.connect(place);
var windows = workspace.windowList();
for (var i = 0; i < windows.length; ++i) place(windows[i]);
"""


def supported():
    app = QApplication.instance()
    if app is None or not app.platformName().startswith("wayland"):
        return False
    return "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper()


def _scripting():
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        return None
    scripting = QDBusInterface(_KDE_SERVICE, _SCRIPTING_PATH, _SCRIPTING_IFACE, bus)
    if not scripting.isValid():
        return None
    return scripting


def _load_and_run(name, body, keep_alive=False):
    """Load *body* as a KWin script and run it.

    Returns the script id on success, None otherwise. The temp file is
    removed after run() returns, because run() re-reads the file. When
    keep_alive is True the script stays loaded; otherwise it is stopped
    and unloaded immediately.
    """
    scripting = _scripting()
    if scripting is None:
        return None
    fd, path = tempfile.mkstemp(suffix=".js", prefix="miniclock-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
        scripting.call("unloadScript", name)
        reply = scripting.call("loadScript", path, name)
        if reply.type() != QDBusMessage.ReplyMessage or not reply.arguments():
            return None
        script_id = int(reply.arguments()[0])
        if script_id < 0:
            return None
        runner = QDBusInterface(
            _KDE_SERVICE,
            f"{_SCRIPTING_PATH}/Script{script_id}",
            _SCRIPT_IFACE,
            QDBusConnection.sessionBus(),
        )
        if not runner.isValid():
            return None
        runner.call("run")
        if not keep_alive:
            runner.call("stop")
            scripting.call("unloadScript", name)
        return script_id
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _set_window_property(name, prop, enabled):
    if not supported():
        return False
    body = (
        "var windows = workspace.windowList();\n"
        "for (var i = 0; i < windows.length; i++) {\n"
        "    if (windows[i].caption === '%s') {\n"
        "        windows[i].%s = %s;\n"
        "        break;\n"
        "    }\n"
        "}\n" % (_CAPTION, prop, "true" if enabled else "false")
    )
    return _load_and_run(name, body) is not None


def set_keep_above(enabled):
    return _set_window_property("miniclock-keepabove", "keepAbove", enabled)


def set_on_all_desktops(enabled):
    return _set_window_property("miniclock-alldesktops", "onAllDesktops", enabled)


def place_at(x, y):
    """Place the clock window at (x, y) on the KWin side (Wayland only).

    Returns True on success. The script stays loaded so it also applies the
    position if the window appears slightly later than this call.
    """
    if not supported():
        return False
    body = _PLACE_JS % {"caption": _CAPTION, "x": int(x), "y": int(y)}
    return _load_and_run("miniclock-place", body, keep_alive=True) is not None
