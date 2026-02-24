#ifndef __MGRS_VULKAN_DEVICE_H
#define __MGRS_VULKAN_DEVICE_H

#include "mgrs/context.h"

namespace mgrs {
namespace vulkan {
class VulkanDevice {
public:
  // Create a new Vulkan device
  static Result Create(VkPhysicalDevice physicalDevice, uint32_t deviceIndex,
                       VulkanDevice **outDevice);

  // Initialize the device
  Result Initialize();

  // Get device capabilities
  const DeviceCapabilities &GetCapabilities() const;

  // Get device index
  uint32_t GetDeviceIndex() const;

  ~VulkanDevice();

private:
  VulkanDevice() = default;
  VkPhysicalDevice m_physicalDevice = VK_NULL_HANDLE;
  uint32_t m_deviceIndex = 0;
  DeviceCapabilities m_caps = {};
};
} // namespace vulkan
} // namespace mgrs

#endif // __MGRS_VULKAN_DEVICE_H
