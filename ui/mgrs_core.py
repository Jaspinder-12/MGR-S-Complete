#!/usr/bin/env python3
"""
Project: MGR-S (Multi-GPU Runtime System)
Module:  mgrs_core.py — GPU Detection & Enumeration
Author:  Jaspinder
License: See LICENSE file

Detects all GPUs on the system using:
  - nvidia-smi  (NVIDIA GPUs)
  - rocm-smi    (AMD GPUs on ROCm)
  - wmi         (Windows fallback — all vendors)
  - DxDiag      (last-resort display adapter list)

Returns structured GpuNode objects used by the rest of the runtime.
"""

import subprocess
import re
import json
import platform
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

log = logging.getLogger("mgrs.core")


from mgrs_types import GpuVendor, GpuRole, PcieLink, GpuNode


# ─────────────────────────────────────────────────────────────────────────────
# Detection backends
# ─────────────────────────────────────────────────────────────────────────────

def _run(cmd: list, timeout: int = 5) -> str:
    """Run a subprocess command and return stdout, or '' on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        return result.stdout.strip()
    except Exception as e:
        log.debug(f"Command {cmd[0]} failed: {e}")
        return ""


def _detect_nvidia() -> List[GpuNode]:
    """Use nvidia-smi to enumerate NVIDIA GPUs."""
    nodes: List[GpuNode] = []
    query = "index,name,memory.total,driver_version,pcie.link.gen.current,pcie.link.width.current,uuid"
    out = _run(["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"])
    if not out:
        return nodes

    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            continue
        idx, name, vram_str, driver, pcie_gen, pcie_w, uuid = parts[:7]
        try:
            pcie = PcieLink(
                gen=int(pcie_gen) if pcie_gen.isdigit() else 3,
                width=int(pcie_w) if pcie_w.isdigit() else 16
            )
            node = GpuNode(
                id=int(idx),
                name=name,
                vendor=GpuVendor.NVIDIA,
                vram_mb=int(float(vram_str)),
                driver_version=driver,
                uuid=uuid,
                pcie=pcie,
                vulkan_support=True,
            )
            nodes.append(node)
            log.debug(f"NVIDIA GPU detected: {name} [{vram_str}MB] PCIe Gen{pcie_gen}x{pcie_w}")
        except Exception as e:
            log.warning(f"Failed to parse nvidia-smi line: {line} — {e}")

    return nodes


def _detect_amd() -> List[GpuNode]:
    """Use rocm-smi to enumerate AMD GPUs (only if ROCm installed)."""
    nodes: List[GpuNode] = []
    out = _run(["rocm-smi", "--json"])
    if not out:
        return nodes

    try:
        data = json.loads(out)
        for key, val in data.items():
            if not key.startswith("card"):
                continue
            gfx_id = int(key.replace("card", ""))
            name = val.get("Card series", "AMD GPU")
            vram_mb = int(val.get("VRAM Total Memory (B)", 0)) // (1024 * 1024)
            node = GpuNode(
                id=100 + gfx_id,  # Offset to avoid clash with NVIDIA IDs
                name=name,
                vendor=GpuVendor.AMD,
                vram_mb=vram_mb,
                driver_version=val.get("Driver Version", "Unknown"),
                vulkan_support=True,
            )
            nodes.append(node)
    except Exception as e:
        log.warning(f"rocm-smi parse error: {e}")

    return nodes


def _detect_wmi() -> List[GpuNode]:
    """Use Windows WMI (Win32_VideoController) as a fallback for all vendors."""
    nodes: List[GpuNode] = []
    if platform.system() != "Windows":
        return nodes

    try:
        import wmi  # type: ignore
        c = wmi.WMI()
        for i, ctrl in enumerate(c.Win32_VideoController()):
            name = ctrl.Name or "Unknown GPU"
            vram_bytes = getattr(ctrl, "AdapterRAM", 0) or 0
            vram_mb = int(vram_bytes) // (1024 * 1024)

            if "NVIDIA" in name.upper():
                vendor = GpuVendor.NVIDIA
            elif "AMD" in name.upper() or "RADEON" in name.upper():
                vendor = GpuVendor.AMD
            elif "INTEL" in name.upper():
                vendor = GpuVendor.INTEL
            else:
                vendor = GpuVendor.UNKNOWN

            node = GpuNode(
                id=200 + i,
                name=name,
                vendor=vendor,
                vram_mb=max(vram_mb, 0),
                driver_version=ctrl.DriverVersion or "Unknown",
                vulkan_support=(vendor in (GpuVendor.NVIDIA, GpuVendor.AMD, GpuVendor.INTEL)),
            )
            nodes.append(node)
            log.debug(f"WMI GPU: {name} [{vram_mb}MB]")
    except ImportError:
        log.info("wmi module not installed — skipping WMI detection")
    except Exception as e:
        log.warning(f"WMI detection error: {e}")

    return nodes


def _detect_dxdiag() -> List[GpuNode]:
    """Parse DxDiag XML output as a last-resort fallback (Windows only)."""
    nodes: List[GpuNode] = []
    if platform.system() != "Windows":
        return nodes

    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
    tmp.close()

    _run(["dxdiag", "/x", tmp.name], timeout=20)
    try:
        with open(tmp.name, "r", errors="replace") as f:
            content = f.read()

        displays = re.findall(r"<DisplayDevice>(.*?)</DisplayDevice>", content, re.DOTALL)
        for i, block in enumerate(displays):
            def tag(t):
                m = re.search(fr"<{t}>(.*?)</{t}>", block)
                return m.group(1).strip() if m else ""

            name = tag("CardName")
            vram_str = tag("DedicatedVideoMemory")
            vram_mb = 0
            m = re.match(r"(\d+)", vram_str.replace(",", ""))
            if m:
                vram_mb = int(m.group(1))
                if "GB" in vram_str.upper():
                    vram_mb *= 1024

            if not name:
                continue

            if "NVIDIA" in name.upper():
                vendor = GpuVendor.NVIDIA
            elif "AMD" in name.upper() or "RADEON" in name.upper():
                vendor = GpuVendor.AMD
            elif "INTEL" in name.upper():
                vendor = GpuVendor.INTEL
            else:
                vendor = GpuVendor.UNKNOWN

            nodes.append(GpuNode(
                id=300 + i,
                name=name,
                vendor=vendor,
                vram_mb=vram_mb,
                driver_version=tag("DriverVersion"),
                vulkan_support=(vendor in (GpuVendor.NVIDIA, GpuVendor.AMD)),
            ))
    except Exception as e:
        log.warning(f"DxDiag parse error: {e}")
    finally:
        try:
            os.unlink(tmp.name)
        except:
            pass

    return nodes


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def _deduplicate(nodes: List[GpuNode]) -> List[GpuNode]:
    """Remove duplicate GPUs detected by multiple backends (by name similarity)."""
    seen = {}
    result = []
    for n in nodes:
        key = n.name.strip().lower()
        if key not in seen:
            seen[key] = True
            result.append(n)
    return result


def _assign_roles(nodes: List[GpuNode]) -> List[GpuNode]:
    """
    Assign Authority / Assistant roles.
    Strategy:
      - Highest VRAM discrete GPU → Authority
      - Remaining Vulkan-capable GPUs → Assistant
      - Non-Vulkan (Intel iGPU without Vulkan driver, etc.) → Inactive
    """
    if not nodes:
        return nodes

    # Sort: discrete NVIDIA/AMD before Intel iGPU, then by VRAM
    def sort_key(n: GpuNode):
        discrete = 1 if n.vendor in (GpuVendor.NVIDIA, GpuVendor.AMD) else 0
        return (discrete, n.vram_mb)

    nodes.sort(key=sort_key, reverse=True)

    for i, n in enumerate(nodes):
        if i == 0:
            n.role = GpuRole.AUTHORITY
        elif n.vulkan_support:
            n.role = GpuRole.ASSISTANT
        else:
            n.role = GpuRole.INACTIVE

    # Re-assign IDs in sorted order, keeping track of monitor_id
    for i, n in enumerate(nodes):
        if n.monitor_id == -1:
            n.monitor_id = n.id
        n.id = i

    return nodes


def _detect_powershell() -> List[GpuNode]:
    """Use PowerShell and Registry to detect GPUs and their LUIDs accurately."""
    if platform.system() != "Windows":
        return []
    
    nodes: List[GpuNode] = []
    # Query Win32_VideoController for name/vram and PNPDeviceID
    ps_cmd = (
        "Get-CimInstance Win32_VideoController | Select-Object Name, PNPDeviceID, AdapterRAM | ConvertTo-Json"
    )
    out = _run(["powershell", "-Command", ps_cmd])
    if not out: return nodes
    
    try:
        import winreg
        data = json.loads(out)
        if not isinstance(data, list): data = [data]
        
        for i, item in enumerate(data):
            name = item.get("Name", "Unknown")
            pnp_id = item.get("PNPDeviceID", "")
            vram = int(item.get("AdapterRAM", 0)) / (1024*1024)
            
            # Retrieve LUID from Registry for robust matching
            luid_str = ""
            try:
                # Registry path: HKLM\SYSTEM\CurrentControlSet\Enum\<PNP_ID>
                reg_path = f"SYSTEM\\CurrentControlSet\\Enum\\{pnp_id}"
                reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                luid_bytes, _ = winreg.QueryValueEx(reg_key, "DeviceLUID")
                winreg.CloseKey(reg_key)
                
                if len(luid_bytes) == 8:
                        # LUID is LowPart (4 bytes) then HighPart (4 bytes) (little-endian)
                        low = int.from_bytes(luid_bytes[0:4], "little")
                        high = int.from_bytes(luid_bytes[4:8], "little")
                        luid_str = f"0x{high:x}_0x{low:x}"
            except: pass
            
            vendor = GpuVendor.UNKNOWN
            name_lower = name.lower()
            if "nvidia" in name_lower: vendor = GpuVendor.NVIDIA
            elif "amd" in name_lower or "radeon" in name_lower: vendor = GpuVendor.AMD
            elif "intel" in name_lower: vendor = GpuVendor.INTEL

            node = GpuNode(
                id=i, 
                name=name,
                vendor=vendor,
                vram_mb=int(vram),
                uuid=luid_str, # Use real registry LUID
                vulkan_support=("intel" not in name_lower) or ("uhd" not in name_lower),
                is_active=True
            )
            nodes.append(node)
    except Exception as e:
        log.debug(f"PowerShell discovery error: {e}")
        
    return nodes


def _enumerate_via_subprocess() -> List[GpuNode]:
    """
    Detect GPUs using subprocess calls to vendor-specific tools.
    """
    nodes: List[GpuNode] = []
    nodes.extend(_detect_nvidia())
    nodes.extend(_detect_amd())

    if not nodes:
        log.info("Primary detection found no GPUs — trying DxDiag…")
        nodes.extend(_detect_dxdiag())

    nodes = _deduplicate(nodes)
    return nodes

def _enumerate_via_wmi() -> List[GpuNode]:
    """
    Detect GPUs using WMI (Windows Management Instrumentation).
    """
    nodes: List[GpuNode] = []
    nodes.extend(_detect_wmi())
    nodes = _deduplicate(nodes)
    return nodes


def enumerate_gpus() -> List[GpuNode]:
    """
    Main entry point for GPU detection.
    Unified Strategy: Collect from all sources and deduplicate by name.
    """
    all_nodes: List[GpuNode] = []

    # 1. Try Native Vulkan Bridge
    try:
        from mgrs_bridge import enumerate_gpus_native
        native = enumerate_gpus_native()
        if native:
            all_nodes.extend(native)
            logging.info(f"Native bridge: {len(native)} GPUs found")
    except Exception as e:
        logging.debug(f"Native bridge failed: {e}")

    # 2. Try Subprocess Tools (nvidia-smi, etc.)
    sub_nodes = _enumerate_via_subprocess()
    if sub_nodes:
        all_nodes.extend(sub_nodes)
        logging.info(f"Subprocess tools: {len(sub_nodes)} GPUs found")

    # 3. Try PowerShell (replacement for WMI)
    ps_nodes = _detect_powershell()
    if ps_nodes:
        all_nodes.extend(ps_nodes)
        logging.info(f"PowerShell discovery: {len(ps_nodes)} GPUs found")

    # Final: Deduplicate and assign roles
    if not all_nodes:
        logging.warning("No GPUs detected via any method. Using generic fallback.")
        nodes = [GpuNode(id=0, name="Generic GPU 0", vendor=GpuVendor.UNKNOWN, vram_mb=4096)]
    else:
        nodes = _deduplicate(all_nodes)
        logging.info(f"Enumeration complete: {len(nodes)} unique GPUs found")

    _assign_roles(nodes)
    return nodes


def get_authority_gpu(nodes: List[GpuNode]) -> Optional[GpuNode]:
    for n in nodes:
        if n.role == GpuRole.AUTHORITY:
            return n
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    gpus = enumerate_gpus()
    for g in gpus:
        print(f"[{g.role.value.upper()}] {g.name} | {g.vram_gb}GB VRAM | "
              f"PCIe Gen{g.pcie.gen}x{g.pcie.width} ({g.pcie.link_type}) | "
              f"Vulkan={g.vulkan_support}")
