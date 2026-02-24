# Phase 4: Runtime Control & Observability

## Purpose and Scope
Implement comprehensive runtime control and observability features for mg-rs, including an advanced CLI interface, live GPU utilization reporting, per-device timelines, memory and queue diagnostics, and integration with debugging and validation tools. This phase focuses on providing developers with the tools needed to monitor, debug, and control the runtime behavior of mg-rs applications.

## Architecture Additions

### 1. CLI Command Extensions
```cpp
// runtime/include/mgrs/cli.h
namespace mgrs {
    enum class CLICommand {
        HELP,
        INFO,
        DEVICES,
        METRICS,
        TIMELINE,
        MEMORY,
        QUEUE,
        PIPELINE,
        DEBUG,
        VALIDATION,
        QUIT
    };

    struct CLIResult {
        bool success;
        std::string output;
        std::vector<std::string> errors;
    };

    class CLI {
    public:
        static Result Create(Context* context, CLI** outCLI);
        static void Destroy(CLI* cli);

        virtual CLIResult ExecuteCommand(CLICommand command, const std::vector<std::string>& args) = 0;
        virtual void SetOutputCallback(std::function<void(const std::string&)> callback) = 0;
        virtual void SetErrorCallback(std::function<void(const std::string&)> callback) = 0;

        virtual ~CLI() = default;
    };
}
```

### 2. Live Metrics Reporting
```cpp
// runtime/include/mgrs/metrics.h
namespace mgrs {
    struct DeviceMetrics {
        uint32_t deviceIndex;
        uint64_t gpuUtilization;
        uint64_t memoryUtilization;
        uint64_t temperature;
        uint64_t powerUsage;
        uint64_t frameTime;
        uint64_t fps;
    };

    struct QueueMetrics {
        uint32_t deviceIndex;
        uint32_t queueFamily;
        uint32_t queueIndex;
        uint64_t submitCount;
        uint64_t commandCount;
        uint64_t idleTime;
        uint64_t busyTime;
    };

    struct MemoryMetrics {
        uint32_t deviceIndex;
        uint64_t total;
        uint64_t used;
        uint64_t free;
        uint64_t allocationCount;
        uint64_t fragmentation;
    };

    class MetricsCollector {
    public:
        static Result Create(Context* context, MetricsCollector** outCollector);
        static void Destroy(MetricsCollector* collector);

        virtual Result CollectDeviceMetrics(std::vector<DeviceMetrics>& outMetrics) = 0;
        virtual Result CollectQueueMetrics(std::vector<QueueMetrics>& outMetrics) = 0;
        virtual Result CollectMemoryMetrics(std::vector<MemoryMetrics>& outMetrics) = 0;
        virtual Result GetFrameTimeRange(uint64_t& outMin, uint64_t& outMax, double& outAvg) = 0;

        virtual ~MetricsCollector() = default;
    };
}
```

### 3. Timeline Visualization
```cpp
// runtime/include/mgrs/timeline.h
namespace mgrs {
    struct TimelineEvent {
        uint32_t deviceIndex;
        uint64_t startTime;
        uint64_t endTime;
        std::string name;
        std::string category;
        uint32_t commandBufferId;
        uint32_t queueIndex;
    };

    class Timeline {
    public:
        static Result Create(Context* context, Timeline** outTimeline);
        static void Destroy(Timeline* timeline);

        virtual void AddEvent(const TimelineEvent& event) = 0;
        virtual Result GetEvents(uint32_t deviceIndex, uint64_t startTime, uint64_t endTime, std::vector<TimelineEvent>& outEvents) = 0;
        virtual Result GetAllEvents(std::vector<TimelineEvent>& outEvents) = 0;
        virtual void ClearEvents() = 0;
        virtual void EnableEventTracking(bool enabled) = 0;

        virtual ~Timeline() = default;
    };
}
```

### 4. Memory Diagnostics
```cpp
// runtime/include/mgrs/memory_diagnostics.h
namespace mgrs {
    struct MemoryAllocation {
        uint32_t deviceIndex;
        uint64_t address;
        size_t size;
        VkMemoryPropertyFlags properties;
        std::string allocationType;
        uint64_t allocationTime;
        uint64_t lastAccessTime;
        uint32_t allocationId;
    };

    class MemoryDiagnostics {
    public:
        static Result Create(Context* context, MemoryDiagnostics** outDiagnostics);
        static void Destroy(MemoryDiagnostics* diagnostics);

        virtual Result GetAllocations(uint32_t deviceIndex, std::vector<MemoryAllocation>& outAllocations) = 0;
        virtual Result GetAllocationStats(uint32_t deviceIndex, uint64_t& outCount, size_t& outTotalSize) = 0;
        virtual Result FindLeaks(std::vector<MemoryAllocation>& outLeaks) = 0;
        virtual Result FindLargeAllocations(size_t minSize, std::vector<MemoryAllocation>& outAllocations) = 0;

        virtual ~MemoryDiagnostics() = default;
    };
}
```

### 5. Queue Diagnostics
```cpp
// runtime/include/mgrs/queue_diagnostics.h
namespace mgrs {
    struct QueueSubmission {
        uint32_t deviceIndex;
        uint32_t queueIndex;
        uint64_t submitTime;
        uint64_t completeTime;
        uint32_t commandBufferCount;
        std::vector<uint32_t> commandBufferIds;
    };

    class QueueDiagnostics {
    public:
        static Result Create(Context* context, QueueDiagnostics** outDiagnostics);
        static void Destroy(QueueDiagnostics* diagnostics);

        virtual Result GetSubmissions(uint32_t deviceIndex, uint32_t queueIndex, std::vector<QueueSubmission>& outSubmissions) = 0;
        virtual Result GetQueueStats(uint32_t deviceIndex, uint32_t queueIndex, uint64_t& outSubmitCount, uint64_t& outTotalTime) = 0;
        virtual Result FindLongRunningSubmissions(uint64_t minDuration, std::vector<QueueSubmission>& outSubmissions) = 0;

        virtual ~QueueDiagnostics() = default;
    };
}
```

### 6. Debug and Validation Integration
```cpp
// runtime/include/mgrs/debug_layer.h
namespace mgrs {
    enum class DebugMessageSeverity {
        VERBOSE,
        INFO,
        WARNING,
        ERROR
    };

    enum class DebugMessageType {
        GENERAL,
        VALIDATION,
        PERFORMANCE
    };

    struct DebugMessage {
        DebugMessageSeverity severity;
        DebugMessageType type;
        std::string message;
        std::string source;
        uint64_t timestamp;
    };

    class DebugLayer {
    public:
        static Result Create(Context* context, DebugLayer** outLayer);
        static void Destroy(DebugLayer* layer);

        virtual void Enable(DebugMessageSeverity minSeverity, DebugMessageType typeMask) = 0;
        virtual void Disable() = 0;
        virtual bool IsEnabled() const = 0;

        virtual void SetMessageCallback(std::function<void(const DebugMessage&)> callback) = 0;
        virtual Result GetMessages(std::vector<DebugMessage>& outMessages) = 0;
        virtual void ClearMessages() = 0;

        virtual ~DebugLayer() = default;
    };
}
```

## Data Flow and Control Flow

### Runtime Control Pipeline
```
┌─────────────────────────────────────────────────────────┐
│ 1. User Input                                            │
│    - Accept CLI commands from user                        │
│    - Parse and validate command arguments                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Command Execution                                     │
│    - Execute command logic                               │
│    - Collect data from runtime                           │
│    - Format output                                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Output Generation                                     │
│    - Print formatted output to console                   │
│    - Display metrics in dashboard                        │
│    - Save data to file if requested                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Post-Execution Analysis                               │
│    - Analyze collected data                               │
│    - Identify performance bottlenecks                      │
│    - Report errors and warnings                           │
└─────────────────────────────────────────────────────────┘
```

### Vulkan-Specific Considerations

#### Debug Marker Integration
- Use `VK_EXT_debug_marker` or `VK_EXT_debug_utils` extensions
- Implement command buffer and queue labeling
- Add memory allocation tags

#### Validation Layers
- Support Vulkan validation layers
- Implement custom validation checks
- Provide detailed error messages and call stacks

## Failure Modes and Safeguards

### CLI Command Errors
- Validate command arguments before execution
- Handle invalid commands and arguments
- Provide helpful error messages and usage information

### Metrics Collection Errors
- Handle failed device queries gracefully
- Continue operation with partial metrics
- Warn about missing metrics data

### Debug Layer Errors
- Handle debug layer initialization failures
- Continue operation without debug information
- Warn about disabled debug functionality

## Incremental Implementation Steps

### Phase 4.1: CLI Command Extensions
1. Create `CLI` interface and implementation
2. Add core CLI commands (help, info, devices)
3. Implement command parsing and validation
4. Add output formatting

### Phase 4.2: Live Metrics Reporting
1. Create `MetricsCollector` interface and implementation
2. Implement device metrics collection
3. Add queue and memory metrics
4. Implement frame time tracking

### Phase 4.3: Timeline Visualization
1. Create `Timeline` interface and implementation
2. Add event tracking for command buffers
3. Implement event querying and filtering
4. Add timeline visualization

### Phase 4.4: Memory Diagnostics
1. Create `MemoryDiagnostics` interface and implementation
2. Implement allocation tracking
3. Add leak detection
4. Implement allocation statistics

### Phase 4.5: Queue Diagnostics
1. Create `QueueDiagnostics` interface and implementation
2. Implement submission tracking
3. Add submission statistics
4. Implement long-running submission detection

### Phase 4.6: Debug and Validation Integration
1. Create `DebugLayer` interface and implementation
2. Integrate with Vulkan validation layers
3. Implement custom validation checks
4. Add debug marker support

## Validation and Testing Strategy

### Unit Tests
- Test CLI command parsing and execution
- Test metrics collection and formatting
- Test timeline event tracking
- Test memory allocation tracking

### Integration Tests
- Test complete runtime control pipeline
- Test metrics collection under load
- Test debug layer integration
- Test CLI commands in multi-GPU scenarios

### Performance Tests
- Measure CLI command response time
- Measure metrics collection overhead
- Test timeline tracking performance
- Test memory diagnostics performance

### Stress Tests
- Test CLI commands under high load
- Test metrics collection with large datasets
- Test timeline tracking for extended periods
- Test memory diagnostics with frequent allocations
