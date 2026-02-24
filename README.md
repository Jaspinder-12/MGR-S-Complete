# MGR-S: Multi-GPU Runtime System

MGR-S is a comprehensive software-only, explicit, and engine-integrated multi-GPU runtime designed to replace legacy technologies like SLI. It focuses on modern graphics APIs (Vulkan, DX12) and provides explicit control over workload distribution across multiple execution nodes.

## Project Structure

- **Main Runtime**: Core components for frame decomposition, memory ownership, and timeline synchronization.
- **MGRS Bridge**: Integrated observability and task management bridge (formerly Herald), enabling remote monitoring and bridge capabilities for Claude Chat and Claude Code.
- **Release Directory**:
  - `mgrs_app.exe`: The primary release executable for the MGR-S application.

## Download

You can find the latest release files directly in the root of the repository:
- [Download mgrs_app.exe (Standalone)](https://github.com/Jaspinder-12/MGR-S-Complete/blob/main/mgrs_app.exe)
- [Download mgrs_setup.exe (Installer)](https://github.com/Jaspinder-12/MGR-S-Complete/blob/main/mgrs_setup.exe)

## Features

- **Explicit Workload Distribution**: Supports pass-level, tile-level, and task-level decomposition.
- **Advanced Synchronization**: Utilizes timeline semaphores and software-based synchronization for minimal overhead.
- **Asymmetric Support**: Designed to work with asymmetric GPU configurations.
- **Observability Integrated**: Built-in bridge for real-time monitoring and remote task execution.

## Getting Started

1.  **Environment**: Ensure Vulkan or DX12 compatible drivers are installed.
2.  **Build**: Use the provided scripts or project files in the root directory.
3.  **Bridge**: Navigate to `mgrs-bridge/` to set up the observability server.

---
*Created and maintained by [Jaspinder-12](https://github.com/Jaspinder-12)*
