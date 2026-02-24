#!/usr/bin/env python3
"""
Project: MGR-S (Multi-GPU Runtime System)
Module:  mgrs_tray.py — Windows System Tray Integration
Author:  Jaspinder
License: See LICENSE file

Adds a system tray icon using pystray + Pillow.
Launches/shows/hides the main Tk window from the tray.
"""

import threading
import logging
import os
import sys

log = logging.getLogger("mgrs.tray")


def _get_icon_path() -> str:
    """Return path to the .ico file bundled with the app."""
    # PyInstaller bundle: sys._MEIPASS
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)

    # Try installer resources first, then local
    candidates = [
        os.path.join(base, "mgrs_icon.ico"),
        os.path.join(base, "..", "installer", "resources", "icon.ico"),
        os.path.join(base, "icon.ico"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _build_tray_image(size=64):
    """
    Generate a tray icon programmatically if no .ico is found.
    Draws a simple blue gear-like shape using Pillow.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer circle (blue)
    draw.ellipse([4, 4, size - 4, size - 4], fill="#3B82F6")
    # Inner circle (dark cutout — makes it look like a gear/ring)
    inset = size // 4
    draw.ellipse([inset, inset, size - inset, size - inset], fill="#0A0F1E")
    # M letter in center
    cx, cy = size // 2, size // 2
    draw.text((cx - 6, cy - 7), "M", fill="white")

    return img


def _load_icon():
    """Load icon from file or generate fallback."""
    icon_path = _get_icon_path()

    if icon_path:
        try:
            from PIL import Image
            return Image.open(icon_path).resize((64, 64))
        except Exception as e:
            log.warning(f"Could not load icon from {icon_path}: {e}")

    return _build_tray_image()


class SystemTray:
    """
    Wraps pystray to provide a Windows system tray icon.
    Exposes show/hide/quit actions for the main Tk window.
    """

    def __init__(self, tk_root, app_state_getter=None):
        """
        :param tk_root: The root Tk window.
        :param app_state_getter: Callable returning the runtime state string.
        """
        self._root = tk_root
        self._state_getter = app_state_getter or (lambda: "RUNNING")
        self._icon = None
        self._visible = True

    def start(self):
        """Start tray icon in a daemon thread."""
        threading.Thread(target=self._run, daemon=True, name="mgrs-tray").start()

    def _run(self):
        try:
            import pystray
        except ImportError:
            log.warning("pystray not installed — system tray disabled. "
                        "Install with: pip install pystray pillow")
            return

        image = _load_icon()
        if image is None:
            log.warning("Could not create tray icon image — tray disabled.")
            return

        menu = pystray.Menu(
            pystray.MenuItem("Show MGR-S", self._on_show, default=True),
            pystray.MenuItem("Hide to Tray", self._on_hide),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("State: …", self._menu_state, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )

        self._icon = pystray.Icon(
            "MGRS",
            image,
            "MGR-S  | Multi-GPU Runtime",
            menu
        )

        log.info("System tray icon started")
        self._icon.run()

    # ── Dynamic menu item ────────────────────────────────────────────────────

    def _menu_state(self, icon, item):
        """Returns a display-only string showing current runtime state."""
        return f"State: {self._state_getter()}"

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_show(self, icon, item):
        self._root.after(0, self._show_window)

    def _on_hide(self, icon, item):
        self._root.after(0, self._hide_window)

    def _on_quit(self, icon, item):
        self._root.after(0, self._quit_app)

    def _show_window(self):
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()
        self._visible = True
        log.info("Window restored from tray")

    def _hide_window(self):
        self._root.withdraw()
        self._visible = False
        if self._icon:
            self._icon.notify("MGR-S", "Minimized to tray. Click the tray icon to restore.")
        log.info("Window minimized to tray")

    def _quit_app(self):
        if self._icon:
            self._icon.stop()
        self._root.quit()
        self._root.destroy()
        log.info("Application quit from tray")

    def stop(self):
        """Call on application exit."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    # ── Intercept window close → minimize to tray ────────────────────────────

    def bind_close_to_tray(self):
        """
        Override the window X button to hide to tray instead of quitting.
        Call after the tray is started.
        """
        self._root.protocol("WM_DELETE_WINDOW", self._hide_window)
        log.info("WM_DELETE_WINDOW bound to hide-to-tray")


# ── Convenience bootstrap ─────────────────────────────────────────────────────

def attach_tray(tk_root, state_getter=None) -> SystemTray:
    """
    Create and start a SystemTray for `tk_root`.
    Returns the tray instance so the caller can call .stop() on exit.
    """
    tray = SystemTray(tk_root, state_getter)
    tray.start()
    tray.bind_close_to_tray()
    return tray
