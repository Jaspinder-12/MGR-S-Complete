#!/usr/bin/env python3
"""
Project: MGR-S (Multi-GPU Runtime System)
Module:  mgrs_memory.py — PCIe Bandwidth & Memory Pool Analysis
Author:  Jaspinder
License: See LICENSE file

Models PCIe link capacity, cross-GPU transfer latency, and
memory pool strategy (Local VRAM / Host-Visible / BAR).
Based on the EAMR architecture design document.
"""

import math
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

log = logging.getLogger("mgrs.memory")


class LinkQuality(Enum):
    EXCELLENT   = "DIRECT_P2P"           # ≥ 32 GB/s — PCIe4 x16
    GOOD        = "HOST_MEDIATED"        # 8–31 GB/s — PCIe3 x16 / PCIe4 x8
    LIMITED     = "HOST_MEDIATED_SLOW"   # 2–7 GB/s  — PCIe3 x4 / PCIe4 x4
    FATAL       = "THUNDERBOLT_DEGRADED" # < 2 GB/s  — eGPU / Thunderbolt


@dataclass
class MemoryPool:
    """Represents one of the three EAMR memory pools."""
    name: str
    description: str
    size_mb: float
    bandwidth_gbps: float
    latency_us: float        # typical round-trip latency
    is_shared: bool          # accessible by CPU + all GPUs


@dataclass
class TransferEstimate:
    """Result of a cross-GPU transfer cost analysis."""
    size_mb: float
    bandwidth_gbps: float
    transfer_time_ms: float
    link_quality: LinkQuality
    is_fatal: bool           # True if transfer time exceeds frame budget
    frame_budget_ms: float
    overhead_pct: float      # Transfer time as % of frame budget
    recommendation: str


@dataclass
class PcieLink:
    gen: int
    width: int

    # Theoretical bandwidth table (GB/s per lane, one direction)
    _PER_LANE = {1: 0.25, 2: 0.5, 3: 1.0, 4: 2.0, 5: 4.0}

    @property
    def peak_bandwidth_gbps(self) -> float:
        per_lane = self._PER_LANE.get(self.gen, 1.0)
        return per_lane * self.width

    @property
    def effective_bandwidth_gbps(self) -> float:
        """Effective bandwidth ≈ 80% of theoretical (protocol overhead)."""
        return self.peak_bandwidth_gbps * 0.80

    @property
    def link_quality(self) -> LinkQuality:
        bw = self.effective_bandwidth_gbps
        if bw >= 32:
            return LinkQuality.EXCELLENT
        elif bw >= 8:
            return LinkQuality.GOOD
        elif bw >= 2:
            return LinkQuality.LIMITED
        else:
            return LinkQuality.FATAL

    def describe(self) -> str:
        return (f"PCIe Gen{self.gen} x{self.width} — "
                f"{self.effective_bandwidth_gbps:.1f} GB/s effective — "
                f"{self.link_quality.value}")


class MemoryAnalyzer:
    """
    Analyzes PCIe links between GPUs and estimates transfer costs
    for a given workload (e.g., 4K frame buffer = 64MB).
    """

    # 4K RGBA 16bpp = 3840×2160×8 bytes ≈ 64MB
    FRAME_4K_MB = 3840 * 2160 * 8 / (1024 * 1024)

    # Shadow map (4K, 32-bit depth) ≈ 32MB
    SHADOW_MAP_MB = 3840 * 2160 * 4 / (1024 * 1024)

    def __init__(self, target_fps: int = 60):
        self.target_fps = target_fps
        self.frame_budget_ms = 1000.0 / target_fps

    def estimate_transfer(
        self,
        size_mb: float,
        link: PcieLink,
        label: str = "buffer"
    ) -> TransferEstimate:
        """Estimate how long it takes to transfer `size_mb` over `link`."""
        bw = link.effective_bandwidth_gbps
        # Convert: size_mb / (bw GB/s) = size_mb / (bw * 1024 MB/s)
        if bw <= 0:
            transfer_ms = float("inf")
        else:
            transfer_ms = (size_mb / (bw * 1024)) * 1000.0

        overhead_pct = (transfer_ms / self.frame_budget_ms) * 100.0
        is_fatal = transfer_ms > (self.frame_budget_ms * 0.75)

        if link.link_quality == LinkQuality.FATAL:
            rec = (f"⛔ FATAL: eGPU/Thunderbolt link too slow for {label} SFR. "
                   f"Use functional offload (physics/shadows) instead.")
        elif overhead_pct > 20:
            rec = (f"⚠ HIGH COST: {label} transfer = {transfer_ms:.1f}ms "
                   f"({overhead_pct:.0f}% of frame budget). Consider lower resolution or async.")
        elif overhead_pct > 10:
            rec = (f"ℹ ACCEPTABLE: {label} transfer = {transfer_ms:.1f}ms "
                   f"({overhead_pct:.0f}% budget). Use timeline semaphores to overlap.")
        else:
            rec = (f"✅ OK: {label} transfer = {transfer_ms:.1f}ms "
                   f"({overhead_pct:.0f}% budget). No issues.")

        return TransferEstimate(
            size_mb=size_mb,
            bandwidth_gbps=bw,
            transfer_time_ms=transfer_ms,
            link_quality=link.link_quality,
            is_fatal=is_fatal,
            frame_budget_ms=self.frame_budget_ms,
            overhead_pct=overhead_pct,
            recommendation=rec,
        )

    def build_memory_pools(
        self,
        gpu_vram_mbs: List[float],
        system_ram_mb: float = 16384
    ) -> List[MemoryPool]:
        """
        Return the three EAMR memory pool definitions for the current system.
        """
        pools = []

        for i, vram in enumerate(gpu_vram_mbs):
            pools.append(MemoryPool(
                name=f"GPU{i} Local VRAM",
                description="High-bandwidth device-local. Render targets, static geometry.",
                size_mb=vram,
                bandwidth_gbps=400.0 if vram > 8192 else 250.0,  # Rough estimate
                latency_us=0.1,
                is_shared=False,
            ))

        pools.append(MemoryPool(
            name="Host-Visible Coherent (System RAM)",
            description="PCIe-accessible staging ring. Command buffers, constants, cross-GPU transfers.",
            size_mb=min(system_ram_mb * 0.25, 8192),
            bandwidth_gbps=50.0,   # DDR5 ~50-80 GB/s
            latency_us=100.0,
            is_shared=True,
        ))

        return pools

    def compute_tile_split(
        self,
        gpu_performance_ratios: List[float],
        screen_width: int = 3840,
        screen_height: int = 2160,
    ) -> List[dict]:
        """
        Split screen into horizontal tiles weighted by GPU performance ratios.
        Returns a list of {gpu_id, x, y, w, h, task_type} dicts.
        """
        total = sum(gpu_performance_ratios)
        tiles = []
        current_x = 0

        for i, ratio in enumerate(gpu_performance_ratios):
            tile_w = int(screen_width * (ratio / total))
            # The last GPU gets any remaining pixels
            if i == len(gpu_performance_ratios) - 1:
                tile_w = screen_width - current_x

            tiles.append({
                "gpu_id": i,
                "x": current_x,
                "y": 0,
                "w": tile_w,
                "h": screen_height,
                "task_type": "G_BUFFER" if i == 0 else "SHADOW_OR_GI",
                "pct": round((tile_w / screen_width) * 100, 1),
            })
            current_x += tile_w

        return tiles

    def full_report(self, links: List[PcieLink], gpu_vram_mbs: List[float]) -> str:
        """Generate a human-readable diagnostic report."""
        lines = ["=" * 60, "MGR-S Memory & PCIe Analysis Report", "=" * 60]

        lines.append(f"\n📐 Frame Budget: {self.frame_budget_ms:.1f}ms @ {self.target_fps}fps")
        lines.append(f"📏 4K Frame Buffer: {self.FRAME_4K_MB:.0f} MB")
        lines.append(f"📏 Shadow Map:      {self.SHADOW_MAP_MB:.0f} MB")

        lines.append("\n🔗 PCIe Links:")
        for i, link in enumerate(links):
            lines.append(f"  GPU{i}→GPU0: {link.describe()}")

        lines.append("\n📦 Transfer Estimates (4K Color Buffer):")
        for i, link in enumerate(links):
            est = self.estimate_transfer(self.FRAME_4K_MB, link, f"4K color (GPU{i}→GPU0)")
            lines.append(f"  {est.recommendation}")

        lines.append("\n📦 Transfer Estimates (Shadow Map):")
        for i, link in enumerate(links):
            est = self.estimate_transfer(self.SHADOW_MAP_MB, link, f"Shadow (GPU{i}→GPU0)")
            lines.append(f"  {est.recommendation}")

        lines.append("\n💾 Memory Pools:")
        pools = self.build_memory_pools(gpu_vram_mbs)
        for p in pools:
            shared_tag = "SHARED" if p.is_shared else "DEVICE-LOCAL"
            lines.append(f"  [{shared_tag}] {p.name}: {p.size_mb:.0f}MB @ {p.bandwidth_gbps:.0f}GB/s")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    analyzer = MemoryAnalyzer(target_fps=60)

    # Simulate RTX 4080 + RTX 3060 config
    links = [
        PcieLink(gen=4, width=16),  # 4080 primary — no self-transfer
        PcieLink(gen=4, width=8),   # 3060 assistant
    ]
    vrams = [16384, 12288]  # MB

    print(analyzer.full_report(links, vrams))

    tiles = analyzer.compute_tile_split([0.70, 0.30])
    print("\n🗂 Tile Split:")
    for t in tiles:
        print(f"  GPU{t['gpu_id']}: x={t['x']} w={t['w']} ({t['pct']}%) — {t['task_type']}")
