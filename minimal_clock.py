#!/usr/bin/env python3
"""Minimal transparent analog clock (PySide6 / Qt6).

A frameless, transparent clock showing thin hands on a circle face.
Right-click → Settings opens a panel to change radius, color (white / black /
semi-transparent), smoothness, keep-above, per-clock timezone, and to add a
second clock (max two).

Changes are saved to ~/.config/minimal-clock/config.json.

Usage:
    python3 minimal_clock.py [options]
"""
import argparse
import sys

from PySide6.QtWidgets import QApplication

from src.config import CONFIG_PATH, COLORS, MAX_RADIUS, MIN_RADIUS, load_config, radius_from_size
from src.manager import ClockManager


def build_parser():
    p = argparse.ArgumentParser(
        prog="minimal-clock",
        description="Minimal transparent analog clock (PySide6).",
    )
    p.add_argument("--config", default=CONFIG_PATH, help="Config file path")
    p.add_argument("--radius", type=int, help="Clock radius in pixels (40-300)")
    p.add_argument("--size", type=int, help="Window size in pixels (alias for --radius)")
    p.add_argument("--color", choices=list(COLORS.keys()), help="Hand color")
    p.add_argument("--keep-above", action="store_true", help="Keep window above others")
    p.add_argument("--no-smooth", action="store_true", help="Tick once per second")
    p.add_argument("--timezone", help="IANA timezone for the first clock")
    return p


def apply_args(cfg, args):
    """Apply CLI overrides on top of the loaded config."""
    if args.radius is not None:
        cfg["radius"] = max(MIN_RADIUS, min(MAX_RADIUS, args.radius))
    elif args.size is not None:
        cfg["radius"] = radius_from_size(args.size)
    if args.color:
        cfg["color"] = args.color
    if args.keep_above:
        cfg["keep_above"] = True
    if args.no_smooth:
        cfg["smooth"] = False
    if args.timezone:
        cfg["clocks"][0]["timezone"] = args.timezone


def main():
    args = build_parser().parse_args()
    cfg = load_config(args.config)
    apply_args(cfg, args)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    manager = ClockManager(cfg, args.config)
    app.aboutToQuit.connect(manager.save)
    manager.save()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
