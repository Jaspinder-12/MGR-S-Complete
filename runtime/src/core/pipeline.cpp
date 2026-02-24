#include "mgrs/pipeline.h"
#include "mgrs/vulkan/vulkan_pipeline.h"
#include "mgrs/vulkan/vulkan_context.h"

namespace mgrs {

Result Pipeline::Create(Context* context, const GraphicsPipelineCreateInfo& info, Pipeline** outPipeline) {
    if (!context || !outPipeline) {
        return Result::ErrorInvalidArgument;
    }

    auto vulkanContext = dynamic_cast<vulkan::VulkanContext*>(context);
    if (vulkanContext) {
        return vulkan::VulkanPipeline::Create(vulkanContext, info, reinterpret_cast<vulkan::VulkanPipeline**>(outPipeline));
    }

    return Result::ErrorDeviceNotFound;
}

void Pipeline::Destroy(Pipeline* pipeline) {
    if (!pipeline) {
        return;
    }

    auto vulkanPipeline = dynamic_cast<vulkan::VulkanPipeline*>(pipeline);
    if (vulkanPipeline) {
        vulkan::VulkanPipeline::Destroy(vulkanPipeline);
        return;
    }

    delete pipeline;
}

} // namespace mgrs
