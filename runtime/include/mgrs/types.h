#pragma once

#include <cstdint>
#include <vulkan/vulkan.h>

namespace mgrs {
// Result type
enum class Result {
  Success,
  ErrorInitialization,
  ErrorDeviceNotFound,
  ErrorInvalidArgument,
  ErrorOutOfMemory,
  ErrorUnknown
};

// Runtime state
enum class RuntimeState { STARTING, RUNNING, DEGRADED, ERROR_STATE };

// Device capabilities
struct DeviceCapabilities {
  uint64_t computeFlops;
  uint64_t rasterPixels;
  uint64_t raytraceTriangles;
  uint64_t vramTotal;
  uint8_t deviceLUID[VK_LUID_SIZE];
  bool hasLUID;
};

// Context creation information
struct ContextCreateInfo {
  uint32_t apiVersion;
};
} // namespace mgrs
