#pragma once

#include "mgrs/context.h"
#include "mgrs/shader.h"
#include "mgrs/pipeline_layout.h"
#include "mgrs/render_pass.h"
#include <vector>
#include <cstdint>

namespace mgrs {

struct VertexInputBinding {
    uint32_t binding;
    uint32_t stride;
    uint32_t inputRate; // 0 for vertex, 1 for instance
};

struct VertexInputAttribute {
    uint32_t location;
    uint32_t binding;
    uint32_t format;
    uint32_t offset;
};

struct InputAssemblyState {
    uint32_t topology; // Triangle list, triangle strip, etc.
    bool primitiveRestartEnable;
};

struct RasterizationState {
    bool depthClampEnable;
    bool rasterizerDiscardEnable;
    uint32_t polygonMode;
    uint32_t cullMode;
    uint32_t frontFace;
    bool depthBiasEnable;
    float depthBiasConstantFactor;
    float depthBiasClamp;
    float depthBiasSlopeFactor;
    float lineWidth;
};

struct DepthStencilState {
    bool depthTestEnable;
    bool depthWriteEnable;
    uint32_t depthCompareOp;
    bool depthBoundsTestEnable;
    bool stencilTestEnable;
    // Stencil op state for front and back faces (simplified)
    uint32_t frontStencilFailOp;
    uint32_t frontStencilDepthFailOp;
    uint32_t frontStencilPassOp;
    uint32_t frontStencilCompareOp;
    uint32_t backStencilFailOp;
    uint32_t backStencilDepthFailOp;
    uint32_t backStencilPassOp;
    uint32_t backStencilCompareOp;
    uint32_t stencilReadMask;
    uint32_t stencilWriteMask;
    int32_t stencilReference;
    float minDepthBounds;
    float maxDepthBounds;
};

struct BlendAttachmentState {
    bool blendEnable;
    uint32_t srcColorBlendFactor;
    uint32_t dstColorBlendFactor;
    uint32_t colorBlendOp;
    uint32_t srcAlphaBlendFactor;
    uint32_t dstAlphaBlendFactor;
    uint32_t alphaBlendOp;
    uint32_t colorWriteMask;
};

struct BlendState {
    bool logicOpEnable;
    uint32_t logicOp;
    std::vector<BlendAttachmentState> attachments;
    float blendConstants[4];
};

struct DynamicState {
    std::vector<uint32_t> dynamicStates;
};

struct GraphicsPipelineCreateInfo {
    RenderPass* renderPass;
    uint32_t subpass;
    std::vector<Shader*> shaders;
    std::vector<VertexInputBinding> vertexInputBindings;
    std::vector<VertexInputAttribute> vertexInputAttributes;
    InputAssemblyState inputAssemblyState;
    RasterizationState rasterizationState;
    DepthStencilState depthStencilState;
    BlendState blendState;
    DynamicState dynamicState;
    PipelineLayout* pipelineLayout;
};

class Pipeline {
public:
    static Result Create(Context* context, const GraphicsPipelineCreateInfo& info, Pipeline** outPipeline);
    static void Destroy(Pipeline* pipeline);

    virtual ~Pipeline() = default;
};

} // namespace mgrs
