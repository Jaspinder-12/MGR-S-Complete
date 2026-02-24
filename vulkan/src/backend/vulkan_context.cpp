#include "mgrs/vulkan/vulkan_context.h"
#include <algorithm> // for std::max if needed, though I used totalVram > maxVram manually

namespace mgrs {
namespace vulkan {
VulkanContext::VulkanContext()
    : m_apiVersion(0), m_instance(VK_NULL_HANDLE), m_authorityIndex(0),
      m_state(RuntimeState::STARTING) {}

Result VulkanContext::Create(const ContextCreateInfo &info,
                             VulkanContext **outContext) {
  auto context = new VulkanContext();
  if (!context) {
    return Result::ErrorOutOfMemory;
  }
  context->m_apiVersion = info.apiVersion;

  // 1. Create Vulkan Instance
  VkApplicationInfo appInfo = {};
  appInfo.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  appInfo.pApplicationName = "MGR-S Runtime";
  appInfo.applicationVersion = VK_MAKE_VERSION(0, 2, 0);
  appInfo.pEngineName = "MGR-S Engine";
  appInfo.engineVersion = VK_MAKE_VERSION(0, 2, 0);
  appInfo.apiVersion = info.apiVersion;

  VkInstanceCreateInfo createInfo = {};
  createInfo.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  createInfo.pApplicationInfo = &appInfo;

  if (vkCreateInstance(&createInfo, nullptr, &context->m_instance) !=
      VK_SUCCESS) {
    delete context;
    return Result::ErrorInitialization;
  }

  // 2. Enumerate Physical Devices
  uint32_t deviceCount = 0;
  vkEnumeratePhysicalDevices(context->m_instance, &deviceCount, nullptr);
  if (deviceCount == 0) {
    vkDestroyInstance(context->m_instance, nullptr);
    delete context;
    return Result::ErrorDeviceNotFound;
  }

  context->m_physicalDevices.resize(deviceCount);
  vkEnumeratePhysicalDevices(context->m_instance, &deviceCount,
                             context->m_physicalDevices.data());

  // 3. Query Device Properties & Caps
  uint64_t maxVram = 0;
  for (uint32_t i = 0; i < deviceCount; i++) {
    VkPhysicalDeviceProperties props;
    vkGetPhysicalDeviceProperties(context->m_physicalDevices[i], &props);
    context->m_deviceNames.push_back(props.deviceName);

    // Query Driver Version (KHR) and LUID
    std::string driverVersion = "Unknown Driver";
    uint8_t luid[VK_LUID_SIZE] = {0};
    bool hasLUID = false;

    if (info.apiVersion >= VK_API_VERSION_1_1) {
      VkPhysicalDeviceDriverProperties driverProps = {};
      driverProps.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DRIVER_PROPERTIES;

      VkPhysicalDeviceIDProperties idProps = {};
      idProps.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ID_PROPERTIES;
      idProps.pNext = &driverProps;

      VkPhysicalDeviceProperties2 props2 = {};
      props2.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2;
      props2.pNext = &idProps;

      vkGetPhysicalDeviceProperties2(context->m_physicalDevices[i], &props2);

      if (driverProps.driverName[0] != '\0') {
        driverVersion =
            std::string(driverProps.driverName) + " " + driverProps.driverInfo;
      }

      if (idProps.deviceLUIDValid) {
        memcpy(luid, idProps.deviceLUID, VK_LUID_SIZE);
        hasLUID = true;
      }
    }
    context->m_driverVersions.push_back(driverVersion);

    VkPhysicalDeviceMemoryProperties memProps;
    vkGetPhysicalDeviceMemoryProperties(context->m_physicalDevices[i],
                                        &memProps);

    uint64_t totalVram = 0;
    for (uint32_t j = 0; j < memProps.memoryHeapCount; j++) {
      if (memProps.memoryHeaps[j].flags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT) {
        totalVram += memProps.memoryHeaps[j].size;
      }
    }

    DeviceCapabilities caps = {};
    caps.vramTotal = totalVram;
    memcpy(caps.deviceLUID, luid, VK_LUID_SIZE);
    caps.hasLUID = hasLUID;
    // Estimate compute from maxComputeWorkGroupCount
    caps.computeFlops =
        (uint64_t)props.limits.maxComputeWorkGroupCount[0] * 1000000;
    caps.rasterPixels = 1000000000;     // Placeholder
    caps.raytraceTriangles = 100000000; // Placeholder

    context->m_caps.push_back(caps);

    if (totalVram > maxVram) {
      maxVram = totalVram;
      context->m_authorityIndex = i;
    }
  }

  context->m_state = RuntimeState::RUNNING;
  *outContext = context;
  return Result::Success;
}

uint32_t VulkanContext::GetDeviceCount() const {
  return static_cast<uint32_t>(m_physicalDevices.size());
}

const DeviceCapabilities &
VulkanContext::GetDeviceCapabilities(uint32_t deviceIndex) const {
  if (deviceIndex >= m_caps.size()) {
    static DeviceCapabilities empty = {};
    return empty;
  }
  return m_caps[deviceIndex];
}

RuntimeState VulkanContext::GetState() const { return m_state; }

uint32_t VulkanContext::GetApiVersion() const { return m_apiVersion; }

uint32_t VulkanContext::GetGpuCount() const { return GetDeviceCount(); }

uint32_t VulkanContext::GetAuthorityGpuIndex() const {
  return m_authorityIndex;
}

std::string VulkanContext::GetDeviceName(uint32_t deviceIndex) const {
  if (deviceIndex >= m_deviceNames.size())
    return "Unknown Device";
  return m_deviceNames[deviceIndex];
}

std::string VulkanContext::GetDriverVersion(uint32_t deviceIndex) const {
  if (deviceIndex >= m_driverVersions.size())
    return "Unknown Driver";
  return m_driverVersions[deviceIndex];
}

VulkanContext::~VulkanContext() {
  if (m_instance != VK_NULL_HANDLE) {
    vkDestroyInstance(m_instance, nullptr);
  }
}
} // namespace vulkan
} // namespace mgrs
