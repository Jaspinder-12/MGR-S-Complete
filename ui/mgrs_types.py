from dataclasses import dataclass, field
from enum import Enum
import time

class GpuVendor(Enum):
    NVIDIA = "NVIDIA"
    AMD    = "AMD"
    INTEL  = "Intel"
    UNKNOWN = "Unknown"

class GpuRole(Enum):
    AUTHORITY  = "Authority"
    ASSISTANT  = "Assistant"
    INACTIVE   = "Inactive"
    UNKNOWN    = "Unknown"

@dataclass
class PcieLink:
    gen: int = 0
    width: int = 0
    rebar_enabled: bool = False

    @property
    def bandwidth_gbps(self) -> float:
        per_lane = {1: 0.25, 2: 0.5, 3: 1.0, 4: 2.0, 5: 4.0}
        return per_lane.get(self.gen, 1.0) * self.width

    @property
    def link_type(self) -> str:
        bw = self.bandwidth_gbps
        if bw >= 32: return "DIRECT_P2P"
        elif bw >= 8: return "HOST_MEDIATED"
        else: return "THUNDERBOLT_DEGRADED"

@dataclass
class GpuNode:
    id: int
    name: str
    vendor: GpuVendor
    vram_mb: int
    role: GpuRole = GpuRole.UNKNOWN
    pcie: PcieLink = field(default_factory=PcieLink)
    driver_version: str = "Unknown"
    uuid: str = ""
    vulkan_support: bool = False
    compute_flops: float = 0.0
    is_active: bool = True
    is_authority: bool = False
    monitor_id: int = -1  # ID used by GpuMonitor (e.g. nvidia-smi index)

    @property
    def vram_gb(self) -> float:
        return round(self.vram_mb / 1024, 1)

@dataclass
class GpuMetrics:
    gpu_id: int
    name: str
    utilization_pct: float = 0.0      # GPU core usage %
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    temperature_c: float = 0.0
    power_draw_w: float = 0.0
    power_limit_w: float = 0.0
    clock_mhz: float = 0.0
    fan_speed_pct: float = 0.0
    pcie_tx_mbps: float = 0.0         # PCIe throughput TX
    pcie_rx_mbps: float = 0.0         # PCIe throughput RX
    timestamp: float = field(default_factory=time.time)

    @property
    def memory_used_pct(self) -> float:
        if self.memory_total_mb <= 0:
            return 0.0
        return round((self.memory_used_mb / self.memory_total_mb) * 100, 1)

    @property
    def memory_free_mb(self) -> float:
        return max(self.memory_total_mb - self.memory_used_mb, 0)

@dataclass
class SystemMetrics:
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    cpu_pct: float = 0.0

    @property
    def ram_used_pct(self) -> float:
        if self.ram_total_mb <= 0:
            return 0.0
        return round((self.ram_used_mb / self.ram_total_mb) * 100, 1)

class LinkQuality(Enum):
    EXCELLENT   = "DIRECT_P2P"
    GOOD        = "HOST_MEDIATED"
    LIMITED     = "HOST_MEDIATED_SLOW"
    FATAL       = "THUNDERBOLT_DEGRADED"
