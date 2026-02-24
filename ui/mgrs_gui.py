#!/usr/bin/env python3
"""
Project: MGR-S (Multi-GPU Runtime System)
Module:  mgrs_gui.py — Main GUI Application (v0.2)
Author:  Jaspinder
License: See LICENSE file

Dark-mode dashboard showing real GPU data, live metrics,
tile visualizer, PCIe analysis, diagnostics, and settings.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import math
import logging
import os
import sys

# ── Setup logging ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "logs", "mgrs.log"),
                            encoding="utf-8", errors="replace")
    ]
)
log = logging.getLogger("mgrs.gui")

# ── Import MGR-S modules ─────────────────────────────────────────────────────
try:
    from mgrs_types import GpuNode, GpuRole, GpuVendor, PcieLink
    from mgrs_monitor import GpuMonitor, GpuMetrics, SystemMetrics
    from mgrs_scheduler import MultiGpuScheduler, SchedulerConfig
    from mgrs_memory import MemoryAnalyzer, PcieLink
    from mgrs_core import enumerate_gpus
    MODULES_OK = True
except ImportError as e:
    log.warning(f"MGR-S module import error: {e} — running in demo mode")
    MODULES_OK = False

try:
    from mgrs_tray import attach_tray
    TRAY_OK = True
except ImportError:
    TRAY_OK = False
    log.info("mgrs_tray not available — install pystray+pillow to enable")

# ── Color palette ─────────────────────────────────────────────────────────────
C = {
    "bg":         "#0F172A",   # Base Slate
    "surface":    "#1E293B",   # Cards / Panels
    "border":     "#334155",   # Minimal borders
    "header":     "#1E293B",   # Solid top bar
    "accent":     "#3B82F6",   # Primary Blue
    "success":    "#10B981",   # Emerald
    "warning":    "#F59E0B",   # Amber
    "error":      "#EF4444",   # Rose
    "text_p":     "#E2E8F0",   # Softer high-contrast text
    "text_s":     "#94A3B8",   # Muted descriptions
    "log_bg":     "#111827",   # Darker surface for logs
    "accent2":    "#6366F1",   # Indigo/Secondary Accent
}
# Legacy map for backward compatibility during refactor
C["panel"] = C["surface"]
C["text"] = C["text_p"]
C["muted"] = C["text_s"]
C["green"] = C["success"]
C["amber"] = C["warning"]
C["red"] = C["error"]
C["authority"] = C["accent"]
C["assistant"] = "#6366F1"  # Indigo


FONTS = {
    "app_title": ("Segoe UI Variable Display", 22, "bold"),
    "section":   ("Segoe UI Variable Display", 16, "bold"),
    "body":      ("Segoe UI Variable Text", 14),
    "mono":      ("JetBrains Mono", 12),
    "small":     ("Segoe UI Variable Text", 12),
    "badge":     ("Segoe UI Variable Text", 10, "bold"),
}
# Legacy map
FONTS["title"] = FONTS["app_title"]
FONTS["h2"] = FONTS["section"]
FONTS["h3"] = ("Segoe UI Variable Display", 14, "bold")



# ─────────────────────────────────────────────────────────────────────────────
# Re-usable widget helpers
# ─────────────────────────────────────────────────────────────────────────────

def card(parent, radius=16, **kwargs) -> tk.Frame:
    """Enterprise-grade card with rounded corners and soft shadow simulation."""
    # Note: True rounded corners and shadows aren't native to tk.Frame
    # We use highlightthickness=0 and rely on the surface color for 'depth'.
    f = tk.Frame(parent, bg=C["surface"],
                 highlightthickness=0,
                 **kwargs)
    return f


class PillBadge(tk.Frame):
    """Modern pill badge with subtle tinted background."""
    def __init__(self, parent, text, state="INFO", **kwargs):
        super().__init__(parent, bg=C["surface"], **kwargs)
        self._colors = {
            "RUNNING":   ("#10B981", "#064E3B"), # Text, Bg-tint (estimated)
            "DEGRADED":  ("#F59E0B", "#451A03"),
            "ERROR":     ("#EF4444", "#450A0A"),
            "STARTING":  ("#3B82F6", "#1E3A8A"),
            "INFO":      ("#94A3B8", "#1E293B"),
        }
        fg, bg = self._colors.get(state, self._colors["INFO"])
        
        # We simulate the pill with a canvas or just a high-radius rounded label if possible
        # For simplicity in pure tkinter, we use a label with padding
        self.lbl = tk.Label(self, text=text.upper(), font=FONTS["badge"],
                            fg=fg, bg=bg, padx=10, pady=2)
        self.lbl.pack()

    def set_state(self, text, state):
        fg, bg = self._colors.get(state, self._colors["INFO"])
        self.lbl.config(text=text.upper(), fg=fg, bg=bg)


def label(parent, text, font=None, fg=None, bg=None, **kwargs) -> tk.Label:
    return tk.Label(parent, text=text,
                    font=font or FONTS["body"],
                    fg=fg or C["text"],
                    bg=bg or C["panel"],
                    **kwargs)


class MiniBar(tk.Canvas):
    """A slim horizontal progress bar drawn on canvas."""
    def __init__(self, parent, width=120, height=6, color=None, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg="#334155", highlightthickness=0, **kwargs)
        self._width = width
        self._height = height
        self._color = color or C["accent"]
        self._pct = 0.0

    def set_value(self, pct: float):
        self._pct = max(0.0, min(100.0, pct))
        self.delete("all")
        
        # Draw fully rounded background
        r = self._height // 2
        self.create_oval(0, 0, self._height, self._height, fill="#334155", outline="")
        self.create_oval(self._width-self._height, 0, self._width, self._height, fill="#334155", outline="")
        self.create_rectangle(r, 0, self._width-r, self._height, fill="#334155", outline="")

        fill_w = int(self._width * self._pct / 100)
        if fill_w > self._height:
            self.create_oval(0, 0, self._height, self._height, fill=self._color, outline="")
            self.create_oval(fill_w-self._height, 0, fill_w, self._height, fill=self._color, outline="")
            self.create_rectangle(r, 0, fill_w-r, self._height, fill=self._color, outline="")
        elif fill_w > 0:
            self.create_oval(0, 0, fill_w, self._height, fill=self._color, outline="")

    def set_color(self, c: str):
        self._color = c
        self.set_value(self._pct)


class SparkLine(tk.Canvas):
    """Mini line chart showing last N values."""
    def __init__(self, parent, width=140, height=32, color=None, max_points=60, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=C["panel"], highlightthickness=0, **kwargs)
        self._width = width
        self._height = height
        self._color = color or C["accent"]
        self._data = []
        self._max_pts = max_points

    def push(self, value: float):
        self._data.append(value)
        if len(self._data) > self._max_pts:
            self._data.pop(0)
        self._draw()

    def _draw(self):
        self.delete("all")
        if len(self._data) < 2:
            return
        max_v = max(self._data) or 100
        pts = []
        step = self._width / (len(self._data) - 1)
        for i, v in enumerate(self._data):
            x = i * step
            y = self._height - (v / max_v) * self._height
            pts.append((x, y))

        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            self.create_line(x0, y0, x1, y1, fill=self._color, width=1.5, smooth=True)


class TileVisualizer(tk.Canvas):
    """Draws the screen-space tile split between GPUs."""
    def __init__(self, parent, width=280, height=60, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=C["bg"], highlightthickness=1,
                         highlightbackground=C["border"], **kwargs)
        self._width = width
        self._height = height
        self._tiles = []

    def set_tiles(self, tiles: list):
        """tiles = [{gpu_id, pct, task_type, state}]"""
        self._tiles = tiles
        self._draw()

    def _draw(self):
        self.delete("all")
        GPU_COLORS = [C["authority"], C["assistant"], "#6366F1", "#A855F7"]
        state_alpha = {"active": 1.0, "degraded": 0.6, "suspended": 0.3}

        x = 0
        for i, t in enumerate(self._tiles):
            pct = t.get("pct", 0)
            w = int(self._width * pct / 100)
            color = GPU_COLORS[i % len(GPU_COLORS)]
            self.create_rectangle(x, 0, x + w, self._height,
                                  fill=color, outline=C["bg"], width=1)
            if w > 30:
                self.create_text(x + w // 2, self._height // 2,
                                 text=f"GPU{t['gpu_id']}\n{pct:.0f}%",
                                 fill="white", font=FONTS["small"],
                                 justify="center")
            x += w


# ─────────────────────────────────────────────────────────────────────────────
# GPU Card widget
# ─────────────────────────────────────────────────────────────────────────────

class GpuCard(tk.Frame):
    """One card per GPU in the left sidebar."""

    def __init__(self, parent, node: "GpuNode", **kwargs):
        super().__init__(parent, bg=C["surface"], padx=16, pady=16, **kwargs)
        self.node = node
        self.on_click_callback = kwargs.get("on_click")

        # Title Row: Name & Role Badge
        hdr = tk.Frame(self, bg=C["surface"])
        hdr.pack(fill=tk.X, pady=(0, 12))
        
        name_lbl = tk.Label(hdr, text=node.name, font=FONTS["section"],
                            fg=C["text_p"], bg=C["surface"], anchor="w")
        name_lbl.pack(side=tk.LEFT)
        
        role_color = C["accent"] if node.role == GpuRole.AUTHORITY else C["assistant"]
        self.badge = PillBadge(hdr, node.role.value, state="STARTING" if node.role == GpuRole.AUTHORITY else "INFO")
        self.badge.pack(side=tk.RIGHT)

        # Metrics rows
        def metric_row(parent, label_text, color):
            row = tk.Frame(parent, bg=C["surface"])
            row.pack(fill=tk.X, pady=(4, 0))
            tk.Label(row, text=label_text, font=FONTS["badge"],
                     fg=C["text_s"], bg=C["surface"]).pack(side=tk.LEFT)
            val = tk.Label(row, text="—", font=FONTS["body"],
                           fg=C["text_p"], bg=C["surface"])
            val.pack(side=tk.RIGHT)
            bar = MiniBar(parent, width=180, height=6, color=color)
            bar.pack(fill=tk.X, pady=(4, 8))
            return val, bar

        self.util_val, self.util_bar = metric_row(self, "UTILIZATION", C["accent"])
        self.vram_val, self.vram_bar = metric_row(self, "VRAM USAGE", "#A855F7") # Indigo-Purple
        
        # Footer: Temp & Power
        footer = tk.Frame(self, bg=C["surface"])
        footer.pack(fill=tk.X, pady=(8, 0))
        
        self.temp_lbl = tk.Label(footer, text="—°C", font=FONTS["small"],
                                 fg=C["text_s"], bg=C["surface"])
        self.temp_lbl.pack(side=tk.LEFT)
        
        self.pwr_lbl = tk.Label(footer, text="—W", font=FONTS["small"],
                                fg=C["text_s"], bg=C["surface"])
        self.pwr_lbl.pack(side=tk.RIGHT)

        # Bind hover effects for "lift" simulation
        self._bind_recursive(self, "<Enter>", lambda e: self._on_enter())
        self._bind_recursive(self, "<Leave>", lambda e: self._on_leave())
        self._bind_recursive(self, "<Button-1>", lambda e: self._on_click())

    def _on_click(self):
        if self.on_click_callback:
            self.on_click_callback(self.node.id)

    def _bind_recursive(self, widget, event, callback):
        widget.bind(event, callback, add="+")
        for child in widget.winfo_children():
            self._bind_recursive(child, event, callback)

    def _on_enter(self):
        self.config(bg="#2D3748")
        for child in self.winfo_children():
            if child.winfo_class() == "Frame":
                child.config(bg="#2D3748")
            elif child.winfo_class() == "Label" and child != self.badge.lbl:
                child.config(bg="#2D3748")

    def _on_leave(self):
        self.config(bg=C["surface"])
        for child in self.winfo_children():
            if child.winfo_class() == "Frame":
                child.config(bg=C["surface"])
            elif child.winfo_class() == "Label" and child != self.badge.lbl:
                child.config(bg=C["surface"])

    def update_metrics(self, m: "GpuMetrics"):
        self.util_bar.set_value(m.utilization_pct)
        self.util_val.config(text=f"{m.utilization_pct:.0f}%")
        
        self.vram_bar.set_value(m.memory_used_pct)
        self.vram_val.config(text=f"{m.memory_used_mb:.0f} MB")
        
        temp_text = f"{m.temperature_c:.0f}°C" if m.temperature_c > 0 else "—°C"
        self.temp_lbl.config(text=temp_text)
        
        pwr_text = f"{m.power_draw_w:.1f}W" if m.power_draw_w > 0 else "—W"
        self.pwr_lbl.config(text=pwr_text)
        
        # Update badge state if needed
        if m.utilization_pct > 90:
            self.badge.set_state("HEAVY", "ERROR")
        else:
            is_active = getattr(self.node, 'is_active', True)
            self.badge.set_state(self.node.role.value, "RUNNING" if is_active else "INFO")


# ─────────────────────────────────────────────────────────────────────────────
# Main application
# ─────────────────────────────────────────────────────────────────────────────

class MgrsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MGR-S — Multi-GPU Runtime System  v0.2")
        self.root.geometry("1200x720")
        self.root.minsize(900, 600)
        self.root.configure(bg=C["bg"])

        # State
        self._gpu_nodes = []
        self._gpu_cards: dict = {}
        self._monitor: "GpuMonitor | None" = None
        self._scheduler: "MultiGpuScheduler | None" = None
        self._memory_analyzer: "MemoryAnalyzer | None" = None
        self._runtime_state = "STARTING"
        self._start_time = time.time()
        self._tray = None
        self._gpu_detail_frames = {}
        self._current_gpu_id = None
        self._prev_tab = "DASHBOARD"

        # Build UI
        self._build_header()
        self._build_body()
        self._build_footer()

        # System tray (if pystray is installed)
        if TRAY_OK:
            self._tray = attach_tray(root, state_getter=lambda: self._runtime_state)

        # Show first-launch dialog if needed
        self._maybe_show_welcome()

        # Initialize runtime in background
        threading.Thread(target=self._init_runtime, daemon=True,
                         name="mgrs-init").start()

    # ── Header ───────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["header"], height=64)
        hdr.pack(fill=tk.X, side=tk.TOP)
        hdr.pack_propagate(False)

        # Title Section
        title_box = tk.Frame(hdr, bg=C["header"])
        title_box.pack(side=tk.LEFT, padx=24)
        
        tk.Label(title_box, text="MGR-S", font=FONTS["app_title"],
                 fg=C["accent"], bg=C["header"]).pack(side=tk.LEFT)
        
        # State Pill
        self._state_pill = PillBadge(title_box, "STARTING", state="STARTING")
        self._state_pill.pack(side=tk.LEFT, padx=16)

        # Right: Uptime & Version
        right = tk.Frame(hdr, bg=C["header"])
        right.pack(side=tk.RIGHT, padx=24)
        
        self._uptime_label = tk.Label(right, text="UPTIME: 00:00:00",
                                      font=FONTS["small"], fg=C["text_s"], bg=C["header"])
        self._uptime_label.pack(side=tk.RIGHT)
        
        tk.Label(right, text="v0.2 Enterprise Edition", font=FONTS["badge"],
                 fg=C["text_s"], bg=C["header"]).pack(side=tk.RIGHT, padx=16)

    # ── Body ─────────────────────────────────────────────────────────────────

    def _build_body(self):
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        # ── Left sidebar — GPU cards ─────────────────────────────────────────
        self._sidebar = tk.Frame(body, bg=C["bg"], width=280)
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 24))
        self._sidebar.pack_propagate(False)

        tk.Label(self._sidebar, text="HARDWARE NODES", font=FONTS["badge"],
                 fg=C["text_s"], bg=C["bg"]).pack(anchor="w", pady=(0, 16))

        self._gpu_cards_frame = tk.Frame(self._sidebar, bg=C["bg"])
        self._gpu_cards_frame.pack(fill=tk.BOTH, expand=True)

        self._gpu_placeholder = tk.Label(
            self._gpu_cards_frame, text="Identifying GPUs...",
            font=FONTS["body"], fg=C["text_s"], bg=C["bg"]
        )
        self._gpu_placeholder.pack(pady=40)

        # ── Right main area — Layout & Tabs ───────────────────────────────
        self._main = tk.Frame(body, bg=C["bg"])
        self._main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Custom Tab Switcher (Underline style)
        tab_bar = tk.Frame(main, bg=C["bg"])
        tab_bar.pack(fill=tk.X, pady=(0, 24))
        
        self._tabs = {}
        self._tab_frames = {}
        self._active_tab = "DASHBOARD"

        def create_tab(name, label_text):
            btn_container = tk.Frame(tab_bar, bg=C["bg"])
            btn_container.pack(side=tk.LEFT, padx=(0, 24))
            
            btn = tk.Label(btn_container, text=label_text, font=FONTS["section"],
                           fg=C["text_s"], bg=C["bg"], cursor="hand2")
            btn.pack(pady=(0, 4))
            
            underline = tk.Frame(btn_container, height=2, bg=C["bg"])
            underline.pack(fill=tk.X)
            
            self._tabs[name] = (btn, underline)
            self._tab_frames[name] = tk.Frame(self._main, bg=C["bg"])
            
            btn.bind("<Button-1>", lambda e: self._switch_tab(name))

        create_tab("DASHBOARD",   "Dashboard")
        create_tab("DIAGNOSTICS", "Diagnostics")
        create_tab("SETTINGS",    "Settings")
        create_tab("LOG",         "System Log")

        self._switch_tab("DASHBOARD") # Initial state

        self._build_dashboard_tab()
        self._build_diagnostics_tab()
        self._build_settings_tab()
        self._build_log_tab()

    def _switch_tab(self, target):
        if self._current_gpu_id is not None:
            self._back_to_main()

        self._active_tab = target
        self._prev_tab = target
        for name, (btn, underline) in self._tabs.items():
            if name == target:
                btn.config(fg=C["accent"])
                underline.config(bg=C["accent"])
                self._tab_frames[name].pack(fill=tk.BOTH, expand=True)
            else:
                btn.config(fg=C["text_s"])
                underline.config(bg=C["bg"])
                self._tab_frames[name].pack_forget()

    def _switch_to_gpu_detail(self, gpu_id):
        """Switch to a detailed view of a specific GPU."""
        log.info(f"Switching to detail view for GPU {gpu_id}")
        
        # Hide all tab frames
        for frame in self._tab_frames.values():
            frame.pack_forget()
            
        # Build or show detail frame
        if gpu_id not in self._gpu_detail_frames:
            node = next((n for n in self._gpu_nodes if n.id == gpu_id), None)
            if node:
                self._gpu_detail_frames[gpu_id] = self._build_gpu_detail_view(node)
        
        frame = self._gpu_detail_frames.get(gpu_id)
        if frame:
            frame.pack(fill=tk.BOTH, expand=True)
            self._current_gpu_id = gpu_id
        
        # Dim tab bar
        for btn, underline in self._tabs.values():
            btn.config(fg="#4B5563") # Dim grey
            underline.config(bg=C["bg"])

    def _back_to_main(self):
        """Return to the main dashboard/tabs."""
        if self._current_gpu_id is not None:
            frame = self._gpu_detail_frames.get(self._current_gpu_id)
            if frame:
                frame.pack_forget()
            self._current_gpu_id = None
            
        self._switch_tab(self._prev_tab)

    # ── Dashboard tab ─────────────────────────────────────────────────────────

    def _build_dashboard_tab(self):
        p = self._tab_frames["DASHBOARD"]

        # Row 1 — System overview cards
        r1 = tk.Frame(p, bg=C["bg"])
        r1.pack(fill=tk.X, pady=(0, 24))

        def stat_card(parent, title, value_text, color=None):
            c = card(parent)
            c.pack(side=tk.LEFT, padx=(0, 16))
            c.config(padx=16, pady=16)
            
            tk.Label(c, text=title, font=FONTS["badge"], 
                     fg=C["text_s"], bg=C["surface"]).pack(anchor="w")
            lbl = tk.Label(c, text=value_text, font=FONTS["section"],
                           fg=color or C["text_p"], bg=C["surface"])
            lbl.pack(anchor="w", pady=(4, 0))
            return lbl

        self._stat_gpus   = stat_card(r1, "GPUs DETECTED",    "—",         C["accent"])
        self._stat_mode   = stat_card(r1, "RUNTIME MODE",     "—",         "#C084FC") # Light Purple
        self._stat_sched  = stat_card(r1, "SCHEDULER",        "Idle",      C["text_s"])
        self._stat_budget = stat_card(r1, "FRAME BUDGET",     "16.7ms",    C["success"])

        # Row 2 — Tile visualizer
        tile_card = card(p, padx=10, pady=8)
        tile_card.pack(fill=tk.X, pady=(0, 6))
        tk.Label(tile_card, text="SCREEN-SPACE TILE SPLIT",
                 font=FONTS["small"], fg=C["muted"], bg=C["panel"]).pack(anchor="w")
        self._tile_vis = TileVisualizer(tile_card, width=600, height=50)
        self._tile_vis.pack(pady=6)
        self._tile_info = tk.Label(tile_card, text="Awaiting scheduler…",
                                   font=FONTS["small"], fg=C["muted"], bg=C["panel"])
        self._tile_info.pack(anchor="w")

        # Row 3 — Sparkline charts
        r3 = tk.Frame(p, bg=C["bg"])
        r3.pack(fill=tk.X, pady=(0, 6))

        def spark_panel(parent, title, color):
            f = card(parent, padx=10, pady=8)
            f.pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(f, text=title, font=FONTS["small"], fg=C["muted"], bg=C["panel"]).pack(anchor="w")
            sp = SparkLine(f, width=180, height=48, color=color)
            sp.pack()
            val = tk.Label(f, text="—", font=FONTS["h3"], fg=color, bg=C["panel"])
            val.pack(anchor="w")
            return sp, val

        self._spark_util0, self._val_util0 = spark_panel(r3, "GPU0 Utilization", C["accent"])
        self._spark_util1, self._val_util1 = spark_panel(r3, "GPU1 Utilization", C["accent2"])
        self._spark_temp,  self._val_temp  = spark_panel(r3, "GPU0 Temperature", C["amber"])
        self._spark_power, self._val_power = spark_panel(r3, "GPU0 Power Draw",  C["red"])

        # PCIe Health
        pcie_card = card(p, padx=10, pady=8)
        pcie_card.pack(fill=tk.X)
        tk.Label(pcie_card, text="PCIe LINK HEALTH",
                 font=FONTS["small"], fg=C["muted"], bg=C["panel"]).pack(anchor="w")
        self._pcie_status = tk.Label(pcie_card, text="Analyzing…",
                                     font=FONTS["body"], fg=C["muted"], bg=C["panel"],
                                     justify="left", anchor="w", wraplength=700)
        self._pcie_status.pack(fill=tk.X, pady=4)

    # ── Diagnostics tab ───────────────────────────────────────────────────────

    def _build_diagnostics_tab(self):
        p = self._tab_frames["DIAGNOSTICS"]
        tk.Label(p, text="System Diagnostics", font=FONTS["section"],
                 fg=C["text_p"], bg=C["bg"]).pack(anchor="w", pady=(0, 16))

        btn_row = tk.Frame(p, bg=C["bg"])
        btn_row.pack(fill=tk.X, pady=(0, 16))

        def modern_btn(parent, text, cmd, variant="accent"):
            bg = C["accent"] if variant == "accent" else C["surface"]
            fg = "white" if variant == "accent" else C["text_p"]
            b = tk.Button(parent, text=text, command=cmd,
                          bg=bg, fg=fg,
                          activebackground="#2D3748" if variant != "accent" else "#2563EB",
                          activeforeground="white",
                          font=FONTS["body"], padx=16, pady=8,
                          relief="flat", cursor="hand2")
            b.pack(side=tk.LEFT, padx=(0, 12))
            return b

        modern_btn(btn_row, "Re-detect GPUs",    self._run_gpu_detection)
        modern_btn(btn_row, "PCIe Bandwidth Test", self._run_pcie_test, variant="secondary")
        modern_btn(btn_row, "Full System Report",  self._run_full_report, variant="secondary")

        diag_content = card(p)
        diag_content.pack(fill=tk.BOTH, expand=True)
        self._diag_text = scrolledtext.ScrolledText(
            diag_content, font=FONTS["mono"], bg=C["log_bg"], fg=C["text_p"],
            insertbackground=C["text_p"], state="disabled",
            relief="flat", borderwidth=0, padx=12, pady=12
        )
        self._diag_text.pack(fill=tk.BOTH, expand=True)

    # ── Settings tab ─────────────────────────────────────────────────────────

    def _build_settings_tab(self):
        p = self._tab_frames["SETTINGS"]
        tk.Label(p, text="Runtime Settings", font=FONTS["section"],
                 fg=C["text_p"], bg=C["bg"]).pack(anchor="w", pady=(0, 16))

        sf = card(p)
        sf.config(padx=24, pady=24)
        sf.pack(fill=tk.X)

        def setting_row(parent, label_text, widget_fn):
            row = tk.Frame(parent, bg=C["surface"])
            row.pack(fill=tk.X, pady=8)
            tk.Label(row, text=label_text, font=FONTS["body"],
                     fg=C["text_s"], bg=C["surface"], width=24, anchor="w").pack(side=tk.LEFT)
            w = widget_fn(row)
            w.pack(side=tk.LEFT, padx=16)
            return w

        # Target FPS
        self._fps_var = tk.StringVar(value="60")
        setting_row(sf, "Target FPS",
                    lambda p: ttk.Combobox(p, textvariable=self._fps_var,
                                          values=["30", "60", "120", "144", "240"],
                                          width=8, state="readonly"))

        # Resolution
        self._res_var = tk.StringVar(value="3840x2160")
        setting_row(sf, "Target Resolution",
                    lambda p: ttk.Combobox(p, textvariable=self._res_var,
                                          values=["1920x1080", "2560x1440", "3840x2160"],
                                          width=12, state="readonly"))

        # Performance mode
        self._mode_var = tk.StringVar(value="Balanced")
        setting_row(sf, "Performance Mode",
                    lambda p: ttk.Combobox(p, textvariable=self._mode_var,
                                          values=["Balanced", "Max Performance", "Power Saving"],
                                          width=14, state="readonly"))

        # Monitor Poll Interval
        self._poll_var = tk.StringVar(value="1.0")
        setting_row(sf, "Monitoring Interval",
                    lambda p: ttk.Combobox(p, textvariable=self._poll_var,
                                          values=["0.5", "1.0", "2.0", "5.0"],
                                          width=6, state="readonly"))

        # Launch on startup
        self._startup_var = tk.BooleanVar(value=False)
        tk.Checkbutton(sf, text="Launch MGR-S on Windows startup",
                       variable=self._startup_var,
                       bg=C["surface"], fg=C["text_p"], selectcolor=C["bg"],
                       activebackground=C["surface"], font=FONTS["body"]).pack(anchor="w", pady=12)

        tk.Button(sf, text="Apply Changes",
                  bg=C["accent"], fg=C["text_p"],
                  activebackground="#2563EB", activeforeground=C["text_p"],
                  font=FONTS["body"], padx=24, pady=8, relief="flat",
                  command=self._apply_settings, cursor="hand2").pack(anchor="w", pady=(12, 0))

    # ── Log tab ───────────────────────────────────────────────────────────────

    def _build_log_tab(self):
        p = self._tab_frames["LOG"]
        tk.Label(p, text="Live System Log", font=FONTS["section"],
                 fg=C["text_p"], bg=C["bg"]).pack(anchor="w", pady=(0, 16))

        lf = card(p)
        lf.pack(fill=tk.BOTH, expand=True)
        
        # Modern scrollable text with JetBrains Mono
        self._log_text = scrolledtext.ScrolledText(
            lf, font=FONTS["mono"], bg=C["log_bg"], fg=C["text_p"],
            insertbackground=C["text_p"], state="disabled",
            relief="flat", borderwidth=0, padx=12, pady=12
        )
        self._log_text.pack(fill=tk.BOTH, expand=True)
        
        # Tags for semantic coloring
        self._log_text.tag_config("INFO",    foreground=C["text_s"])
        self._log_text.tag_config("OK",      foreground=C["success"])
        self._log_text.tag_config("WARNING", foreground=C["warning"])
        self._log_text.tag_config("ERROR",   foreground=C["error"])
        self._log_text.tag_config("WARN",    foreground=C["warning"])

    # ── Footer ────────────────────────────────────────────────────────────────

    def _build_footer(self):
        ftr = tk.Frame(self.root, bg=C["header"], height=32)
        ftr.pack(fill=tk.X, side=tk.BOTTOM)
        ftr.pack_propagate(False)

        tk.Label(ftr, text="© 2026 Jaspinder  •  MGR-S v0.2 Alpha  •  Build: Debug",
                 font=FONTS["small"], fg=C["muted"], bg=C["header"]).pack(side=tk.LEFT, padx=12)

        tk.Button(ftr, text="Exit", bg=C["panel"], fg=C["text"],
                  activebackground=C["red"], activeforeground="white",
                  font=FONTS["small"], relief="flat", padx=8, cursor="hand2",
                  command=self._handle_exit).pack(side=tk.RIGHT, padx=8, pady=4)

    # ── Runtime initialization ────────────────────────────────────────────────

    def _init_runtime(self):
        self._log("Initializing MGR-S runtime…")
        try:
            self._log("Step 1: Enumerating GPUs…")
            if MODULES_OK:
                nodes = enumerate_gpus()
            else:
                nodes = self._demo_nodes()
            self._log(f"Step 1 Complete: {len(nodes)} GPUs found")

            self._gpu_nodes = nodes
            self.root.after(0, self._populate_gpu_cards)

            # Memory analyzer
            self._log("Step 2: Initializing Memory Analyzer…")
            node_vrms = [n.vram_mb for n in nodes]
            self._memory_analyzer = MemoryAnalyzer(target_fps=int(self._fps_var.get() or 60))
            self._log("Step 2 Complete")

            # Scheduler
            self._log("Step 3: Initializing Scheduler…")
            cfg = SchedulerConfig(
                target_fps=int(self._fps_var.get() or 60),
                screen_width=3840, screen_height=2160
            )
            self._scheduler = MultiGpuScheduler(cfg)
            self._scheduler.register_gpus_from_nodes(nodes)
            self._log("Step 3 Complete")

            # Monitor
            self._log("Step 4: Starting Monitor…")
            if MODULES_OK:
                interval_str = self._poll_var.get() or "1.0"
                self._monitor = GpuMonitor(interval=float(interval_str))
                self._monitor.register_callback(self._on_metrics_update)
                self._monitor.start()
            self._log("Step 4 Complete")

            # Set state
            self._log("Step 5: Updating UI state card…")
            if len(nodes) > 1:
                self._set_state("RUNNING")
                mode = "Multi-GPU SFR"
            elif len(nodes) == 1:
                self._set_state("DEGRADED")
                mode = "Single GPU"
            else:
                self._set_state("ERROR")
                mode = "No GPU"

            self.root.after(0, lambda: self._stat_gpus.config(text=str(len(nodes))))
            self.root.after(0, lambda: self._stat_mode.config(text=mode))
            self.root.after(0, lambda: self._stat_sched.config(
                text="Active" if len(nodes) > 1 else "Idle",
                fg=C["green"] if len(nodes) > 1 else C["amber"]
            ))

            self._log(f"Runtime ready: {len(nodes)} GPU(s) detected", "OK")
            self.root.after(0, self._refresh_pcie_panel)
            self.root.after(0, self._refresh_tile_vis)
            self._log("Initialization fully complete", "OK")

        except Exception as e:
            self._log(f"Initialization error: {e}", "ERROR")
            self._set_state("ERROR")

        # Start UI refresh timer
        self.root.after(1000, self._ui_tick)

    def _demo_nodes(self):
        """Return fake nodes when modules not available."""
        class FakeNode:
            def __init__(self, id, name, vendor_n, vram_mb, role_n):
                self.id = id
                self.name = name
                self.vendor = type("V", (), {"value": vendor_n})()
                self.vram_mb = vram_mb
                self.vram_gb = round(vram_mb / 1024, 1)
                self.role = type("R", (), {"value": role_n})()
                self.driver_version = "Demo"
                self.vulkan_support = True
                self.is_active = True
                self.pcie = type("P", (), {
                    "gen": 4, "width": 16,
                    "bandwidth_gbps": 32.0, "link_type": "DIRECT_P2P"
                })()
        return [
            FakeNode(0, "NVIDIA GeForce RTX 3060", "NVIDIA", 12288, "Authority"),
            FakeNode(1, "Intel UHD Graphics 630",  "Intel",   1024, "Assistant"),
        ]

    def _populate_gpu_cards(self):
        """Build GPU card widgets from detected nodes."""
        for w in self._gpu_cards_frame.winfo_children():
            w.destroy()
        self._gpu_cards = {}

        if not self._gpu_nodes:
            tk.Label(self._gpu_cards_frame, text="No GPUs detected",
                     font=FONTS["body"], fg=C["red"], bg=C["bg"]).pack(pady=20)
            return

        for node in self._gpu_nodes:
            c = GpuCard(self._gpu_cards_frame, node, on_click=self._switch_to_gpu_detail)
            c.pack(fill=tk.X, pady=(0, 6))
            self._gpu_cards[node.id] = c

    def _on_metrics_update(self, gpu_metrics: list, sys_metrics):
        """Called from monitor thread — schedule GUI update on main thread."""
        self.root.after(0, lambda: self._apply_metrics(gpu_metrics, sys_metrics))

    def _apply_metrics(self, gpu_metrics: list, sys_metrics):
        # 1. Create mapping from monitor_id -> Card
        monitor_to_card = {node.monitor_id: self._gpu_cards[node.id] 
                           for node in self._gpu_nodes if node.id in self._gpu_cards}
        
        # 2. Create mapping from LUID -> Card
        luid_to_card = {node.uuid: self._gpu_cards[node.id] 
                        for node in self._gpu_nodes if node.uuid and node.id in self._gpu_cards}

        # Track which cards already got "high-fidelity" metrics this tick (NVIDIA/AMD)
        updated_cards = set()

        # Step 1: Process high-fidelity metrics first (NVIDIA/AMD)
        for m in gpu_metrics:
            if not m.name.startswith("WMI_GPU_LUID_"):
                if m.gpu_id in monitor_to_card:
                    card = monitor_to_card[m.gpu_id]
                    card.update_metrics(m)
                    updated_cards.add(id(card))

        # Step 2: Process fallback WMI metrics
        unassigned_wmi_metrics = []
        for m in gpu_metrics:
            if m.name.startswith("WMI_GPU_LUID_"):
                luid = m.name.replace("WMI_GPU_LUID_", "")
                if luid in luid_to_card:
                    card = luid_to_card[luid]
                    if id(card) not in updated_cards:
                        card.update_metrics(m)
                        updated_cards.add(id(card))
                    else:
                        # This LUID is already updated (likely by nvidia-smi)
                        # DISCARD it so it doesn't end up in heuristic fallback
                        pass
                else:
                    unassigned_wmi_metrics.append(m)

        # Step 3: Heuristic Fallback for iGPUs (AMD/Intel)
        # If we have cards still not updated, and unassigned WMI metrics, pair them up
        remaining_cards = [card for card in self._gpu_cards.values() 
                           if id(card) not in updated_cards and 
                           card.node.vendor in (GpuVendor.AMD, GpuVendor.INTEL)]
        
        for i, card in enumerate(remaining_cards):
            if i < len(unassigned_wmi_metrics):
                m = unassigned_wmi_metrics[i]
                card.update_metrics(m)
                updated_cards.add(id(card))

        if gpu_metrics:
            m0 = gpu_metrics[0]
            self._spark_util0.push(m0.utilization_pct)
            self._val_util0.config(text=f"{m0.utilization_pct:.0f}%")
            self._spark_temp.push(m0.temperature_c)
            self._val_temp.config(text=f"{m0.temperature_c:.0f}°C")
            self._spark_power.push(m0.power_draw_w)
            self._val_power.config(text=f"{m0.power_draw_w:.0f}W")

        if len(gpu_metrics) >= 2:
            m1 = gpu_metrics[1]
            self._spark_util1.push(m1.utilization_pct)
            self._val_util1.config(text=f"{m1.utilization_pct:.0f}%")

        # Step 4: Update active GPU detail dashboard
        if self._current_gpu_id is not None:
            node = next((n for n in self._gpu_nodes if n.id == self._current_gpu_id), None)
            if node:
                current_m = None
                for m in gpu_metrics:
                    if (node.uuid and m.name == f"WMI_GPU_LUID_{node.uuid}") or (m.gpu_id == node.monitor_id):
                        current_m = m
                        break
                
                if current_m:
                    frame = self._gpu_detail_frames.get(self._current_gpu_id)
                    if frame and hasattr(frame, "trackers"):
                        t = frame.trackers
                        t["util"].config(text=f"{current_m.utilization_pct:.1f}%")
                        t["vram"].config(text=f"{current_m.memory_used_mb:.0f} MB")
                        t["temp"].config(text=f"{current_m.temperature_c:.1f}°C" if current_m.temperature_c > 0 else "—°C")
                        t["pwr"].config(text=f"{current_m.power_draw_w:.1f}W" if current_m.power_draw_w > 0 else "—W")
                        t["s_util"].push(current_m.utilization_pct)
                        t["s_vram"].push(current_m.memory_used_pct)

    def _ui_tick(self):
        """Called every second from main thread."""
        uptime = int(time.time() - self._start_time)
        h, rem = divmod(uptime, 3600)
        m, s = divmod(rem, 60)
        self._uptime_label.config(text=f"Uptime {h:02d}:{m:02d}:{s:02d}")
        self._refresh_tile_vis()
        self.root.after(3000, self._ui_tick)

    # ── Panel refresh ─────────────────────────────────────────────────────────

    def _refresh_tile_vis(self):
        if not self._scheduler:
            return
        try:
            tiles = self._scheduler.get_tile_distribution()
            self._tile_vis.set_tiles(tiles)
            info = "  ".join(
                f"GPU{t['gpu_id']}: {t['pct']:.0f}% ({t['task_type']})"
                for t in tiles
            )
            self._tile_info.config(text=info)
        except Exception as e:
            log.debug(f"tile refresh error: {e}")

    def _refresh_pcie_panel(self):
        if not self._gpu_nodes or not self._memory_analyzer:
            return
        try:
            lines = []
            for n in self._gpu_nodes[1:]:
                link = PcieLink(gen=n.pcie.gen, width=n.pcie.width)
                est = self._memory_analyzer.estimate_transfer(
                    MemoryAnalyzer.FRAME_4K_MB, link, f"GPU{n.id}→GPU0 (4K)"
                )
                lines.append(
                    f"GPU{n.id} ({n.name}): "
                    f"PCIe Gen{n.pcie.gen}x{n.pcie.width} — "
                    f"{link.peak_bandwidth_gbps:.0f}GB/s peak — "
                    f"{est.recommendation}"
                )

            if not lines:
                lines.append("Single GPU — no cross-GPU links")

            self._pcie_status.config(text="\n".join(lines), fg=C["text"])
        except Exception as e:
            log.debug(f"PCIe panel error: {e}")

    def _build_gpu_detail_view(self, node):
        parent = self._main
        container = tk.Frame(parent, bg=C["bg"])
        
        # Header with Back button
        hdr = tk.Frame(container, bg=C["bg"])
        hdr.pack(fill=tk.X, pady=(0, 24))
        
        back_btn = tk.Label(hdr, text="← BACK", font=FONTS["badge"], 
                            fg=C["accent"], bg=C["bg"], cursor="hand2", padx=8, pady=4)
        back_btn.pack(side=tk.LEFT)
        back_btn.bind("<Button-1>", lambda e: self._back_to_main())
        
        tk.Label(hdr, text=node.name.upper(), font=FONTS["h3"], 
                 fg=C["text_p"], bg=C["bg"]).pack(side=tk.LEFT, padx=16)

        # Content area
        content = tk.Frame(container, bg=C["bg"])
        content.pack(fill=tk.BOTH, expand=True)
        
        # Row 1: Key Stats
        r1 = tk.Frame(content, bg=C["bg"])
        r1.pack(fill=tk.X, pady=(0, 16))
        
        def detail_stat(parent, label, color):
            c = card(parent, padx=20, pady=20)
            c.pack(side=tk.LEFT, padx=(0, 16), fill=tk.BOTH, expand=True)
            tk.Label(c, text=label, font=FONTS["badge"], fg=C["text_s"], bg=C["surface"]).pack(anchor="w")
            val = tk.Label(c, text="—", font=FONTS["h2"], fg=color, bg=C["surface"])
            val.pack(anchor="w", pady=(8, 0))
            return val

        v_util = detail_stat(r1, "CORE UTILIZATION", C["accent"])
        v_vram = detail_stat(r1, "MEMORY USAGE", "#A855F7")
        v_temp = detail_stat(r1, "TEMPERATURE", C["amber"])
        v_pwr  = detail_stat(r1, "POWER DRAW", C["red"])
        
        # Row 2: Large Sparklines
        r2 = tk.Frame(content, bg=C["bg"])
        r2.pack(fill=tk.X, pady=(0, 16))
        
        def large_spark(parent, title, color):
            f = card(parent, padx=16, pady=16)
            f.pack(side=tk.LEFT, padx=(0, 16), fill=tk.BOTH, expand=True)
            tk.Label(f, text=title, font=FONTS["badge"], fg=C["muted"], bg=C["surface"]).pack(anchor="w")
            sp = SparkLine(f, width=400, height=120, color=color)
            sp.pack(fill=tk.X, pady=12)
            return sp

        s_util = large_spark(r2, "UTILIZATION HISTORY", C["accent"])
        s_vram = large_spark(r2, "VRAM HISTORY", "#A855F7")
        
        # Save trackers for metric updates
        container.trackers = {
            "util": v_util, "vram": v_vram, "temp": v_temp, "pwr": v_pwr,
            "s_util": s_util, "s_vram": s_vram
        }
        
        return container

    # ── Actions ───────────────────────────────────────────────────────────────

    def _run_gpu_detection(self):
        self._diag_append("--- Re-detecting GPUs ---")
        threading.Thread(target=self._do_gpu_detection, daemon=True).start()

    def _do_gpu_detection(self):
        try:
            nodes = enumerate_gpus() if MODULES_OK else self._demo_nodes()
            self._gpu_nodes = nodes
            self.root.after(0, self._populate_gpu_cards)
            lines = [f"  GPU{n.id}: {n.name}  {n.vram_gb}GB  {n.role.value}" for n in nodes]
            self._diag_append(f"Found {len(nodes)} GPU(s):\n" + "\n".join(lines))
        except Exception as e:
            self._diag_append(f"ERROR: {e}")

    def _run_pcie_test(self):
        self._diag_append("--- PCIe Bandwidth Analysis ---")
        threading.Thread(target=self._do_pcie_test, daemon=True).start()

    def _do_pcie_test(self):
        try:
            if not self._gpu_nodes or not self._memory_analyzer:
                self._diag_append("No GPU nodes registered.")
                return

            links = []
            for n in self._gpu_nodes:
                links.append(PcieLink(gen=n.pcie.gen, width=n.pcie.width))

            vrams = [n.vram_mb for n in self._gpu_nodes]
            report = self._memory_analyzer.full_report(links, vrams)
            self._diag_append(report)
        except Exception as e:
            self._diag_append(f"ERROR: {e}")

    def _run_full_report(self):
        self._diag_append("--- Full System Report ---")
        threading.Thread(target=self._do_full_report, daemon=True).start()

    def _do_full_report(self):
        try:
            lines = ["MGR-S System Report", f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                     f"GPUs: {len(self._gpu_nodes)}", ""]
            for n in self._gpu_nodes:
                lines.append(f"  [{n.role.value}] GPU{n.id}: {n.name}")
                lines.append(f"    VRAM: {n.vram_gb}GB  Driver: {n.driver_version}")
                lines.append(f"    Vulkan: {n.vulkan_support}")
                lines.append(f"    PCIe: Gen{n.pcie.gen}x{n.pcie.width} → {n.pcie.link_type}")
                lines.append("")

            if self._scheduler:
                s = self._scheduler.get_status_summary()
                lines.append(f"Scheduler: frame {s['frame_id']}, budget {s['frame_budget_ms']:.1f}ms")
                for gid, info in s["nodes"].items():
                    lines.append(f"  GPU{gid}: weight={info['weight']} state={info['state']} miss={info['miss_rate']}%")

            self._diag_append("\n".join(lines))
        except Exception as e:
            self._diag_append(f"ERROR: {e}")

    def _apply_settings(self):
        self._log("Settings applied", "OK")
        messagebox.showinfo("Settings", "Settings applied.\nRestart required for some changes.")

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _set_state(self, state: str):
        self._runtime_state = state
        colors = {"RUNNING": C["green"], "DEGRADED": C["amber"],
                  "ERROR": C["red"], "STARTING": C["amber"]}
        self.root.after(0, lambda: self._state_pill.config(
            text=state.upper(), fg="white" # PillBadge handles its own styling usually
        ))

    def _log(self, msg: str, severity: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{severity}] {msg}\n"
        def _append():
            self._log_text.configure(state="normal")
            self._log_text.insert(tk.END, entry, severity)
            self._log_text.see(tk.END)
            self._log_text.configure(state="disabled")
        self.root.after(0, _append)
        log.info(f"[{severity}] {msg}")

    def _diag_append(self, text: str):
        def _append():
            self._diag_text.configure(state="normal")
            self._diag_text.insert(tk.END, text + "\n\n")
            self._diag_text.see(tk.END)
            self._diag_text.configure(state="disabled")
        self.root.after(0, _append)

    def _maybe_show_welcome(self):
        marker = os.path.join(os.path.dirname(__file__), "..", "first_launch.txt")
        if os.path.exists(marker):
            return
        self.root.after(500, self._show_welcome)

    def _show_welcome(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Welcome to MGR-S")
        dlg.geometry("520x420")
        dlg.resizable(False, False)
        dlg.configure(bg=C["bg"])
        dlg.grab_set()

        # Center
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 260
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 210
        dlg.geometry(f"+{x}+{y}")

        tk.Label(dlg, text="MGR-S", font=("Segoe UI", 24, "bold"),
                 fg=C["accent"], bg=C["bg"]).pack(pady=(30, 4))
        tk.Label(dlg, text="Multi-GPU Runtime System  v0.2 Alpha",
                 font=FONTS["body"], fg=C["muted"], bg=C["bg"]).pack()

        info = card(dlg, padx=16, pady=12)
        info.pack(padx=20, pady=20, fill=tk.X)

        lines = [
            ("What MGR-S does:", C["accent2"]),
            ("  • Explicit multi-GPU work scheduling (SFR + functional offload)", C["text"]),
            ("  • Real-time GPU telemetry monitoring", C["text"]),
            ("  • PCIe bandwidth analysis and transfer cost estimation", C["text"]),
            ("  • Dynamic tile-split balancing with degraded-node recovery", C["text"]),
            ("", None),
            ("What it does NOT do:", C["amber"]),
            ("  • Not SLI or CrossFire", C["text"]),
            ("  • Not a guaranteed performance boost", C["text"]),
            ("  • Not magic", C["text"]),
        ]
        for text, color in lines:
            if color:
                tk.Label(info, text=text, font=FONTS["body"],
                         fg=color, bg=C["panel"], anchor="w").pack(fill=tk.X)

        def ok():
            marker = os.path.join(os.path.dirname(__file__), "..", "first_launch.txt")
            try:
                with open(marker, "w") as f:
                    f.write("1")
            except:
                pass
            dlg.destroy()

        tk.Button(dlg, text="Get Started", command=ok,
                  bg=C["accent"], fg="white",
                  activebackground=C["accent2"], activeforeground="white",
                  font=FONTS["h3"], padx=20, pady=8, relief="flat",
                  cursor="hand2").pack(pady=8)

    def _handle_exit(self):
        if self._monitor:
            self._monitor.stop()
        if self._tray:
            self._tray.stop()
        self._log("Shutting down MGR-S…")
        self.root.after(800, self.root.destroy)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    root = tk.Tk()
    app = MgrsApp(root)
    root.mainloop()
