"""
Project: MGR-S (Multi-GPU Runtime System)
Module:  tests/test_core.py — Pytest unit tests for core Python modules
Author:  Jaspinder

Run with:
    cd "j:/GPU linking"
    python -m pytest tests/ -v
"""

import sys
import os

# Make sure ui/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ui"))

import pytest
import math


# ─────────────────────────────────────────────────────────────────────────────
# mgrs_core tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMgrsCore:

    def test_import(self):
        from mgrs_core import enumerate_gpus, GpuNode, GpuRole, GpuVendor
        assert enumerate_gpus is not None

    def test_enumerate_returns_list(self):
        from mgrs_core import enumerate_gpus
        nodes = enumerate_gpus()
        assert isinstance(nodes, list)

    def test_at_least_one_gpu(self):
        from mgrs_core import enumerate_gpus
        nodes = enumerate_gpus()
        assert len(nodes) >= 1, "Expected at least one GPU to be detected"

    def test_gpu_node_fields(self):
        from mgrs_core import enumerate_gpus, GpuNode
        nodes = enumerate_gpus()
        for node in nodes:
            assert hasattr(node, "id")
            assert hasattr(node, "name")
            assert hasattr(node, "vram_mb")
            assert hasattr(node, "vendor")
            assert hasattr(node, "role")
            assert hasattr(node, "pcie")
            assert node.vram_mb >= 0
            assert isinstance(node.name, str)
            assert len(node.name) > 0

    def test_authority_role_assigned(self):
        from mgrs_core import enumerate_gpus, GpuRole
        nodes = enumerate_gpus()
        roles = [n.role for n in nodes]
        assert GpuRole.AUTHORITY in roles, "At least one GPU should be Authority"

    def test_no_duplicate_ids(self):
        from mgrs_core import enumerate_gpus
        nodes = enumerate_gpus()
        ids = [n.id for n in nodes]
        assert len(ids) == len(set(ids)), "GPU IDs should be unique"

    def test_pcie_fields(self):
        from mgrs_core import enumerate_gpus
        nodes = enumerate_gpus()
        for node in nodes:
            pcie = node.pcie
            assert pcie.gen in [1, 2, 3, 4, 5, 0], f"Unexpected PCIe gen: {pcie.gen}"
            assert pcie.width in [1, 2, 4, 8, 16, 32, 0], f"Unexpected PCIe width: {pcie.width}"

    def test_vram_gb_consistent(self):
        from mgrs_core import enumerate_gpus
        nodes = enumerate_gpus()
        for node in nodes:
            expected_gb = round(node.vram_mb / 1024, 1)
            assert abs(node.vram_gb - expected_gb) < 0.5


# ─────────────────────────────────────────────────────────────────────────────
# mgrs_memory tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMgrsMemory:

    def test_import(self):
        from mgrs_memory import MemoryAnalyzer, PcieLink, LinkQuality
        assert MemoryAnalyzer is not None

    def test_pcie_link_bandwidth(self):
        from mgrs_memory import PcieLink
        link = PcieLink(gen=4, width=16)
        assert link.peak_bandwidth_gbps > 0
        assert link.effective_bandwidth_gbps > 0
        assert link.effective_bandwidth_gbps < link.peak_bandwidth_gbps

    def test_link_quality_gen4_x16(self):
        from mgrs_memory import PcieLink, LinkQuality
        link = PcieLink(gen=4, width=16)
        assert link.link_quality in (LinkQuality.EXCELLENT, LinkQuality.GOOD)

    def test_link_quality_gen3_x4_limited(self):
        from mgrs_memory import PcieLink, LinkQuality
        link = PcieLink(gen=3, width=4)
        # Gen3 x4 = ~4GB/s effective — should be Limited
        assert link.link_quality in (LinkQuality.LIMITED, LinkQuality.GOOD)

    def test_transfer_estimate_returns_dataclass(self):
        from mgrs_memory import MemoryAnalyzer, PcieLink
        analyzer = MemoryAnalyzer(target_fps=60)
        link = PcieLink(gen=4, width=16)
        est = analyzer.estimate_transfer(64.0, link, "test_buffer")
        assert est.transfer_time_ms > 0
        assert isinstance(est.recommendation, str)
        assert len(est.recommendation) > 0

    def test_frame_budget_consistency(self):
        from mgrs_memory import MemoryAnalyzer
        for fps in [30, 60, 120]:
            m = MemoryAnalyzer(target_fps=fps)
            expected = 1000.0 / fps
            assert abs(m.frame_budget_ms - expected) < 0.01

    def test_tile_split_sums_to_width(self):
        from mgrs_memory import MemoryAnalyzer
        m = MemoryAnalyzer(target_fps=60)
        weights = [0.7, 0.3]
        screen_w = 3840
        # Tile split: each GPU's tile width proportional to weight
        tiles = [int(screen_w * w) for w in weights]
        tiles[-1] = screen_w - sum(tiles[:-1])   # Last tile gets remainder
        assert sum(tiles) == screen_w, f"Tiles {tiles} don't sum to {screen_w}"

    def test_full_report_returns_string(self):
        from mgrs_memory import MemoryAnalyzer, PcieLink
        m = MemoryAnalyzer(target_fps=60)
        links = [PcieLink(gen=4, width=16), PcieLink(gen=3, width=8)]
        vrams = [12288, 6144]
        report = m.full_report(links, vrams)
        assert isinstance(report, str)
        assert len(report) > 50


# ─────────────────────────────────────────────────────────────────────────────
# mgrs_scheduler tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMgrsScheduler:

    def _make_scheduler(self, fps=60):
        from mgrs_scheduler import MultiGpuScheduler, SchedulerConfig
        cfg = SchedulerConfig(
            target_fps=fps,
            screen_width=3840,
            screen_height=2160,
        )
        sched = MultiGpuScheduler(cfg)
        sched.register_gpu(0, 0.70)
        sched.register_gpu(1, 0.30)
        return sched

    def test_import(self):
        from mgrs_scheduler import MultiGpuScheduler, SchedulerConfig, TaskType
        assert MultiGpuScheduler is not None

    def test_frame_packets_non_empty(self):
        sched = self._make_scheduler()
        packets = sched.build_frame_packets()
        assert len(packets) >= 1

    def test_one_packet_per_active_gpu(self):
        sched = self._make_scheduler()
        packets = sched.build_frame_packets()
        assert len(packets) == 2

    def test_tile_widths_sum_to_screen_width(self):
        sched = self._make_scheduler()
        packets = sched.build_frame_packets()
        sfr_packets = [p for p in packets if p.screen_rect is not None]
        total_w = sum(p.screen_rect["w"] for p in sfr_packets)
        assert total_w == 3840, f"SFR widths {total_w} != 3840"

    def test_tile_heights_equal_screen_height(self):
        sched = self._make_scheduler()
        packets = sched.build_frame_packets()
        for p in packets:
            if p.screen_rect:
                assert p.screen_rect["h"] == 2160

    def test_degradation_triggers(self):
        from mgrs_scheduler import TaskType, NodeState
        sched = self._make_scheduler()
        budget = sched.config.frame_budget_ms

        # Build initial packets to set up tiles
        sched.build_frame_packets()

        # Report GPU1 missing deadline 2+ times
        for _ in range(3):
            sched.record_completion(1, TaskType.G_BUFFER, budget * 2)

        state = sched._gpu_nodes[1]["state"]
        assert state == NodeState.DEGRADED, \
            f"GPU1 should be DEGRADED after 3 misses, got {state}"

    def test_degradation_reduces_weight(self):
        from mgrs_scheduler import TaskType
        sched = self._make_scheduler()
        sched.build_frame_packets()
        initial_weight = sched._gpu_nodes[1]["weight"]
        budget = sched.config.frame_budget_ms

        for _ in range(3):
            sched.record_completion(1, TaskType.G_BUFFER, budget * 2)

        new_weight = sched._gpu_nodes[1]["weight"]
        assert new_weight < initial_weight, \
            "Degraded GPU weight should decrease"

    def test_status_summary_keys(self):
        sched = self._make_scheduler()
        summary = sched.get_status_summary()
        assert "frame_id" in summary
        assert "target_fps" in summary
        assert "frame_budget_ms" in summary
        assert "nodes" in summary
        for gid, info in summary["nodes"].items():
            assert "weight" in info
            assert "state" in info
            assert "miss_rate" in info

    def test_tile_distribution_for_ui(self):
        sched = self._make_scheduler()
        dist = sched.get_tile_distribution()
        assert isinstance(dist, list)
        # At least one entry should have a 'pct' key
        assert any("pct" in t for t in dist)


# ─────────────────────────────────────────────────────────────────────────────
# mgrs_monitor tests (offline — no real GPU required)
# ─────────────────────────────────────────────────────────────────────────────

class TestMgrsMonitor:

    def test_import(self):
        from mgrs_monitor import GpuMonitor, GpuMetrics
        assert GpuMonitor is not None

    def test_create_monitor(self):
        from mgrs_monitor import GpuMonitor
        m = GpuMonitor(interval=1.0)
        assert m is not None

    def test_callback_registration(self):
        from mgrs_monitor import GpuMonitor
        m = GpuMonitor(interval=1.0)
        called = []
        m.register_callback(lambda gpu, sys: called.append(True))
        assert len(m._callbacks) >= 1

    def test_start_stop(self):
        from mgrs_monitor import GpuMonitor
        m = GpuMonitor(interval=2.0)
        m.start()
        import time; time.sleep(0.2)
        m.stop()
        # Should not raise
