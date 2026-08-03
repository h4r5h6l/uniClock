#!/usr/bin/env python3
"""Analog Clock Widget - a portable GTK3 rewrite of the Cinnamon clock desklet.

Usage:
    python3 clock.py [options]

Options mirror the desklet settings for easy multi-instance setups.
"""
import argparse
import os
import sys

try:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
except (ImportError, ValueError) as exc:
    print(
        "PyGObject / GTK3 is required. Install it with e.g.:\n"
        "  Ubuntu/Debian: sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0\n"
        f"Error: {exc}",
        file=sys.stderr,
    )
    sys.exit(1)

from src.config import Config
from src.clock_window import ClockWindow
from src.theme import ASSETS_ROOT

KNOWN_STYLE_KEYS = {
    "light",
    "dark",
    "light_transparent",
    "dark_transparent",
    "semi_transparent",
    "custom-images",
}


def build_parser():
    p = argparse.ArgumentParser(
        prog="clock-widget",
        description="Portable analog clock widget (GTK3).",
    )
    p.add_argument("--config", default=None, help="Path to a JSON config file")
    p.add_argument("--size", type=int, default=None, help="Clock size in pixels (10-500)")
    p.add_argument(
        "--style",
        default=None,
        choices=sorted(KNOWN_STYLE_KEYS),
        help="Clock style (light, dark, *_transparent, semi_transparent, custom-images)",
    )
    p.add_argument("--show-seconds", action="store_true", dest="show_seconds", default=None,
                   help="Show the seconds hand (overrides config)")
    p.add_argument("--hide-seconds", action="store_false", dest="show_seconds",
                   help="Hide the seconds hand (overrides config)")
    p.add_argument("--no-smooth-seconds", action="store_true", default=None,
                   help="Disable smooth seconds hand movement")
    p.add_argument("--no-smooth-minutes", action="store_true", default=None,
                   help="Disable smooth minutes hand movement")
    p.add_argument("--label", default=None, help="Custom desklet label (e.g. 'London')")
    p.add_argument("--timezone", default=None, help="IANA timezone (e.g. Europe/London)")
    p.add_argument("--position", nargs=2, type=int, metavar=("X", "Y"),
                   help="Initial window position in pixels")
    p.add_argument("--keep-above", action="store_true", default=None,
                   help="Keep window above other windows")
    p.add_argument("--decorated", action="store_true", default=None,
                   help="Show window decorations (title bar)")
    p.add_argument("--frameless", action="store_false", dest="decorated",
                   help="Hide window decorations (widget mode)")

    # custom images
    for part, arg in (("bg", "bg"), ("s", "seconds"), ("m", "minutes"), ("h", "hours")):
        p.add_argument(
            f"--img-{arg}",
            dest=f"img_{part}",
            default=None,
            metavar="PATH",
            help=f"Custom {arg} hand image (only with --style custom-images)",
        )

    p.add_argument("--check-assets", action="store_true",
                   help="Verify theme assets exist and exit")
    return p


def apply_overrides(cfg, args):
    """Apply CLI overrides on top of the loaded config."""
    if args.size is not None:
        cfg.desklet_size = max(10, min(500, args.size))
    if args.style is not None:
        cfg.style = args.style
    if args.show_seconds is not None:
        cfg.show_seconds_hand = args.show_seconds
    if args.no_smooth_seconds:
        cfg.smooth_seconds_hand = False
    if args.no_smooth_minutes:
        cfg.smooth_minutes_hand = False
    if args.label is not None:
        cfg.use_custom_label = True
        cfg.custom_label = args.label
    if args.timezone is not None:
        cfg.use_custom_tz = True
        cfg.custom_tz = args.timezone
    if args.position is not None:
        cfg.pos = [args.position[0], args.position[1]]
    if args.keep_above is not None:
        cfg.keep_above = args.keep_above
    if args.decorated is not None:
        cfg.hide_decorations = not args.decorated

    for part in ("bg", "s", "m", "h"):
        value = getattr(args, f"img_{part}")
        if value:
            cfg.data[f"img_{part}"] = "file://" + os.path.abspath(value)


def check_assets():
    """Print asset status for every part of every style."""
    missing = 0
    styles = ["light", "dark", "light_transparent", "dark_transparent", "semi_transparent"]
    parts = ["bg", "h", "m", "s"]
    for style in styles:
        for part in parts:
            path = ASSETS_ROOT / "img" / style / f"{part}.svg"
            if path.exists():
                print(f"OK   {path.relative_to(ASSETS_ROOT)}")
            else:
                print(f"MISS {path}")
                missing += 1
    print(f"\n{missing} missing asset(s)." if missing else "\nAll assets present.")
    return 1 if missing else 0


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.check_assets:
        sys.exit(check_assets())

    cfg = Config(path=args.config)
    apply_overrides(cfg, args)

    window = ClockWindow(cfg)
    window.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())