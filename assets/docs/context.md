# Context Management

The `Context` class is the main entry point for the mg-rs library. It manages the overall state of the system, including:

- Initialization and shutdown
- Device enumeration and selection
- Resource management
- Command scheduling
- Memory management

## Context Creation

To create a context, use the static `Create` method:

```cpp
#include <mgrs/context.h>

mg-rs::ContextCreateInfo info;
info.apiVersion = VK_API_VERSION_1_3;

mg-rs::Context* context;
mg-rs::Result result = mg-rs::Context::Create(info, &context);

if (result != mg-rs::Result::Success) {
    // Handle error
}
```

## Context Configuration

The `ContextCreateInfo` structure allows you to configure:

- API version compatibility
- Device selection criteria
- Memory allocation strategy
- Debugging options

## Device Management

Once a context is created, you can enumerate available devices:

```cpp
uint32_t deviceCount = context->GetDeviceCount();
for (uint32_t i = 0; i < deviceCount; i++) {
    const mg-rs::DeviceCapabilities& caps = context->GetDeviceCapabilities(i);
    std::cout << "Device " << i << ":\n";
    std::cout << "  Name: " << context->GetDeviceName(i) << "\n";
    std::cout << "  Compute: " << caps.computeFlops << " FLOPS\n";
    std::cout << "  VRAM: " << caps.vramTotal / 1024 / 1024 / 1024 << " GB\n";
}

// Select a specific device
uint32_t selectedDevice = context->SelectDevice(mg-rs::DeviceType::GPU);
```

## Context State Management

The context tracks its current state:

```cpp
mg-rs::RuntimeState state = context->GetState();

switch (state) {
    case mg-rs::RuntimeState::STARTING:
        std::cout << "Context is initializing...\n";
        break;
    case mg-rs::RuntimeState::RUNNING:
        std::cout << "Context is running...\n";
        break;
    case mg-rs::RuntimeState::DEGRADED:
        std::cout << "Context is in degraded mode...\n";
        break;
    case mg-rs::RuntimeState::ERROR:
        std::cout << "Context is in error state: " << context->GetLastError() << "\n";
        break;
}
```

## Shutdown

Always properly shut down the context to release resources:

```cpp
context->Shutdown();
delete context;
```

## Thread Safety

The context is not thread-safe by default. For multi-threaded applications, use:

```cpp
mg-rs::ContextCreateInfo info;
info.threadSafe = true;
```

Note that this may incur a performance overhead.
