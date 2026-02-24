#pragma once

#include "mgrs/context.h"
#include <vector>
#include <cstdint>

namespace mgrs {

struct DescriptorSetLayoutBinding {
    uint32_t binding;
    uint32_t descriptorCount;
    uint32_t descriptorType; // Use abstract types, not Vulkan specific
    uint32_t stageFlags; // Shader stages that can access this binding
};

struct PipelineLayoutCreateInfo {
    std::vector<DescriptorSetLayoutBinding> descriptorSetLayouts;
    std::vector<uint32_t> pushConstantRanges;
};

class PipelineLayout {
public:
    static Result Create(Context* context, const PipelineLayoutCreateInfo& info, PipelineLayout** outLayout);
    static void Destroy(PipelineLayout* layout);

    virtual ~PipelineLayout() = default;
};

} // namespace mgrs
