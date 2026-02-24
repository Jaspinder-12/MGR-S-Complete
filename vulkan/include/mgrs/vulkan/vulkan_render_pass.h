#ifndef __MGRS_VULKAN_RENDER_PASS_H
#define __MGRS_VULKAN_RENDER_PASS_H

#include "mgrs/render_pass.h"
#include "mgrs/vulkan/vulkan_context.h"
#include <vector>
#include <vulkan/vulkan.h>

namespace mgrs {
    namespace vulkan {
        class VulkanRenderPass : public RenderPass {
        public:
            static Result Create(VulkanContext* context, const RenderPassCreateInfo& info, VulkanRenderPass** outRenderPass);
            static void Destroy(VulkanRenderPass* renderPass);

            VkRenderPass GetVkRenderPass() const override;
            uint32_t GetAttachmentCount() const override;
            const AttachmentDescription& GetAttachmentDescription(uint32_t index) const override;

            ~VulkanRenderPass() override;

        private:
            VulkanRenderPass(); // Private constructor to enforce Create method
            Result Initialize(VulkanContext* context, const RenderPassCreateInfo& info);
            Result CreateRenderPass(const RenderPassCreateInfo& info);
            void Cleanup();

            VulkanContext* m_context;
            VkRenderPass m_renderPass;
            std::vector<AttachmentDescription> m_attachments;
        };
    }
}

#endif // __MGRS_VULKAN_RENDER_PASS_H
