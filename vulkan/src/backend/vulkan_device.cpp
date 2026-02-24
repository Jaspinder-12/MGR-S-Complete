#include "mgrs/vulkan/vulkan_device.h"
#include "mgrs/vulkan/vulkan_context.h"

namespace mgrs {
namespace vulkan {
Result VulkanDevice::Create(VkPhysicalDevice physicalDevice,
                            uint32_t deviceIndex, VulkanDevice **outDevice) {
  auto device = new VulkanDevice();
  if (!device) {
    return Result::ErrorOutOfMemory;
  }

  device->m_physicalDevice = physicalDevice;
  device->m_deviceIndex = deviceIndex;

  // Query capacities
  VkPhysicalDeviceProperties props;
  vkGetPhysicalDeviceProperties(physicalDevice, &props);

  VkPhysicalDeviceMemoryProperties memProps;
  vkGetPhysicalDeviceMemoryProperties(physicalDevice, &memProps);

  uint64_t totalVram = 0;
  for (uint32_t j = 0; j < memProps.memoryHeapCount; j++) {
    if (memProps.memoryHeaps[j].flags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT) {
      totalVram += memProps.memoryHeaps[j].size;
    }
  }

  device->m_caps.vramTotal = totalVram;
  device->m_caps.computeFlops =
      (uint64_t)props.limits.maxComputeWorkGroupCount[0] * 1000000;
  device->m_caps.rasterPixels = 1000000000;
  device->m_caps.raytraceTriangles = 100000000;

  *outDevice = device;
  return Result::Success;
}

Result VulkanDevice::Initialize() { return Result::Success; }

const DeviceCapabilities &VulkanDevice::GetCapabilities() const {
  return m_caps;
}

uint32_t VulkanDevice::GetDeviceIndex() const { return m_deviceIndex; }

VulkanDevice::~VulkanDevice() {
  // Cleanup Vulkan device resources
}
} // namespace vulkan
} // namespace mgrs
