import subprocess
import json
import os
import sys
from typing import List, Optional
import logging

# Add parent directory to path for imports if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mgrs_types import GpuNode, GpuVendor, LinkQuality

def enumerate_gpus_native() -> Optional[List[GpuNode]]:
    """
    Executes the C++ mgrs_bridge.exe and returns a list of GpuNode objects.
    Returns None if the bridge is not found or fails.
    """
    # Potential paths for the bridge executable
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "mgrs_bridge.exe"),
        os.path.join(os.path.dirname(__file__), "..", "build", "Release", "mgrs_bridge.exe"),
        os.path.join(os.path.dirname(__file__), "..", "build", "Debug", "mgrs_bridge.exe"),
        os.path.join(os.getcwd(), "mgrs_bridge.exe"),
    ]
    
    bridge_path = None
    for p in possible_paths:
        if os.path.exists(p):
            bridge_path = p
            break
            
    if not bridge_path:
        logging.debug("Native Vulkan bridge not found.")
        return None
        
    try:
        result = subprocess.run([bridge_path], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            logging.warning(f"Native bridge failed with code {result.returncode}: {result.stderr}")
            return None
            
        data = json.loads(result.stdout)
        if "error" in data:
            logging.warning(f"Native bridge reported error: {data['error']}")
            return None
            
        nodes = []
        auth_index = data.get("authority_index", 0)
        
        for gpu in data.get("gpus", []):
            vendor = GpuVendor.UNKNOWN
            name_lower = gpu["name"].lower()
            if "nvidia" in name_lower: vendor = GpuVendor.NVIDIA
            elif "amd" in name_lower or "radeon" in name_lower: vendor = GpuVendor.AMD
            elif "intel" in name_lower: vendor = GpuVendor.INTEL
            
            is_auth = (gpu["index"] == auth_index)
            
            node = GpuNode(
                id=gpu["index"],
                name=gpu["name"],
                vendor=vendor,
                vram_mb=gpu["vram_mb"],
                driver_version=gpu.get("driver_version", "Unknown"),
                compute_flops=float(gpu["compute_flops"]) / 1e12, # Convert to TFLOPS
                vulkan_support=True,
                is_authority=is_auth,
                is_active=True
            )
            nodes.append(node)
            
        return nodes
        
    except Exception as e:
        logging.error(f"Failed to execute native bridge: {e}")
        return None

if __name__ == "__main__":
    # Test execution
    nodes = enumerate_gpus_native()
    if nodes:
        print(f"Found {len(nodes)} GPUs via native bridge:")
        for n in nodes:
            print(f" - {n.name} [{n.vram_mb} MB] {'(Authority)' if n.is_authority else ''}")
    else:
        print("Native bridge not available or failed.")
