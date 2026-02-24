#!/usr/bin/env python3
"""
Project: MGR-S (Multi-GPU Runtime System)
Module:  mgrs_scheduler.py — Dynamic Work-Packet Scheduler
Author:  Jaspinder
License: See LICENSE file

Implements the Director logic from the EAMR architecture:
  - Performance Heuristic (PH) updated every N frames
  - Tile-based split-frame scheduling
  - Degraded-node detection (if GPU misses deadline > 2× → reduce tile by 50%)
  - Functional decomposition fallback for iGPU/eGPU nodes
"""

import time
import threading
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

log = logging.getLogger("mgrs.scheduler")


class NodeState(Enum):
    ACTIVE    = "active"
    DEGRADED  = "degraded"     # Slow — tile reduced
    SUSPENDED = "suspended"    # Fully offloaded from SFR


class TaskType(Enum):
    G_BUFFER          = "G-Buffer (main pass)"
    SHADOW_MAP        = "Shadow Maps"
    GI_PROBES         = "GI Probe Ray Tracing"
    POST_PROCESS      = "Post-Processing"
    PHYSICS           = "Physics / Compute"
    UI_OVERLAY        = "UI Overlay"


@dataclass
class WorkPacket:
    """A unit of work assigned to one GPU node."""
    gpu_id: int
    task_type: TaskType
    screen_rect: Optional[Dict]    # {x, y, w, h}  — None for non-SFR tasks
    weight: float                  # Relative performance weight (0.0–1.0)
    deadline_ms: float             # Expected completion time
    state: NodeState = NodeState.ACTIVE


@dataclass
class PerformanceRecord:
    """Timing record for one GPU completing one frame pass."""
    gpu_id: int
    frame_id: int
    task_type: TaskType
    actual_ms: float
    deadline_ms: float

    @property
    def missed(self) -> bool:
        return self.actual_ms > self.deadline_ms


class SchedulerConfig:
    def __init__(
        self,
        target_fps: int = 60,
        screen_width: int = 3840,
        screen_height: int = 2160,
        ph_update_interval: int = 60,   # Update PH every N frames
        miss_threshold: int = 2,        # Misses before degradation
        degradation_factor: float = 0.5,
    ):
        self.target_fps = target_fps
        self.frame_budget_ms = 1000.0 / target_fps
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ph_update_interval = ph_update_interval
        self.miss_threshold = miss_threshold
        self.degradation_factor = degradation_factor


class MultiGpuScheduler:
    """
    The EAMR Director — schedules work packets across GPU nodes,
    dynamically adjusting tile splits based on real performance.
    """

    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self._lock = threading.Lock()
        self._frame_id = 0

        # GPU state: id → {weight, misses, state, consecutive_misses}
        self._gpu_nodes: Dict[int, Dict] = {}

        # Performance history: gpu_id → [PerformanceRecord, ...]
        self._perf_history: Dict[int, List[PerformanceRecord]] = {}

        log.info(f"Scheduler init: {self.config.target_fps}fps "
                 f"budget={self.config.frame_budget_ms:.1f}ms")

    # ─────────────────────────────────────────────────────────────────────
    # Node registration
    # ─────────────────────────────────────────────────────────────────────

    def register_gpu(self, gpu_id: int, initial_weight: float, is_igpu: bool = False):
        """Register a GPU with an initial performance weight (0.0–1.0)."""
        with self._lock:
            self._gpu_nodes[gpu_id] = {
                "weight": initial_weight,
                "state": NodeState.ACTIVE,
                "consecutive_misses": 0,
                "is_igpu": is_igpu,
                "total_frames": 0,
                "total_misses": 0,
            }
            self._perf_history[gpu_id] = []
            log.info(f"Registered GPU{gpu_id} weight={initial_weight:.2f} iGPU={is_igpu}")

    def register_gpus_from_nodes(self, gpu_nodes):
        """Convenience: register from mgrs_core.GpuNode list."""
        from mgrs_core import GpuRole, GpuVendor
        total_vram = sum(n.vram_mb for n in gpu_nodes) or 1

        for node in gpu_nodes:
            # Weight based on VRAM proportion — crude but good enough for init
            weight = node.vram_mb / total_vram
            is_igpu = (node.vendor == GpuVendor.INTEL and node.vram_mb < 2048)
            self.register_gpu(node.id, weight, is_igpu=is_igpu)

    # ─────────────────────────────────────────────────────────────────────
    # Work packet generation
    # ─────────────────────────────────────────────────────────────────────

    def build_frame_packets(self) -> List[WorkPacket]:
        """
        Build the work-packet list for the next frame.
        Returns one WorkPacket per active GPU node.
        """
        with self._lock:
            packets = []
            active = {gid: info for gid, info in self._gpu_nodes.items()
                      if info["state"] != NodeState.SUSPENDED}

            if not active:
                return []

            # Normalize weights among active nodes
            total_w = sum(info["weight"] for info in active.values())
            if total_w <= 0:
                total_w = 1.0

            ids = sorted(active.keys())
            current_x = 0

            for i, gid in enumerate(ids):
                info = active[gid]
                norm_w = info["weight"] / total_w

                # iGPUs and eGPUs: functional offload instead of SFR
                if info.get("is_igpu") or info["state"] == NodeState.DEGRADED:
                    task = TaskType.SHADOW_MAP if i > 0 else TaskType.G_BUFFER
                    packet = WorkPacket(
                        gpu_id=gid,
                        task_type=task,
                        screen_rect=None,
                        weight=norm_w,
                        deadline_ms=self.config.frame_budget_ms * 0.9,
                        state=info["state"],
                    )
                else:
                    # SFR tile
                    if i == len(ids) - 1:
                        tile_w = self.config.screen_width - current_x
                    else:
                        tile_w = int(self.config.screen_width * norm_w)

                    task = TaskType.G_BUFFER if i == 0 else TaskType.G_BUFFER
                    packet = WorkPacket(
                        gpu_id=gid,
                        task_type=task,
                        screen_rect={"x": current_x, "y": 0,
                                     "w": tile_w, "h": self.config.screen_height},
                        weight=norm_w,
                        deadline_ms=self.config.frame_budget_ms * 0.9,
                        state=info["state"],
                    )
                    current_x += tile_w

                packets.append(packet)
                info["total_frames"] += 1

            self._frame_id += 1

            # Update Performance Heuristic every N frames
            if self._frame_id % self.config.ph_update_interval == 0:
                self._update_performance_heuristic()

            return packets

    # ─────────────────────────────────────────────────────────────────────
    # Performance feedback
    # ─────────────────────────────────────────────────────────────────────

    def record_completion(self, gpu_id: int, task_type: TaskType, actual_ms: float):
        """Call after a GPU completes its assigned work packet."""
        with self._lock:
            if gpu_id not in self._gpu_nodes:
                return
            info = self._gpu_nodes[gpu_id]
            deadline = self.config.frame_budget_ms * 0.9
            rec = PerformanceRecord(
                gpu_id=gpu_id,
                frame_id=self._frame_id,
                task_type=task_type,
                actual_ms=actual_ms,
                deadline_ms=deadline,
            )
            self._perf_history[gpu_id].append(rec)

            # Keep only last 120 records
            if len(self._perf_history[gpu_id]) > 120:
                self._perf_history[gpu_id].pop(0)

            if rec.missed:
                info["consecutive_misses"] += 1
                info["total_misses"] += 1
                log.warning(f"GPU{gpu_id} missed deadline: {actual_ms:.1f}ms > {deadline:.1f}ms "
                             f"(#{info['consecutive_misses']})")

                # Degradation check
                if info["consecutive_misses"] >= self.config.miss_threshold:
                    if info["state"] == NodeState.ACTIVE:
                        info["state"] = NodeState.DEGRADED
                        info["weight"] *= self.config.degradation_factor
                        log.warning(f"GPU{gpu_id} DEGRADED — tile reduced 50% "
                                    f"(new weight={info['weight']:.3f})")
            else:
                info["consecutive_misses"] = 0
                # Slowly recover degraded nodes
                if info["state"] == NodeState.DEGRADED and info["total_frames"] % 60 == 0:
                    info["weight"] = min(info["weight"] * 1.1, 0.5)
                    log.info(f"GPU{gpu_id} recovering (weight={info['weight']:.3f})")

    # ─────────────────────────────────────────────────────────────────────
    # Performance Heuristic (PH) update
    # ─────────────────────────────────────────────────────────────────────

    def _update_performance_heuristic(self):
        """Rebalance tile splits based on recent average completion times."""
        # Lower avg completion time → higher weight → more pixels
        timings = {}
        for gid, history in self._perf_history.items():
            recent = [r.actual_ms for r in history[-60:]]
            if recent:
                timings[gid] = sum(recent) / len(recent)

        if not timings:
            return

        # Invert: faster GPU gets higher weight
        inv = {gid: 1.0 / (t + 0.001) for gid, t in timings.items()}
        total_inv = sum(inv.values())

        for gid, w in inv.items():
            if gid in self._gpu_nodes and self._gpu_nodes[gid]["state"] != NodeState.SUSPENDED:
                self._gpu_nodes[gid]["weight"] = w / total_inv

        ph_parts = [f"GPU{g}={self._gpu_nodes[g]['weight']:.2f}" for g in timings]
        log.info(f"PH update (frame {self._frame_id}): {', '.join(ph_parts)}")

    # ─────────────────────────────────────────────────────────────────────
    # Status queries
    # ─────────────────────────────────────────────────────────────────────

    def get_tile_distribution(self) -> List[dict]:
        """Return current tile assignments as a list of dicts (for UI)."""
        packets = self.build_frame_packets()
        result = []
        for p in packets:
            entry = {
                "gpu_id": p.gpu_id,
                "task_type": p.task_type.value,
                "weight_pct": round(p.weight * 100, 1),
                "state": p.state.value,
            }
            if p.screen_rect:
                entry.update(p.screen_rect)
                entry["pct"] = round((p.screen_rect["w"] / self.config.screen_width) * 100, 1)
            else:
                entry["pct"] = 0
            result.append(entry)
        return result

    def get_status_summary(self) -> dict:
        with self._lock:
            return {
                "frame_id": self._frame_id,
                "target_fps": self.config.target_fps,
                "frame_budget_ms": self.config.frame_budget_ms,
                "nodes": {
                    gid: {
                        "weight": round(info["weight"], 3),
                        "state": info["state"].value,
                        "miss_rate": round(
                            info["total_misses"] / max(info["total_frames"], 1) * 100, 1
                        ),
                    }
                    for gid, info in self._gpu_nodes.items()
                },
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import random

    cfg = SchedulerConfig(target_fps=60, screen_width=3840, screen_height=2160)
    sched = MultiGpuScheduler(cfg)
    sched.register_gpu(0, 0.70)   # RTX 4080
    sched.register_gpu(1, 0.30)   # RTX 3060

    print("Simulating 120 frames...\n")
    for frame in range(120):
        packets = sched.build_frame_packets()
        for p in packets:
            # Simulate GPU completion (GPU1 occasionally slow)
            latency = random.gauss(10, 2) if p.gpu_id == 0 else random.gauss(14, 4)
            sched.record_completion(p.gpu_id, p.task_type, latency)

    summary = sched.get_status_summary()
    print(f"\nFinal status after {summary['frame_id']} frames:")
    for gid, node in summary["nodes"].items():
        print(f"  GPU{gid}: weight={node['weight']:.2f}  state={node['state']}  "
              f"miss_rate={node['miss_rate']}%")

    print("\nCurrent tile distribution:")
    for t in sched.get_tile_distribution():
        print(f"  GPU{t['gpu_id']}: {t['task_type']} — {t['pct']}% of screen")
