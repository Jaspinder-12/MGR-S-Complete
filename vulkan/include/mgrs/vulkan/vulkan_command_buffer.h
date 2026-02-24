#ifndef __MGRS_VULKAN_COMMAND_BUFFER_H
#define __MGRS_VULKAN_COMMAND_BUFFER_H

#include "mgrs/command_buffer.h"
#include "mgrs/vulkan/vulkan_context.h"
#include <vulkan/vulkan.h>

namespace mgrs {
    namespace vulkan {
        class VulkanCommandBuffer : public CommandBuffer {
        public:
            static Result Create(VulkanContext* context, VulkanCommandBuffer** outCommandBuffer);
            static void Destroy(VulkanCommandBuffer* commandBuffer);

            Result Begin() override;
            Result End() override;
            Result Submit() override;

            Result BindPipeline(Pipeline* pipeline) override;
            Result BindDescriptorSets(uint32_t firstSet, const void* descriptorSets, uint32_t descriptorSetCount, const uint32_t* dynamicOffsets, uint32_t dynamicOffsetCount) override;
            Result BindVertexBuffers(uint32_t firstBinding, const void* buffers, uint32_t bufferCount, const uint64_t* offsets) override;
            Result BindIndexBuffer(const void* buffer, uint64_t offset, uint32_t indexType) override;

            VkCommandBuffer GetVkCommandBuffer() const;

            ~VulkanCommandBuffer() override;

        private:
            VulkanCommandBuffer();
            Result Initialize(VulkanContext* context);
            void Cleanup();

            VulkanContext* m_context;
            VkCommandBuffer m_commandBuffer;
        };
    }
}

#endif // __MGRS_VULKAN_COMMAND_BUFFER_H
