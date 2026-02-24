#include "mgrs/pipeline_layout.h"
#include "mgrs/vulkan/vulkan_pipeline_layout.h"
#include "mgrs/vulkan/vulkan_context.h"

namespace mgrs {

Result PipelineLayout::Create(Context* context, const PipelineLayoutCreateInfo& info, PipelineLayout** outLayout) {
    if (!context || !outLayout) {
        return Result::ErrorInvalidArgument;
    }

    auto vulkanContext = dynamic_cast<vulkan::VulkanContext*>(context);
    if (vulkanContext) {
        return vulkan::VulkanPipelineLayout::Create(vulkanContext, info, reinterpret_cast<vulkan::VulkanPipelineLayout**>(outLayout));
    }

    return Result::ErrorDeviceNotFound;
}

void PipelineLayout::Destroy(PipelineLayout* layout) {
    if (!layout) {
        return;
    }

    auto vulkanLayout = dynamic_cast<vulkan::VulkanPipelineLayout*>(layout);
    if (vulkanLayout) {
        vulkan::VulkanPipelineLayout::Destroy(vulkanLayout);
        return;
    }

    delete layout;
}

} // namespace mgrs
