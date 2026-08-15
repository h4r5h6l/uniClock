#!/usr/bin/env python3

import json
import math
import os
import platform
from datetime import datetime
from tkinter import colorchooser, messagebox

import tkinter as tk

SYSTEM_BACKGROUND = "systembackground"

DEFAULT_CONFIG = {
    "size": 300,
    "circle_color": "#E63965",
    "tick_color": "#FFFFFF",
    "minute_tick_color": "#FFD5DE",
    "hand_color": "#FFFFFF",
    "second_color": "#FFD166",
    "show_second_hand": True,
    "smooth_hands": True,
    "always_on_top": True,
    "opacity": 0.6,
    "x": None,
    "y": None,
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clock_settings.json")

CONFIG = dict(DEFAULT_CONFIG)
TRANSPARENT_BG = None
BG_IS_KEY = False
SHAPED = False
_settings_open = False


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            loaded = json.load(f)
        for key in DEFAULT_CONFIG:
            if key in loaded:
                CONFIG[key] = loaded[key]
        CONFIG["size"] = int(CONFIG["size"])
    except (OSError, ValueError):
        pass


def save_config():
    with open(CONFIG_PATH, "w") as f:
        json.dump(CONFIG, f, indent=2)


def save_position(root):
    CONFIG["x"] = root.winfo_x()
    CONFIG["y"] = root.winfo_y()
    save_config()


def start_position_watchdog(root):
    def tick():
        x = root.winfo_x()
        y = root.winfo_y()
        if x != CONFIG.get("x") or y != CONFIG.get("y"):
            save_position(root)
        root.after(5000, tick)

    root.after(5000, tick)


def geo(size):
    radius = size / 2 - 0.05 * size
    return {
        "center": size / 2,
        "radius": radius,
        "margin": 0.05 * size,
        "hour": 0.50 * radius,
        "minute": 0.75 * radius,
        "second": 0.80 * radius,
        "second_tail": 0.10 * radius,
        "cap": 0.02 * size,
        "tick_hour_width": 0.01 * size,
        "tick_minute_width": size / 300,
        "hour_width": size / 60,
        "minute_width": size / 100,
        "second_width": size / 300,
    }


def apply_x11_circle_shape(root, size):
    try:
        import ctypes
        import ctypes.util

        x11 = ctypes.CDLL(ctypes.util.find_library("X11"))
        xext = ctypes.CDLL(ctypes.util.find_library("Xext"))
    except (OSError, TypeError):
        return False

    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XDefaultScreen.argtypes = [ctypes.c_void_p]
    x11.XDefaultScreen.restype = ctypes.c_int
    x11.XCreatePixmap.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
    x11.XCreatePixmap.restype = ctypes.c_ulong
    x11.XCreateGC.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
    x11.XCreateGC.restype = ctypes.c_ulong
    x11.XSetForeground.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong]
    x11.XFillRectangle.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
    x11.XFillArc.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_int, ctypes.c_int]
    x11.XFreePixmap.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XFreeGC.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    x11.XDefaultRootWindow.restype = ctypes.c_ulong
    x11.XQueryTree.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)),
        ctypes.POINTER(ctypes.c_uint),
    ]
    x11.XQueryTree.restype = ctypes.c_int
    xext.XShapeCombineMask.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong, ctypes.c_int]

    display = x11.XOpenDisplay(None)
    if not display:
        return False

    screen_root = x11.XDefaultRootWindow(display)
    window = root.winfo_id()
    for _ in range(8):
        root_ret = ctypes.c_ulong()
        parent = ctypes.c_ulong()
        children = ctypes.POINTER(ctypes.c_ulong)()
        count = ctypes.c_uint()
        if not x11.XQueryTree(
            display,
            window,
            ctypes.byref(root_ret),
            ctypes.byref(parent),
            ctypes.byref(children),
            ctypes.byref(count),
        ):
            break
        if parent.value == screen_root or parent.value == 0:
            break
        window = parent.value

    margin = int(round(size * 0.05))
    pixmap = x11.XCreatePixmap(display, window, size, size, 1)
    gc = x11.XCreateGC(display, pixmap, 0, None)
    x11.XSetForeground(display, gc, 0)
    x11.XFillRectangle(display, pixmap, gc, 0, 0, size, size)
    x11.XSetForeground(display, gc, 1)
    x11.XFillArc(display, pixmap, gc, margin, margin, size - 2 * margin, size - 2 * margin, 0, 360 * 64)

    SHAPE_BOUNDING = 0
    SHAPE_SET = 0
    xext.XShapeCombineMask(display, window, SHAPE_BOUNDING, 0, 0, pixmap, SHAPE_SET)

    x11.XFreePixmap(display, pixmap)
    x11.XFreeGC(display, gc)
    x11.XCloseDisplay(display)
    return True


def configure_transparency(root):
    global TRANSPARENT_BG, BG_IS_KEY, SHAPED
    system = platform.system().lower()
    if system == "windows":
        try:
            root.attributes("-transparentcolor", SYSTEM_BACKGROUND)
            TRANSPARENT_BG = SYSTEM_BACKGROUND
            BG_IS_KEY = True
            return
        except tk.TclError:
            pass
    elif system == "darwin":
        try:
            root.attributes("-transparent", True)
            TRANSPARENT_BG = "systemTransparent"
            BG_IS_KEY = True
            return
        except tk.TclError:
            pass
    elif apply_x11_circle_shape(root, CONFIG["size"]):
        SHAPED = True
    TRANSPARENT_BG = CONFIG["circle_color"]


def apply_opacity(root):
    if not BG_IS_KEY:
        root.attributes("-alpha", CONFIG["opacity"])


def make_draggable(root, canvas):
    drag_data = {"x": 0, "y": 0, "is_dragging": False}

    def _on_press(event):
        drag_data["x"] = event.x_root - root.winfo_x()
        drag_data["y"] = event.y_root - root.winfo_y()
        drag_data["is_dragging"] = True

    def _on_drag(event):
        if not drag_data["is_dragging"]:
            return
        x = event.x_root - drag_data["x"]
        y = event.y_root - drag_data["y"]
        root.geometry(f"+{x}+{y}")

    def _on_release(event):
        drag_data["is_dragging"] = False
        save_position(root)

    canvas.bind("<ButtonPress-1>", _on_press)
    canvas.bind("<B1-Motion>", _on_drag)
    canvas.bind("<ButtonRelease-1>", _on_release)


def draw_ticks(canvas):
    size = CONFIG["size"]
    g = geo(size)
    radius = g["radius"]

    for minute in range(60):
        angle = math.radians(minute * 6)

        if minute % 5 == 0:
            inner = 0.85 * radius
            width = g["tick_hour_width"]
            color = CONFIG["tick_color"]
        else:
            inner = 0.90 * radius
            width = g["tick_minute_width"]
            color = CONFIG["minute_tick_color"]

        outer = 0.95 * radius
        canvas.create_line(
            g["center"] + inner * math.cos(angle),
            g["center"] + inner * math.sin(angle),
            g["center"] + outer * math.cos(angle),
            g["center"] + outer * math.sin(angle),
            fill=color,
            width=width,
            capstyle="round",
            tags="static",
        )


def draw_hands(canvas):
    g = geo(CONFIG["size"])
    now = datetime.now()
    hour = now.hour % 12
    minute = now.minute
    second = now.second
    microsecond = now.microsecond

    if CONFIG["smooth_hands"]:
        second_progress = second + microsecond / 1_000_000
        minute_progress = minute + second_progress / 60
        hour_progress = hour + minute_progress / 60
    else:
        second_progress = second
        minute_progress = minute
        hour_progress = hour + minute / 60

    second_angle = math.radians(second_progress * 6 - 90)
    minute_angle = math.radians(minute_progress * 6 - 90)
    hour_angle = math.radians(hour_progress * 30 - 90)

    canvas.delete("hands")

    if CONFIG["show_second_hand"]:
        canvas.create_line(
            g["center"] - g["second_tail"] * math.cos(second_angle),
            g["center"] - g["second_tail"] * math.sin(second_angle),
            g["center"] + g["second"] * math.cos(second_angle),
            g["center"] + g["second"] * math.sin(second_angle),
            fill=CONFIG["second_color"],
            width=g["second_width"],
            capstyle=tk.ROUND,
            tags="hands",
        )

    canvas.create_line(
        g["center"],
        g["center"],
        g["center"] + g["minute"] * math.cos(minute_angle),
        g["center"] + g["minute"] * math.sin(minute_angle),
        fill=CONFIG["hand_color"],
        width=g["minute_width"],
        capstyle=tk.ROUND,
        tags="hands",
    )

    canvas.create_line(
        g["center"],
        g["center"],
        g["center"] + g["hour"] * math.cos(hour_angle),
        g["center"] + g["hour"] * math.sin(hour_angle),
        fill=CONFIG["hand_color"],
        width=g["hour_width"],
        capstyle=tk.ROUND,
        tags="hands",
    )

    canvas.create_oval(
        g["center"] - g["cap"],
        g["center"] - g["cap"],
        g["center"] + g["cap"],
        g["center"] + g["cap"],
        fill=CONFIG["hand_color"],
        outline="",
        tags="hands",
    )

    interval = 50 if CONFIG["smooth_hands"] else 1000
    canvas.after(interval, lambda: draw_hands(canvas))


def redraw_static(canvas):
    size = CONFIG["size"]
    g = geo(size)
    canvas.delete("static")
    canvas.create_oval(
        g["margin"],
        g["margin"],
        size - g["margin"],
        size - g["margin"],
        fill=CONFIG["circle_color"],
        outline="",
        tags="static",
    )
    draw_ticks(canvas)


def apply_config(root, canvas):
    global TRANSPARENT_BG
    size = CONFIG["size"]
    root.geometry(f"{size}x{size}")
    root.minsize(size, size)
    root.maxsize(size, size)
    canvas.configure(width=size, height=size)
    if not BG_IS_KEY:
        TRANSPARENT_BG = CONFIG["circle_color"]
        canvas.configure(bg=TRANSPARENT_BG)
    if SHAPED:
        root.update_idletasks()
        apply_x11_circle_shape(root, size)
    root.attributes("-topmost", CONFIG["always_on_top"])
    apply_opacity(root)
    redraw_static(canvas)


def open_settings(root, canvas):
    global _settings_open
    if _settings_open:
        return
    _settings_open = True

    def close():
        global _settings_open
        _settings_open = False
        win.destroy()

    win = tk.Toplevel(root)
    win.title("Clock Settings")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    win.protocol("WM_DELETE_WINDOW", close)

    pending = dict(CONFIG)

    frame = tk.Frame(win, padx=12, pady=12)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Colors").grid(row=0, column=0, columnspan=2, sticky="w")

    def pick_color(key, button):
        _, hexv = colorchooser.askcolor(pending[key], title="Pick color", parent=win)
        if hexv:
            pending[key] = hexv
            button.configure(bg=hexv)

    color_rows = [
        ("Circle", "circle_color"),
        ("Hour ticks", "tick_color"),
        ("Minute ticks", "minute_tick_color"),
        ("Hands", "hand_color"),
        ("Second hand", "second_color"),
    ]
    for r, (label, key) in enumerate(color_rows, start=1):
        tk.Label(frame, text=label).grid(row=r, column=0, sticky="w", padx=4, pady=2)
        button = tk.Button(frame, bg=pending[key], width=3, relief="ridge")
        button.configure(command=lambda k=key, b=button: pick_color(k, b))
        button.grid(row=r, column=1, padx=4, pady=2)

    show_second = tk.BooleanVar(value=pending["show_second_hand"])
    smooth = tk.BooleanVar(value=pending["smooth_hands"])
    topmost = tk.BooleanVar(value=pending["always_on_top"])

    r = len(color_rows) + 1
    tk.Checkbutton(frame, text="Show second hand", variable=show_second).grid(
        row=r, column=0, columnspan=2, sticky="w", padx=4, pady=2
    )
    r += 1
    tk.Checkbutton(frame, text="Smooth hands", variable=smooth).grid(
        row=r, column=0, columnspan=2, sticky="w", padx=4, pady=2
    )
    r += 1
    tk.Checkbutton(frame, text="Always on top", variable=topmost).grid(
        row=r, column=0, columnspan=2, sticky="w", padx=4, pady=2
    )
    r += 1
    tk.Label(frame, text="Size").grid(row=r, column=0, sticky="w", padx=4, pady=2)
    size_var = tk.IntVar(value=pending["size"])
    tk.Spinbox(frame, from_=200, to=500, increment=20, textvariable=size_var, width=6).grid(
        row=r, column=1, sticky="w", padx=4
    )
    r += 1
    tk.Label(frame, text="Opacity").grid(row=r, column=0, sticky="w", padx=4, pady=2)
    opacity_var = tk.DoubleVar(value=pending["opacity"])
    tk.Scale(
        frame,
        from_=0.2,
        to=1.0,
        resolution=0.05,
        orient="horizontal",
        variable=opacity_var,
        width=10,
        length=150,
    ).grid(row=r, column=1, sticky="w", padx=4)
    r += 1

    def save():
        try:
            pending["size"] = int(size_var.get())
        except ValueError:
            messagebox.showerror("Invalid size", "Size must be a number.", parent=win)
            return
        pending["show_second_hand"] = show_second.get()
        pending["smooth_hands"] = smooth.get()
        pending["always_on_top"] = topmost.get()
        pending["opacity"] = float(opacity_var.get())
        CONFIG.update(pending)
        save_config()
        apply_config(root, canvas)
        close()

    tk.Button(frame, text="Save", command=save).grid(row=r, column=0, padx=4, pady=8, sticky="e")
    tk.Button(frame, text="Cancel", command=close).grid(row=r, column=1, padx=4, pady=8, sticky="w")


def main():
    load_config()
    root = tk.Tk()
    root.title("")
    size = CONFIG["size"]
    if CONFIG.get("x") is not None and CONFIG.get("y") is not None:
        root.geometry(f"{size}x{size}+{CONFIG['x']}+{CONFIG['y']}")
    else:
        root.geometry(f"{size}x{size}")
    root.minsize(size, size)
    root.maxsize(size, size)
    root.overrideredirect(True)

    root.update_idletasks()
    configure_transparency(root)
    apply_opacity(root)

    canvas = tk.Canvas(
        root,
        width=size,
        height=size,
        bg=TRANSPARENT_BG,
        highlightthickness=0,
        borderwidth=0,
    )
    canvas.pack(fill="both", expand=True)

    redraw_static(canvas)
    draw_hands(canvas)
    make_draggable(root, canvas)
    canvas.bind("<ButtonPress-3>", lambda e: open_settings(root, canvas))

    root.attributes("-topmost", CONFIG["always_on_top"])
    start_position_watchdog(root)
    root.mainloop()


if __name__ == "__main__":
    main()
