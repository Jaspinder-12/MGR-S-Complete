#pragma once

#include "mgrs/context.h"
#include "mgrs/swapchain.h"
#include <vector>
#include <vulkan/vulkan.h>

namespace mgrs {

struct AttachmentDescription {
    VkFormat format;
    VkSampleCountFlagBits samples;
    VkAttachmentLoadOp loadOp;
    VkAttachmentStoreOp storeOp;
    VkAttachmentLoadOp stencilLoadOp;
    VkAttachmentStoreOp stencilStoreOp;
    VkImageLayout initialLayout;
    VkImageLayout finalLayout;
};

struct SubpassDescription {
    std::vector<uint32_t> inputAttachments;
    std::vector<uint32_t> colorAttachments;
    std::vector<uint32_t> resolveAttachments;
    uint32_t depthStencilAttachment;
    std::vector<uint32_t> preserveAttachments;
};

struct RenderPassCreateInfo {
    std::vector<AttachmentDescription> attachments;
    std::vector<SubpassDescription> subpasses;
    std::vector<VkSubpassDependency> dependencies;
};

class RenderPass {
public:
    static Result Create(Context* context, const RenderPassCreateInfo& info, RenderPass** outRenderPass);
    static void Destroy(RenderPass* renderPass);

    virtual VkRenderPass GetVkRenderPass() const = 0;
    virtual uint32_t GetAttachmentCount() const = 0;
    virtual const AttachmentDescription& GetAttachmentDescription(uint32_t index) const = 0;

    virtual ~RenderPass() = default;
};

} // namespace mgrs
