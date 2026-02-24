/*
 * Project: MGR-S (Multi-GPU Runtime System)
 * Author: Jaspinder
 * Description: Part of the MGR-S project
 * License: See LICENSE file
 */

#pragma once

#include "mgrs/pipeline.h"

namespace mgrs {

class CommandBuffer {
public:
    static Result Create(Context* context, CommandBuffer** outCommandBuffer);
    static void Destroy(CommandBuffer* commandBuffer);

    virtual Result Begin() = 0;
    virtual Result End() = 0;
    virtual Result Submit() = 0;

    virtual Result BindPipeline(Pipeline* pipeline) = 0;
    virtual Result BindDescriptorSets(uint32_t firstSet, const void* descriptorSets, uint32_t descriptorSetCount, const uint32_t* dynamicOffsets, uint32_t dynamicOffsetCount) = 0;
    virtual Result BindVertexBuffers(uint32_t firstBinding, const void* buffers, uint32_t bufferCount, const uint64_t* offsets) = 0;
    virtual Result BindIndexBuffer(const void* buffer, uint64_t offset, uint32_t indexType) = 0;

    virtual ~CommandBuffer() = default;
};

} // namespace mgrs
