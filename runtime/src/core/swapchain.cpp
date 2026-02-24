#include "mgrs/swapchain.h"
#include "mgrs/vulkan/vulkan_swapchain.h"
#include "mgrs/vulkan/vulkan_context.h"

namespace mgrs {

Result Swapchain::Create(Context* context, const SwapchainCreateInfo& info, Swapchain** outSwapchain) {
    if (!context || !outSwapchain) {
        return Result::ErrorInvalidArgument;
    }

    // Check if context is a VulkanContext
    auto vulkanContext = dynamic_cast<vulkan::VulkanContext*>(context);
    if (vulkanContext) {
        return vulkan::VulkanSwapchain::Create(vulkanContext, info, reinterpret_cast<vulkan::VulkanSwapchain**>(outSwapchain));
    }

    // Add support for other backends here (e.g., DirectX 12, Metal, etc.)
    return Result::ErrorDeviceNotFound;
}

void Swapchain::Destroy(Swapchain* swapchain) {
    if (!swapchain) {
        return;
    }

    // Check if swapchain is a VulkanSwapchain
    auto vulkanSwapchain = dynamic_cast<vulkan::VulkanSwapchain*>(swapchain);
    if (vulkanSwapchain) {
        vulkan::VulkanSwapchain::Destroy(vulkanSwapchain);
        return;
    }

    // Add support for other backends here
    delete swapchain;
}

} // namespace mgrs
