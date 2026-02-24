#ifndef __MGRS_VULKAN_SYNC_H
#define __MGRS_VULKAN_SYNC_H

#include <memory>
#include <vector>
#include <vulkan/vulkan.h>


#ifdef _WIN32
#include <windows.h>
#endif

namespace mgrs {
namespace vulkan {

/**
 * MultiGpuSync manages synchronization primitives shared across different
 * physical devices (Vulkan devices). On Windows, it uses NT handles; on Linux,
 * it uses Opaque FD.
 */
class MultiGpuSync {
public:
  struct SyncInfo {
    VkDevice device;
    VkSemaphore semaphore;
    uint64_t currentValue;
  };

  explicit MultiGpuSync(VkDevice primaryDevice);
  ~MultiGpuSync();

  // Export primary semaphore to a handle that can be imported by other devices
  void *ExportSemaphore();

  // Import the primary semaphore into a peer device
  VkSemaphore ImportToPeer(VkDevice peerDevice, void *handle);

  // Wait for a specific value on a device's semaphore
  void Wait(VkDevice device, uint64_t value);

  // Signal a specific value on a device's semaphore
  void Signal(VkDevice device, uint64_t value);

private:
  VkDevice m_primaryDevice;
  VkSemaphore m_primarySemaphore;
#ifdef _WIN32
  HANDLE m_sharedHandle;
#else
  int m_sharedFd;
#endif
};

} // namespace vulkan
} // namespace mgrs

#endif // __MGRS_VULKAN_SYNC_H
