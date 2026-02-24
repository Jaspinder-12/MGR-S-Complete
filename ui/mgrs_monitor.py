#!/usr/bin/env python3
"""
Project: MGR-S (Multi-GPU Runtime System)
Module:  mgrs_monitor.py — Real-Time GPU Telemetry
Author:  Jaspinder
License: See LICENSE file

Polls live GPU metrics every N seconds using:
  - nvidia-smi  for NVIDIA GPUs
  - rocm-smi    for AMD GPUs
  - psutil      for system RAM
"""

import subprocess
import threading
import time
import platform
import json
import re
from typing import Dict, List, Optional, Callable
from collections import deque
import logging
from mgrs_types import GpuMetrics, SystemMetrics

log = logging.getLogger("mgrs.monitor")
MAX_HISTORY = 60


def _run(cmd: list, timeout: int = 4) -> str:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        return r.stdout.strip()
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Data collectors
# ─────────────────────────────────────────────────────────────────────────────

def _poll_nvidia() -> List[GpuMetrics]:
    metrics: List[GpuMetrics] = []
    query = (
        "index,name,"
        "utilization.gpu,memory.used,memory.total,"
        "temperature.gpu,power.draw,power.limit,"
        "clocks.current.graphics,fan.speed,"
        "pcie.link.gen.current,pcie.link.width.current"
    )
    out = _run(["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"])
    if not out:
        return metrics

    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 12:
            continue
        try:
            def safe_float(v, default=0.0):
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return default

            m = GpuMetrics(
                gpu_id=int(parts[0]),
                name=parts[1],
                utilization_pct=safe_float(parts[2]),
                memory_used_mb=safe_float(parts[3]),
                memory_total_mb=safe_float(parts[4]),
                temperature_c=safe_float(parts[5]),
                power_draw_w=safe_float(parts[6]),
                power_limit_w=safe_float(parts[7]),
                clock_mhz=safe_float(parts[8]),
                fan_speed_pct=safe_float(parts[9]),
            )
            metrics.append(m)
        except Exception as e:
            log.debug(f"nvidia-smi parse error: {e}")

    return metrics


def _poll_amd() -> List[GpuMetrics]:
    metrics: List[GpuMetrics] = []
    import json
    out = _run(["rocm-smi", "--json"])
    if not out:
        return metrics
    try:
        data = json.loads(out)
        for key, val in data.items():
            if not key.startswith("card"):
                continue
            gfx_id = int(key.replace("card", ""))

            def g(k, default=0.0):
                v = val.get(k, str(default))
                try:
                    return float(str(v).replace("%", "").strip())
                except:
                    return default

            vram_total = int(val.get("VRAM Total Memory (B)", 0)) // (1024 * 1024)
            vram_used  = int(val.get("VRAM Total Used Memory (B)", 0)) // (1024 * 1024)

            m = GpuMetrics(
                gpu_id=100 + gfx_id,
                name=val.get("Card series", f"AMD GPU {gfx_id}"),
                utilization_pct=g("GPU use (%)"),
                memory_used_mb=vram_used,
                memory_total_mb=vram_total,
                temperature_c=g("Temperature (Sensor edge) (C)"),
                power_draw_w=g("Average Graphics Package Power (W)"),
                clock_mhz=g("sclk clock speed:"),
                fan_speed_pct=g("Fan speed (%)"),
            )
            metrics.append(m)
    except Exception as e:
        log.debug(f"rocm-smi parse error: {e}")
    return metrics


def _poll_windows_native() -> List[GpuMetrics]:
    """Fallback: use a single PowerShell call for all GPU counters."""
    if platform.system() != "Windows":
        return []
    
    metrics: List[GpuMetrics] = []
    # Combine util and memory into one command to save process overhead
    ps_cmd = (
        "$u = Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue; "
        "$m = Get-Counter '\\GPU Adapter Memory(*)\\Dedicated Usage' -ErrorAction SilentlyContinue; "
        "($u.CounterSamples + $m.CounterSamples) | Select-Object Path, CookedValue | ConvertTo-Json"
    )
    
    out = _run(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=8)
    if not out: return []
    
    raw_data = {} # luid -> {util: X, mem: Y}
    try:
        data = json.loads(out)
        if not isinstance(data, list): data = [data]
        
        for item in data:
            path = item.get("Path", "").lower()
            val = item.get("CookedValue", 0.0)
            
            # Extract LUID components (High_Low)
            m = re.search(r"luid_(0x[0-9a-f]+)_(0x[0-9a-f]+)", path)
            if not m: continue
            
            high = int(m.group(1), 16)
            low = int(m.group(2), 16)
            luid = f"0x{high:x}_0x{low:x}"
            
            if luid not in raw_data: raw_data[luid] = {"util": 0.0, "mem": 0.0}
            
            if "utilization" in path:
                # We take the max across all engines (3D, Video, etc.) for that LUID
                raw_data[luid]["util"] = max(raw_data[luid]["util"], float(val))
            elif "usage" in path:
                raw_data[luid]["mem"] = float(val) / (1024 * 1024)
    except Exception as e:
        log.debug(f"Combined PS parse error: {e}")

    for luid, stats in raw_data.items():
        metrics.append(GpuMetrics(
            gpu_id=-1, # Unmapped
            name=f"WMI_GPU_LUID_{luid}",
            utilization_pct=stats["util"],
            memory_used_mb=stats["mem"],
        ))
        
    return metrics


def _poll_system() -> SystemMetrics:
    try:
        import psutil
        vm = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=None)
        return SystemMetrics(
            ram_used_mb=vm.used / (1024 * 1024),
            ram_total_mb=vm.total / (1024 * 1024),
            cpu_pct=cpu,
        )
    except ImportError:
        return SystemMetrics()
    except Exception:
        return SystemMetrics()


# ─────────────────────────────────────────────────────────────────────────────
# Monitor class (runs a background polling thread)
# ─────────────────────────────────────────────────────────────────────────────

class GpuMonitor:
    """
    Background monitor that polls GPU metrics every `interval` seconds.
    Consumers register callbacks that are called with fresh GpuMetrics lists.

    Usage:
        monitor = GpuMonitor(interval=1.0)
        monitor.start()
        ...
        latest = monitor.get_latest()
        monitor.stop()
    """

    def __init__(self, interval: float = 1.0):
        self._interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest_gpu: List[GpuMetrics] = []
        self._latest_sys: SystemMetrics = SystemMetrics()
        self._history: Dict[int, deque] = {}
        self._callbacks: List[Callable] = []
        
        # Async polling for slow sources (Windows Native/WMI)
        self._win_metrics: List[GpuMetrics] = []
        self._win_thread: Optional[threading.Thread] = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="mgrs-monitor")
        self._thread.start()
        
        self._win_thread = threading.Thread(target=self._win_poll_loop, daemon=True, name="mgrs-win-poll")
        self._win_thread.start()
        
        log.info(f"GpuMonitor started (interval={self._interval}s)")

    def stop(self):
        self._running = False
        log.info("GpuMonitor stopping...")

    def register_callback(self, fn: Callable):
        """Register a function(gpu_metrics_list, system_metrics) called on each poll."""
        self._callbacks.append(fn)

    def get_latest(self) -> List[GpuMetrics]:
        with self._lock:
            return list(self._latest_gpu)

    def get_latest_system(self) -> SystemMetrics:
        with self._lock:
            return self._latest_sys

    def get_history(self, gpu_id: int) -> List[GpuMetrics]:
        with self._lock:
            return list(self._history.get(gpu_id, deque()))

    def _win_poll_loop(self):
        """Slow cycle for expensive WMI/PowerShell metrics."""
        while self._running:
            try:
                metrics = _poll_windows_native()
                with self._lock:
                    self._win_metrics = metrics
            except Exception as e:
                log.debug(f"Win poller error: {e}")
            
            # Polling this frequently is expensive and unnecessary
            time.sleep(2.0)

    def _poll_loop(self):
        """Fast cycle for low-latency metrics (NVIDIA-SMI, etc.)."""
        while self._running:
            start = time.time()
            try:
                # Fast sources
                nvidia_metrics = _poll_nvidia()
                amd_metrics = _poll_amd()
                
                with self._lock:
                    # Combine fast metrics with latest async Windows metrics
                    gpu_metrics = nvidia_metrics + amd_metrics + self._win_metrics
                    sys_metrics = _poll_system()
                    
                    self._latest_gpu = gpu_metrics
                    self._latest_sys = sys_metrics
                    for m in gpu_metrics:
                        if m.gpu_id not in self._history:
                            self._history[m.gpu_id] = deque(maxlen=MAX_HISTORY)
                        self._history[m.gpu_id].append(m)

                for cb in self._callbacks:
                    try:
                        cb(gpu_metrics, sys_metrics)
                    except Exception as e:
                        log.warning(f"Monitor callback error: {e}")

            except Exception as e:
                log.warning(f"Monitor poll error: {e}")

            elapsed = time.time() - start
            sleep_time = max(0, self._interval - elapsed)
            time.sleep(sleep_time)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    monitor = GpuMonitor(interval=2.0)
    monitor.start()
    for _ in range(5):
        time.sleep(2)
        for m in monitor.get_latest():
            print(f"  GPU{m.gpu_id} {m.name}: {m.utilization_pct}% util | "
                  f"{m.memory_used_mb:.0f}/{m.memory_total_mb:.0f}MB VRAM | "
                  f"{m.temperature_c}°C | {m.power_draw_w}W")
        sys_m = monitor.get_latest_system()
        print(f"  SYS: CPU {sys_m.cpu_pct}% | RAM {sys_m.ram_used_mb:.0f}/{sys_m.ram_total_mb:.0f}MB")
    monitor.stop()
