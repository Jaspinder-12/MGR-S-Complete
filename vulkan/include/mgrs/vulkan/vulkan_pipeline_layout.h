#ifndef __MGRS_VULKAN_PIPELINE_LAYOUT_H
#define __MGRS_VULKAN_PIPELINE_LAYOUT_H

#include "mgrs/pipeline_layout.h"
#include "mgrs/vulkan/vulkan_context.h"
#include <vulkan/vulkan.h>

namespace mgrs {
    namespace vulkan {
        class VulkanPipelineLayout : public PipelineLayout {
        public:
            static Result Create(VulkanContext* context, const PipelineLayoutCreateInfo& info, VulkanPipelineLayout** outLayout);
            static void Destroy(VulkanPipelineLayout* layout);

            VkPipelineLayout GetVkPipelineLayout() const;

            ~VulkanPipelineLayout() override;

        private:
            VulkanPipelineLayout();
            Result Initialize(VulkanContext* context, const PipelineLayoutCreateInfo& info);
            Result CreatePipelineLayout(const PipelineLayoutCreateInfo& info);
            void Cleanup();

            VulkanContext* m_context;
            VkPipelineLayout m_pipelineLayout;
        };
    }
}

#endif // __MGRS_VULKAN_PIPELINE_LAYOUT_H
