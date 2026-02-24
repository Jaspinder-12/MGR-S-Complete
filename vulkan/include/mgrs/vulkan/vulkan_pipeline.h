#ifndef __MGRS_VULKAN_PIPELINE_H
#define __MGRS_VULKAN_PIPELINE_H

#include "mgrs/pipeline.h"
#include "mgrs/vulkan/vulkan_context.h"
#include <vulkan/vulkan.h>

namespace mgrs {
    namespace vulkan {
        class VulkanPipeline : public Pipeline {
        public:
            static Result Create(VulkanContext* context, const GraphicsPipelineCreateInfo& info, VulkanPipeline** outPipeline);
            static void Destroy(VulkanPipeline* pipeline);

            VkPipeline GetVkPipeline() const;

            ~VulkanPipeline() override;

        private:
            VulkanPipeline();
            Result Initialize(VulkanContext* context, const GraphicsPipelineCreateInfo& info);
            Result CreateGraphicsPipeline(const GraphicsPipelineCreateInfo& info);
            void Cleanup();

            VulkanContext* m_context;
            VkPipeline m_pipeline;
        };
    }
}

#endif // __MGRS_VULKAN_PIPELINE_H
