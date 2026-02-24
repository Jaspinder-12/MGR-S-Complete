#pragma once

#include "mgrs/context.h"
#include "mgrs/semaphore.h"
#include <vector>
#include <vulkan/vulkan.h>

namespace mgrs {

struct SwapchainCreateInfo {
    uint32_t width;
    uint32_t height;
    uint32_t minImageCount;
    VkFormat format;
    VkColorSpaceKHR colorSpace;
    VkPresentModeKHR presentMode;
    bool vsync;
};

class Swapchain {
public:
    static Result Create(Context* context, const SwapchainCreateInfo& info, Swapchain** outSwapchain);
    static void Destroy(Swapchain* swapchain);

    virtual uint32_t GetImageCount() const = 0;
    virtual VkImage GetImage(uint32_t index) const = 0;
    virtual VkImageView GetImageView(uint32_t index) const = 0;
    virtual Result AcquireNextImage(TimelineSemaphore* semaphore, uint64_t signalValue, uint32_t* outImageIndex) = 0;
    virtual Result Present(uint32_t imageIndex, TimelineSemaphore* waitSemaphore, uint64_t waitValue) = 0;
    virtual Result Recreate(const SwapchainCreateInfo& info) = 0;
    virtual bool IsOutOfDate() const = 0;

    virtual ~Swapchain() = default;
};

} // namespace mgrs
