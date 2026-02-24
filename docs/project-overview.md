# GPU Linking Project - Overview

## PROJECT SUMMARY
This project explores a software + hardware system for advanced GPU utilization, multi-GPU orchestration, performance scaling, and experimental architectures (e.g., multi-GPU interconnects, scheduling, and high-performance rendering / compute workflows).

Current focus: SOFTWARE-FIRST, PROTOTYPE-ONLY effort
Future scope: VR, BCI, GPU bridges (RESEARCH ONLY)

## DEVELOPMENT ENVIRONMENT
- Location: India
- Budget: Limited
- Tools: Open-source
- Hardware: Consumer-grade
- Design: Modular, inspectable

## SAFETY PRIORITY
Previous automation caused catastrophic data loss. Therefore:
- SAFETY > SPEED > CLEVERNESS
- ISOLATION > CONVENIENCE > OPTIMIZATION
- NON-DESTRUCTIVE BEHAVIOR > ALL

## ABSOLUTE SAFETY RULES
See [safety-guidelines.md](./safety-guidelines.md) for full details.

## PROJECT STRUCTURE

```
j:/GPU linking/
├── src/        # Human-written code (CURRENTLY: runtime/, vulkan/, app/)
├── gen/        # AI-generated code ONLY (TBD)
├── docs/       # Architecture, design, research
├── logs/       # Text-only logs of decisions and steps
├── scratch/    # Disposable experiments (can be deleted safely)
├── backups/    # Timestamped snapshots
├── tools/      # Scripts that NEVER self-execute
├── plans/      # Existing planning documents
├── assets/     # Documentation assets
└── build/      # Build artifacts (generated)
```

## EXISTING COMPONENTS

### Core Runtime (runtime/)
- **Context Management**: Initialization, shutdown, device enumeration, resource allocation
- **Device Management**: Query capabilities, manage device-specific resources, execute commands
- **Resource Management**: Buffer/image creation, state transitions, sharing between devices
- **Command Scheduling**: Command buffer recording, submission, dependency management
- **Memory Management**: Allocation, pooling, budget management

### Vulkan Backend (vulkan/)
- **Vulkan Context**: VkInstance, VkPhysicalDevice, VkDevice management
- **Vulkan Device**: VkQueue, VkCommandPool management
- **Vulkan Memory**: VkMemory allocation, type matching
- **Vulkan Resources**: VkBuffer, VkImage creation
- **Vulkan Commands**: VkCommandBuffer recording and submission
- **Timeline Semaphores**: VkSemaphore synchronization

### Application Layer (app/)
- Main entry point and controller
- Test for unavailable API

## ARCHITECTURE

### Layered Approach
```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
├─────────────────────────────────────────────────────────────────┤
│                 Runtime API (C++/Python)                        │
├─────────────────────────────────────────────────────────────────┤
│                  Core Runtime Library                            │
│  - Context Management                                           │
│  - Device Management                                            │
│  - Resource Management                                         │
│  - Command Scheduling                                           │
│  - Memory Management                                           │
├─────────────────────────────────────────────────────────────────┤
│                  Backend Abstraction Layer                      │
│  - Vulkan Backend                                               │
│  - DirectX 12 Backend (future)                                │
│  - Metal Backend (future)                                      │
│  - OpenGL Backend (future)                                    │
└─────────────────────────────────────────────────────────────────┘
```

## DEVELOPMENT PLAN

### Phase 1: Foundation (Q1 2026) - IN PROGRESS

**Core Runtime**
- [ ] Context initialization and shutdown
- [ ] Device enumeration and selection
- [ ] Memory management and allocation
- [ ] Resource creation (buffers, images)
- [ ] Command buffer recording and submission
- [ ] Timeline semaphore synchronization

**Vulkan Backend**
- [ ] Vulkan context initialization
- [ ] Vulkan device management
- [ ] Vulkan memory allocation
- [ ] Vulkan buffer and image creation
- [ ] Vulkan command buffer management
- [ ] Vulkan timeline semaphore integration

**Documentation**
- [x] Safety guidelines
- [ ] API documentation (Doxygen)
- [ ] Architecture documentation
- [ ] Getting started guide

**Testing**
- [ ] Unit tests for core functionality
- [ ] Vulkan backend integration tests
- [ ] Performance benchmarks

### Phase 2: Graphics Pipeline (Q2 2026)

**Core Runtime**
- [ ] Compute pipeline creation
- [ ] Graphics pipeline creation
- [ ] Resource binding and descriptor sets
- [ ] Command buffer reuse and caching
- [ ] Pipeline state management

**Vulkan Backend**
- [ ] Vulkan pipeline creation
- [ ] Vulkan descriptor set management
- [ ] Vulkan command buffer recording
- [ ] Vulkan pipeline cache support

**Integration**
- [ ] UE5 plugin integration
- [ ] Unity plugin integration (basic)
- [ ] Example applications

**Testing**
- [ ] Graphics pipeline tests
- [ ] Compute shader tests
- [ ] Stress tests

### Phase 3: Advanced Features (Q3 2026)

**Core Runtime**
- [ ] Ray tracing pipeline creation
- [ ] Resource streaming support
- [ ] Async command execution
- [ ] Multi-threaded rendering
- [ ] Memory budget management

**Vulkan Backend**
- [ ] Vulkan ray tracing support (NV_ray_tracing)
- [ ] Vulkan asynchronous operations
- [ ] Vulkan memory budget extension
- [ ] Vulkan device group support (multi-GPU)

**Tools and Debugging**
- [ ] Debug marker support
- [ ] Performance profiling tools
- [ ] Error handling and reporting
- [ ] Validation layer integration

**Documentation**
- [ ] Tutorials and examples
- [ ] FAQ and troubleshooting
- [ ] Performance optimization guide

### Phase 4: Additional Backends (Q4 2026)

**DirectX 12 Backend**
- [ ] D3D12 context initialization
- [ ] D3D12 resource management
- [ ] D3D12 command buffer management
- [ ] D3D12 synchronization
- [ ] D3D12 pipeline creation

**Metal Backend**
- [ ] Metal context initialization
- [ ] Metal resource management
- [ ] Metal command buffer management
- [ ] Metal synchronization
- [ ] Metal pipeline creation

**Platform Support**
- [ ] Android support
- [ ] iOS support
- [ ] macOS support (Metal)

**Integration**
- [ ] Improved UE5 plugin
- [ ] Improved Unity plugin
- [ ] Example applications for mobile

### Phase 5: Optimization and Polish (Q1 2027)

**Performance Optimization**
- [ ] Memory allocation optimization
- [ ] Command buffer reuse
- [ ] Resource streaming improvements
- [ ] Pipeline caching
- [ ] Asynchronous operations

**Compatibility**
- [ ] Vulkan 1.3 support
- [ ] DirectX 12 Ultimate support
- [ ] Metal 3 support
- [ ] Cross-vendor compatibility

**Stability and Reliability**
- [ ] Extensive testing
- [ ] Bug fixes
- [ ] Performance profiling
- [ ] Memory leak detection

**Documentation and Examples**
- [ ] Complete API documentation
- [ ] Advanced tutorials
- [ ] Performance benchmarks
- [ ] Real-world examples

## KEY TECHNICAL FEATURES

### Timeline Semaphore Synchronization
Simplifies GPU-CPU and GPU-GPU synchronization

### Low-Overhead API Design
Minimizes driver overhead with direct command buffer recording

### Smart Memory Management
Automatic memory type matching and pooling

### Multi-GPU Support
- Device enumeration and selection
- Resource sharing between GPUs
- Command submission to specific devices
- Load balancing across devices

### Virtual Memory
- Page fault handling
- Overcommitment detection
- Memory statistics monitoring

### Power Management
- Power state control
- Power consumption monitoring
- Temperature-based throttling

### Distributed Rendering
- Network communication
- Remote resource creation
- Frame distribution across nodes

## OPEN-SOURCE DEPENDENCIES

- **Vulkan SDK**: Graphics API
- **Google Test**: Testing framework
- **CMake**: Build system
- **Conan**: Package manager

## COMPILER & PLATFORM SUPPORT

**Compilers**
- Visual Studio 2019/2022 (Windows)
- GCC/Clang (Linux/macOS)

**Target Platforms**
- Windows 10+
- Linux
- macOS
- Android (future)
- iOS (future)

## VERSION CONTROL

- Git initialized on master branch
- All changes committed with clear explanations
- No rebasing, force pushes, or history rewriting
- Recovery-focused approach

## FAILURE HANDLING

- Assume things WILL break
- Always design rollback paths
- Never assume lost data can be recreated
- If ambiguity exists, STOP and ask
- If an instruction risks data, REFUSE and explain why

## CONTINUOUS IMPROVEMENT

- Every complex idea must have a simple baseline version
- Experimental features labeled EXPERIMENTAL
- Clear separation between what's real today, experimental, and future research
- Boring, reliable engineering over clever tricks

## NEXT STEPS

1. Commit remaining code changes
2. Create backup of current state
3. Begin Phase 1 implementation
4. Documentation parallel to coding
