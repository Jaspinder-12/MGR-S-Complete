#ifndef __MGRS_VULKAN_CONTEXT_H
#define __MGRS_VULKAN_CONTEXT_H

#include "mgrs/context.h"
#include <string>
#include <vector>
#include <vulkan/vulkan.h>

namespace mgrs {
namespace vulkan {
class VulkanContext : public Context {
public:
  // Create a new Vulkan context
  static Result Create(const ContextCreateInfo &info,
                       VulkanContext **outContext);

  // Get the number of available devices
  uint32_t GetDeviceCount() const override;

  // Get device capabilities
  const DeviceCapabilities &
  GetDeviceCapabilities(uint32_t deviceIndex) const override;

  // Get current runtime state
  RuntimeState GetState() const override;

  // Get API version
  uint32_t GetApiVersion() const override;

  // Get GPU count
  uint32_t GetGpuCount() const override;

  // Get authority GPU index
  uint32_t GetAuthorityGpuIndex() const override;

  // Get device name
  std::string GetDeviceName(uint32_t deviceIndex) const override;

  // Get driver version
  std::string GetDriverVersion(uint32_t deviceIndex) const override;

  ~VulkanContext() override;

private:
  VulkanContext(); // Private constructor to enforce Create method

  uint32_t m_apiVersion;
  VkInstance m_instance;
  std::vector<VkPhysicalDevice> m_physicalDevices;
  std::vector<DeviceCapabilities> m_caps;
  std::vector<std::string> m_deviceNames;
  std::vector<std::string> m_driverVersions;
  uint32_t m_authorityIndex;
  RuntimeState m_state;
};
} // namespace vulkan
} // namespace mgrs

#endif // __MGRS_VULKAN_CONTEXT_H
