#include "mgrs/render_pass.h"
#include "mgrs/vulkan/vulkan_render_pass.h"
#include "mgrs/vulkan/vulkan_context.h"

namespace mgrs {

Result RenderPass::Create(Context* context, const RenderPassCreateInfo& info, RenderPass** outRenderPass) {
    if (!context || !outRenderPass) {
        return Result::ErrorInvalidArgument;
    }

    // Check if context is a VulkanContext
    auto vulkanContext = dynamic_cast<vulkan::VulkanContext*>(context);
    if (vulkanContext) {
        return vulkan::VulkanRenderPass::Create(vulkanContext, info, reinterpret_cast<vulkan::VulkanRenderPass**>(outRenderPass));
    }

    // Add support for other backends here (e.g., DirectX 12, Metal, etc.)
    return Result::ErrorDeviceNotFound;
}

void RenderPass::Destroy(RenderPass* renderPass) {
    if (!renderPass) {
        return;
    }

    // Check if renderPass is a VulkanRenderPass
    auto vulkanRenderPass = dynamic_cast<vulkan::VulkanRenderPass*>(renderPass);
    if (vulkanRenderPass) {
        vulkan::VulkanRenderPass::Destroy(vulkanRenderPass);
        return;
    }

    // Add support for other backends here
    delete renderPass;
}

} // namespace mgrs
