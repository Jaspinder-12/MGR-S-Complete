# Repository Structure

This document describes the structure of the mg-rs repository.

## Root Directory Structure

```
mg-rs/
├── app/                 # Application layer
├── assets/              # Documentation and other assets
├── build/               # Build artifacts (generated)
├── docs/                # Documentation (Doxygen/Sphinx output)
├── plans/               # Planning documents
├── runtime/             # Core runtime library
├── vulkan/              # Vulkan backend implementation
├── CMakeLists.txt       # Root CMake configuration
├── conanfile.py         # Conan package manager configuration
├── repo-structure.md    # This file
└── test_compile.cpp     # Simple compilation test
```

## app/ - Application Layer

```
app/
├── main.cpp                     # Main application entry point
├── ApplicationController.h      # Application controller header
├── ApplicationController.cpp    # Application controller implementation
├── test_unavailable.cpp         # Test for unavailable API
└── CMakeLists.txt              # Application CMake configuration
```

## runtime/ - Core Runtime Library

```
runtime/
├── include/mgrs/
│   ├── context.h       # Context management
│   ├── device.h        # Device management
│   ├── memory.h        # Memory management
│   ├── resource.h      # Resource management (buffers, images, etc.)
│   ├── scheduler.h     # Scheduler interface
│   └── semaphore.h     # Timeline semaphore interface
└── src/core/
    └── context.cpp     # Context implementation
```

## vulkan/ - Vulkan Backend

```
vulkan/
├── include/mgrs/vulkan/
│   ├── vulkan_context.h        # Vulkan context implementation
│   ├── vulkan_device.h         # Vulkan device implementation
│   └── vulkan_memory.h         # Vulkan memory implementation
└── src/backend/
    ├── vulkan_context.cpp      # Vulkan context implementation
    ├── vulkan_device.cpp       # Vulkan device implementation
    └── vulkan_memory.cpp       # Vulkan memory implementation
```

## assets/ - Documentation and Assets

```
assets/
├── docs/                          # Markdown documentation
│   ├── context.md               # Context management documentation
│   └── ...
├── docs_files/                    # Supporting files for documentation
│   ├── checklist.md             # Task checklist
│   └── ...
└── ...
```

## plans/ - Planning Documents

```
plans/
├── architecture.md              # System architecture
├── frame-execution.md           # Frame execution pipeline
├── problem-solution.md          # Problem and solution approach
├── roadmap.md                   # Development roadmap
├── scaling.md                   # Scaling considerations
├── ue5-plugin.md               # UE5 plugin architecture
└── vulkan-api.md               # Vulkan API usage
```

## Build System

- **CMake**: Main build system
- **Conan**: Package manager for dependencies

## External Dependencies

- Vulkan SDK
- Google Test (for testing)

## Compiler Support

- Visual Studio 2019/2022 (Windows)
- GCC/Clang (Linux/macOS)

## Target Platforms

- Windows 10+
- Linux
- macOS
- Android (future)
- iOS (future)
