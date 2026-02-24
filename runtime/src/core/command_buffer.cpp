/*
 * Project: MGR-S (Multi-GPU Runtime System)
 * Author: Jaspinder
 * Description: Part of the MGR-S project
 * License: See LICENSE file
 */

#include "mgrs/command_buffer.h"
#include "mgrs/vulkan/vulkan_command_buffer.h"
#include "mgrs/vulkan/vulkan_context.h"

namespace mgrs {

Result CommandBuffer::Create(Context* context, CommandBuffer** outCommandBuffer) {
    if (!context || !outCommandBuffer) {
        return Result::ErrorInvalidArgument;
    }

    auto vulkanContext = dynamic_cast<vulkan::VulkanContext*>(context);
    if (vulkanContext) {
        return vulkan::VulkanCommandBuffer::Create(vulkanContext, reinterpret_cast<vulkan::VulkanCommandBuffer**>(outCommandBuffer));
    }

    return Result::ErrorDeviceNotFound;
}

void CommandBuffer::Destroy(CommandBuffer* commandBuffer) {
    if (!commandBuffer) {
        return;
    }

    auto vulkanCommandBuffer = dynamic_cast<vulkan::VulkanCommandBuffer*>(commandBuffer);
    if (vulkanCommandBuffer) {
        vulkan::VulkanCommandBuffer::Destroy(vulkanCommandBuffer);
        return;
    }

    delete commandBuffer;
}

} // namespace mgrs
