#!/usr/bin/env bash
# Install the Analog Clock Widget into the user's home directory.
# No root required. Works on any distro with Python 3 + GTK3 (PyGObject).
#
# Usage:
#   ./install.sh            # install + menu entry
#   ./install.sh --no-menu  # skip desktop menu entry
#   ./install.sh --uninstall
set -euo pipefail

APP_NAME="clock-widget"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/$APP_NAME"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
AUTOSTART_DIR="$HOME/.config/autostart"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/128x128/apps"

UNINSTALL=0
WITH_MENU=1

for arg in "$@"; do
    case "$arg" in
        --uninstall) UNINSTALL=1 ;;
        --no-menu) WITH_MENU=0 ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

# Detect python3 with gi
PYTHON="$(command -v python3 || true)"
if [[ -z "$PYTHON" ]]; then
    echo "ERROR: python3 not found." >&2
    exit 1
fi

uninstall() {
    echo "Removing $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
    rm -f "$DESKTOP_DIR/$APP_NAME.desktop"
    rm -f "$AUTOSTART_DIR/$APP_NAME.desktop"
    rm -f "$ICON_DIR/$APP_NAME.png"
    echo "Removed. Config (~/.config/clock-widget) kept."
}

if [[ "$UNINSTALL" == "1" ]]; then
    uninstall
    exit 0
fi

# Check GTK3 availability
if ! "$PYTHON" -c 'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk' 2>/dev/null; then
    echo "ERROR: PyGObject / GTK3 is required but not available." >&2
    echo "Install it with e.g.:" >&2
    echo "  Ubuntu/Debian: sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0" >&2
    echo "  Fedora:        sudo dnf install python3-gobject gtk3" >&2
    echo "  Arch:          sudo pacman -S python-gobject gtk3" >&2
    exit 1
fi

echo "Installing $APP_NAME to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -r "$SOURCE_DIR/src" "$INSTALL_DIR/"
cp -r "$SOURCE_DIR/assets" "$INSTALL_DIR/"
cp "$SOURCE_DIR/clock.py" "$INSTALL_DIR/clock.py"
chmod +x "$INSTALL_DIR/clock.py"

if [[ "$WITH_MENU" == "1" ]]; then
    echo "Installing desktop menu entry"
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICON_DIR"
    cp "$SOURCE_DIR/assets/icon.png" "$ICON_DIR/$APP_NAME.png"
    cat > "$DESKTOP_DIR/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Name=Analog Clock Widget
Comment=Portable analog clock widget for your desktop
Type=Application
Exec=$INSTALL_DIR/clock.py
Icon=$APP_NAME
Terminal=false
Categories=Utility;Clock;Widget;
StartupNotify=false
EOF
fi

echo
echo "Done. Launch with:  $INSTALL_DIR/clock.py"
echo "Options:  $INSTALL_DIR/clock.py --help"
echo
echo "To start at login, add to your desktop's autostart:"
echo "  $INSTALL_DIR/clock.py"
echo "  (e.g. copy this command into 'Startup Applications')"