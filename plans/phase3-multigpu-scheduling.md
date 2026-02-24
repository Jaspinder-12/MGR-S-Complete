# Phase 3: Multi-GPU Linking & Scheduling

## Purpose and Scope
Enable multi-GPU functionality for mg-rs, including device grouping, workload partitioning, memory management, and cross-GPU synchronization. This phase focuses on creating a scalable multi-GPU architecture that supports explicit control over how work is distributed across available GPUs.

## Architecture Additions

### 1. Device Group Management
```cpp
// runtime/include/mgrs/device_group.h
namespace mgrs {
    struct DeviceGroupCreateInfo {
        std::vector<uint32_t> deviceIndices;
        bool enableCrossDeviceSync;
        bool enableCrossDeviceMemory;
    };

    class DeviceGroup {
    public:
        static Result Create(Context* context, const DeviceGroupCreateInfo& info, DeviceGroup** outGroup);
        static void Destroy(DeviceGroup* group);

        virtual uint32_t GetDeviceCount() const = 0;
        virtual uint32_t GetDeviceIndex(uint32_t groupIndex) const = 0;
        virtual Device* GetDevice(uint32_t groupIndex) const = 0;
        virtual bool SupportsCrossDeviceSync() const = 0;
        virtual bool SupportsCrossDeviceMemory() const = 0;

        virtual ~DeviceGroup() = default;
    };
}
```

### 2. Workload Partitioning
```cpp
// runtime/include/mgrs/workload.h
namespace mgrs {
    enum class WorkloadType {
        COMPUTE,
        GRAPHICS,
        RAY_TRACING
    };

    struct WorkloadPartition {
        uint32_t deviceIndex;
        uint32_t start;
        uint32_t end;
        float weight;
    };

    class WorkloadScheduler {
    public:
        static Result Create(Context* context, WorkloadScheduler** outScheduler);
        static void Destroy(WorkloadScheduler* scheduler);

        virtual Result PartitionWorkload(
            WorkloadType type,
            uint32_t totalSize,
            const std::vector<float>& deviceWeights,
            std::vector<WorkloadPartition>& outPartitions
        ) = 0;

        virtual Result BalanceWorkload(
            const std::vector<uint64_t>& deviceLoads,
            std::vector<float>& outWeights
        ) = 0;

        virtual ~WorkloadScheduler() = default;
    };
}
```

### 3. Cross-GPU Memory Management
```cpp
// runtime/include/mgrs/cross_device_memory.h
namespace mgrs {
    enum class MemorySharingMode {
        EXCLUSIVE,
        CONCURRENT,
        SHARED
    };

    struct CrossDeviceMemoryCreateInfo {
        size_t size;
        VkMemoryPropertyFlags properties;
        MemorySharingMode sharingMode;
        std::vector<uint32_t> deviceIndices;
    };

    class CrossDeviceMemory {
    public:
        static Result Create(Context* context, const CrossDeviceMemoryCreateInfo& info, CrossDeviceMemory** outMemory);
        static void Destroy(CrossDeviceMemory* memory);

        virtual void* Map(uint32_t deviceIndex) = 0;
        virtual void Unmap(uint32_t deviceIndex) = 0;
        virtual Result CopyToDevice(uint32_t deviceIndex, const void* data, size_t size, size_t offset) = 0;
        virtual Result CopyFromDevice(uint32_t deviceIndex, void* data, size_t size, size_t offset) = 0;
        virtual Result CopyBetweenDevices(uint32_t srcDevice, uint32_t dstDevice, size_t size, size_t srcOffset, size_t dstOffset) = 0;

        virtual ~CrossDeviceMemory() = default;
    };
}
```

### 4. Cross-GPU Resource Management
```cpp
// runtime/include/mgrs/cross_device_resource.h
namespace mgrs {
    struct CrossDeviceResourceCreateInfo {
        ResourceType type;
        ResourceDesc desc;
        MemorySharingMode sharingMode;
        std::vector<uint32_t> deviceIndices;
    };

    class CrossDeviceResource {
    public:
        static Result Create(Context* context, const CrossDeviceResourceCreateInfo& info, CrossDeviceResource** outResource);
        static void Destroy(CrossDeviceResource* resource);

        virtual Resource* GetDeviceResource(uint32_t deviceIndex) = 0;
        virtual Result SynchronizeResource(uint32_t srcDevice, uint32_t dstDevice) = 0;
        virtual Result UpdateResource(const void* data, size_t size) = 0;

        virtual ~CrossDeviceResource() = default;
    };
}
```

### 5. Multi-GPU Command Scheduling
```cpp
// runtime/include/mgrs/multi_gpu_scheduler.h
namespace mgrs {
    struct MultiGPUCommandSubmitInfo {
        std::vector<CommandBuffer*> commandBuffers;
        std::vector<uint32_t> deviceIndices;
        TimelineSemaphore* signalSemaphore;
        uint64_t signalValue;
        std::vector<std::pair<TimelineSemaphore*, uint64_t>> waitSemaphores;
    };

    class MultiGPUScheduler {
    public:
        static Result Create(Context* context, MultiGPUScheduler** outScheduler);
        static void Destroy(MultiGPUScheduler* scheduler);

        virtual Result SubmitCommandBuffers(const MultiGPUCommandSubmitInfo& info) = 0;
        virtual Result WaitForCompletion(TimelineSemaphore* semaphore, uint64_t value, uint64_t timeout) = 0;
        virtual Result GetDeviceLoads(std::vector<uint64_t>& outLoads) = 0;

        virtual ~MultiGPUScheduler() = default;
    };
}
```

## Data Flow and Control Flow

### Device Discovery and Grouping
```
┌─────────────────────────────────────────────────────────┐
│ 1. Enumerate Devices                                    │
│    - Query physical devices                             │
│    - Check device capabilities                          │
│    - Determine device compatibility                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Create Device Groups                                 │
│    - Group compatible devices                            │
│    - Initialize cross-device synchronization            │
│    - Set up shared memory regions                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Create Cross-Device Resources                        │
│    - Allocate shared memory                             │
│    - Create resource views on each device                │
│    - Set up resource synchronization                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Partition and Schedule Workload                       │
│    - Analyze workload characteristics                     │
│    - Partition work across devices                        │
│    - Assign command buffers to devices                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Execute and Synchronize                               │
│    - Submit commands to each device                       │
│    - Synchronize across devices                           │
│    - Collect and analyze performance data                 │
└─────────────────────────────────────────────────────────┘
```

### Vulkan-Specific Considerations

#### Device Compatibility
- Check for `VK_KHR_device_group` extension
- Verify identical device properties and capabilities
- Ensure compatible memory heaps and types

#### Cross-Device Memory Sharing
- Use `VK_SHARING_MODE_CONCURRENT` for shared resources
- Implement device memory barriers for synchronization
- Support memory ownership transfers between devices

#### Command Scheduling
- Use `VkDeviceGroupCommandBufferBeginInfo` for device group commands
- Implement `vkCmdDispatchBase` for compute shader distribution
- Use `vkCmdSetDeviceMask` for per-command buffer device selection

## Failure Modes and Safeguards

### Device Incompatibility
- Check device compatibility before creating groups
- Fall back to single-GPU mode if device grouping fails
- Warn about performance implications of incompatible devices

### Resource Sharing Failures
- Validate memory sharing mode against device capabilities
- Fall back to exclusive memory if sharing fails
- Implement memory transfer fallback for incompatible resources

### Command Execution Failures
- Check command buffer validity before submission
- Handle device-specific command execution errors
- Implement fallback to secondary device if primary fails

## Incremental Implementation Steps

### Phase 3.1: Device Group Management
1. Create `DeviceGroup` interface and Vulkan implementation
2. Add device compatibility check
3. Implement device group creation and destruction
4. Add device group capability queries

### Phase 3.2: Cross-Device Memory Management
1. Create `CrossDeviceMemory` interface and Vulkan implementation
2. Implement shared memory allocation
3. Add memory mapping and copying operations
4. Implement memory ownership transfers

### Phase 3.3: Cross-Device Resource Management
1. Create `CrossDeviceResource` interface and Vulkan implementation
2. Add cross-device resource creation
3. Implement resource view creation on each device
4. Add resource synchronization methods

### Phase 3.4: Workload Partitioning
1. Create `WorkloadScheduler` interface and implementation
2. Implement workload partitioning algorithms
3. Add dynamic workload balancing
4. Implement device load monitoring

### Phase 3.5: Multi-GPU Command Scheduling
1. Create `MultiGPUScheduler` interface and implementation
2. Implement multi-GPU command submission
3. Add cross-device synchronization
4. Implement command buffer tracking and debugging

### Phase 3.6: Integration and Testing
1. Integrate all components into existing framework
2. Test multi-GPU workload distribution
3. Measure and optimize performance
4. Implement fallback to single-GPU mode

## Validation and Testing Strategy

### Unit Tests
- Test device group creation and destruction
- Test cross-device memory allocation and copying
- Test workload partitioning algorithms
- Test multi-GPU command submission

### Integration Tests
- Test complete multi-GPU rendering pipeline
- Test dynamic workload balancing
- Test resource sharing and synchronization
- Test fallback to single-GPU mode

### Performance Tests
- Measure frame rate scaling with number of GPUs
- Measure memory bandwidth between GPUs
- Measure command submission overhead
- Test workload distribution efficiency

### Stress Tests
- Test multi-GPU operation under high load
- Test memory usage and leaks with multiple GPUs
- Test device failure handling
- Test continuous operation over extended periods
