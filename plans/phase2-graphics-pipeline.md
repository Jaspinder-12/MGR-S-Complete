# Phase 2: Graphics Pipeline Enablement

## Purpose and Scope
Enable basic graphics pipeline functionality for mg-rs, including swapchain management, render passes, pipeline state objects, and shader management. This phase focuses on creating a minimal, functional graphics pipeline that supports 2D/3D rendering with Vulkan backend.

## Architecture Additions

### 1. Swapchain Abstraction
```cpp
// runtime/include/mgrs/swapchain.h
namespace mgrs {
    struct SwapchainCreateInfo {
        uint32_t width;
        uint32_t height;
        uint32_t minImageCount;
        VkFormat format;
        VkColorSpaceKHR colorSpace;
        VkPresentModeKHR presentMode;
        bool vsync;
    };

    class Swapchain {
    public:
        static Result Create(Context* context, const SwapchainCreateInfo& info, Swapchain** outSwapchain);
        static void Destroy(Swapchain* swapchain);

        virtual uint32_t GetImageCount() const = 0;
        virtual VkImage GetImage(uint32_t index) const = 0;
        virtual VkImageView GetImageView(uint32_t index) const = 0;
        virtual Result AcquireNextImage(TimelineSemaphore* semaphore, uint64_t signalValue, uint32_t* outImageIndex) = 0;
        virtual Result Present(uint32_t imageIndex, TimelineSemaphore* waitSemaphore, uint64_t waitValue) = 0;
        virtual Result Recreate(const SwapchainCreateInfo& info) = 0;
        virtual bool IsOutOfDate() const = 0;

        virtual ~Swapchain() = default;
    };
}
```

### 2. Render Pass System
```cpp
// runtime/include/mgrs/render_pass.h
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
}
```

### 3. Framebuffer Management
```cpp
// runtime/include/mgrs/framebuffer.h
namespace mgrs {
    struct FramebufferCreateInfo {
        RenderPass* renderPass;
        std::vector<VkImageView> attachments;
        uint32_t width;
        uint32_t height;
        uint32_t layers;
    };

    class Framebuffer {
    public:
        static Result Create(Context* context, const FramebufferCreateInfo& info, Framebuffer** outFramebuffer);
        static void Destroy(Framebuffer* framebuffer);

        virtual VkFramebuffer GetVkFramebuffer() const = 0;
        virtual RenderPass* GetRenderPass() const = 0;

        virtual ~Framebuffer() = default;
    };
}
```

### 4. Pipeline State Objects
```cpp
// runtime/include/mgrs/pipeline.h
namespace mgrs {
    struct PipelineShaderStage {
        VkShaderStageFlagBits stage;
        VkShaderModule shaderModule;
        const char* entryPoint;
    };

    struct PipelineVertexInputState {
        std::vector<VkVertexInputBindingDescription> bindings;
        std::vector<VkVertexInputAttributeDescription> attributes;
    };

    struct PipelineInputAssemblyState {
        VkPrimitiveTopology topology;
        bool primitiveRestartEnable;
    };

    struct PipelineViewportState {
        std::vector<VkViewport> viewports;
        std::vector<VkRect2D> scissors;
    };

    struct PipelineRasterizationState {
        bool depthClampEnable;
        bool rasterizerDiscardEnable;
        VkPolygonMode polygonMode;
        VkCullModeFlags cullMode;
        VkFrontFace frontFace;
        bool depthBiasEnable;
        float depthBiasConstantFactor;
        float depthBiasClamp;
        float depthBiasSlopeFactor;
        float lineWidth;
    };

    struct PipelineMultisampleState {
        VkSampleCountFlagBits rasterizationSamples;
        bool sampleShadingEnable;
        float minSampleShading;
        const VkSampleMask* sampleMask;
        bool alphaToCoverageEnable;
        bool alphaToOneEnable;
    };

    struct PipelineDepthStencilState {
        bool depthTestEnable;
        bool depthWriteEnable;
        VkCompareOp depthCompareOp;
        bool depthBoundsTestEnable;
        bool stencilTestEnable;
        VkStencilOpState front;
        VkStencilOpState back;
        float minDepthBounds;
        float maxDepthBounds;
    };

    struct PipelineColorBlendAttachmentState {
        bool blendEnable;
        VkBlendFactor srcColorBlendFactor;
        VkBlendFactor dstColorBlendFactor;
        VkBlendOp colorBlendOp;
        VkBlendFactor srcAlphaBlendFactor;
        VkBlendFactor dstAlphaBlendFactor;
        VkBlendOp alphaBlendOp;
        VkColorComponentFlags colorWriteMask;
    };

    struct PipelineColorBlendState {
        bool logicOpEnable;
        VkLogicOp logicOp;
        std::vector<PipelineColorBlendAttachmentState> attachments;
        float blendConstants[4];
    };

    struct PipelineDynamicState {
        std::vector<VkDynamicState> dynamicStates;
    };

    struct GraphicsPipelineCreateInfo {
        RenderPass* renderPass;
        uint32_t subpass;
        std::vector<PipelineShaderStage> shaderStages;
        PipelineVertexInputState vertexInputState;
        PipelineInputAssemblyState inputAssemblyState;
        PipelineViewportState viewportState;
        PipelineRasterizationState rasterizationState;
        PipelineMultisampleState multisampleState;
        PipelineDepthStencilState depthStencilState;
        PipelineColorBlendState colorBlendState;
        PipelineDynamicState dynamicState;
        VkPipelineLayout pipelineLayout;
    };

    class GraphicsPipeline {
    public:
        static Result Create(Context* context, const GraphicsPipelineCreateInfo& info, GraphicsPipeline** outPipeline);
        static void Destroy(GraphicsPipeline* pipeline);

        virtual VkPipeline GetVkPipeline() const = 0;
        virtual VkPipelineLayout GetVkPipelineLayout() const = 0;

        virtual ~GraphicsPipeline() = default;
    };
}
```

### 5. Shader Management
```cpp
// runtime/include/mgrs/shader.h
namespace mgrs {
    struct ShaderCreateInfo {
        VkShaderStageFlagBits stage;
        const void* code;
        size_t codeSize;
        const char* entryPoint;
    };

    class Shader {
    public:
        static Result Create(Context* context, const ShaderCreateInfo& info, Shader** outShader);
        static void Destroy(Shader* shader);

        virtual VkShaderModule GetVkShaderModule() const = 0;
        virtual VkShaderStageFlagBits GetStage() const = 0;
        virtual const char* GetEntryPoint() const = 0;

        virtual ~Shader() = default;
    };
}
```

### 6. Command Buffer Extensions
```cpp
// runtime/include/mgrs/command_buffer.h
namespace mgrs {
    class CommandBuffer {
    public:
        // Existing methods...

        virtual Result BeginRenderPass(const VkRenderPassBeginInfo& info, VkSubpassContents contents) = 0;
        virtual Result EndRenderPass() = 0;
        virtual Result BindPipeline(VkPipelineBindPoint bindPoint, GraphicsPipeline* pipeline) = 0;
        virtual Result BindVertexBuffers(uint32_t firstBinding, const std::vector<VkBuffer>& buffers, const std::vector<VkDeviceSize>& offsets) = 0;
        virtual Result BindIndexBuffer(VkBuffer buffer, VkDeviceSize offset, VkIndexType indexType) = 0;
        virtual Result Draw(uint32_t vertexCount, uint32_t instanceCount, uint32_t firstVertex, uint32_t firstInstance) = 0;
        virtual Result DrawIndexed(uint32_t indexCount, uint32_t instanceCount, uint32_t firstIndex, int32_t vertexOffset, uint32_t firstInstance) = 0;

        virtual ~CommandBuffer() = default;
    };
}
```

## Data Flow and Control Flow

### Frame Execution Pipeline
```
┌─────────────────────────────────────────────────────────┐
│ 1. Begin Frame                                           │
│    - Acquire swapchain image                             │
│    - Create command buffer                                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Record Commands                                       │
│    - Begin render pass                                   │
│    - Bind pipeline                                       │
│    - Bind vertex/index buffers                           │
│    - Draw calls                                          │
│    - End render pass                                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Submit and Present                                    │
│    - Submit command buffer to queue                      │
│    - Wait for semaphore                                  │
│    - Present swapchain image                             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. End Frame                                             │
│    - Clean up resources                                  │
└─────────────────────────────────────────────────────────┘
```

### Vulkan-Specific Considerations

#### Swapchain Implementation
- Must support multiple present modes (FIFO, Mailbox, Immediate)
- Must handle out-of-date swapchain conditions
- Must support vsync and tearing options
- Must implement swapchain recreation on resize

#### Render Pass Optimization
- Use subpasses for better pipeline efficiency
- Implement render pass culling
- Support multisampling and resolve attachments
- Handle depth/stencil attachments

#### Pipeline Cache
- Implement pipeline cache for faster pipeline creation
- Support pipeline derivative chains
- Handle pipeline layout changes

## Multi-GPU Implications

### Swapchain Limitations
- Only available on devices with graphics queue family
- May require dedicated presentation queue
- Cross-device swapchain operations not supported

### Render Pass Distribution
- Render passes must be created per device
- Framebuffers must be created per device and swapchain image
- Pipeline state objects may be shared between compatible devices

## Failure Modes and Safeguards

### Swapchain Failures
- Handle `VK_ERROR_OUT_OF_DATE_KHR` by recreating swapchain
- Handle `VK_SUBOPTIMAL_KHR` by warning and continuing
- Fall back to software rendering if swapchain creation fails

### Pipeline Creation Failures
- Validate shader modules before pipeline creation
- Check pipeline compatibility with render pass
- Fall back to default pipeline if creation fails

### Command Buffer Recording Failures
- Validate pipeline state before binding
- Check render pass state before draw calls
- Recover from command buffer errors by resetting pool

## Incremental Implementation Steps

### Phase 2.1: Swapchain Abstraction
1. Create `Swapchain` interface and Vulkan implementation
2. Add swapchain creation and destruction methods
3. Implement acquire and present operations
4. Handle swapchain resize and recreation

### Phase 2.2: Render Pass System
1. Create `RenderPass` interface and Vulkan implementation
2. Add attachment, subpass, and dependency descriptions
3. Implement framebuffer creation and management

### Phase 2.3: Pipeline State Objects
1. Create `GraphicsPipeline` interface and Vulkan implementation
2. Add pipeline state descriptions (vertex input, rasterization, etc.)
3. Implement pipeline creation with shader stages

### Phase 2.4: Shader Management
1. Create `Shader` interface and Vulkan implementation
2. Add shader module creation from SPIR-V code
3. Implement shader stage management

### Phase 2.5: Command Buffer Extensions
1. Extend `CommandBuffer` interface with render pass commands
2. Add pipeline and buffer binding methods
3. Implement draw call commands

### Phase 2.6: Frame Execution Pipeline
1. Integrate all components into frame execution
2. Implement timeline semaphore synchronization
3. Add frame statistics and profiling

## Validation and Testing Strategy

### Unit Tests
- Test swapchain creation and destruction
- Test render pass and framebuffer creation
- Test pipeline creation with various state configurations
- Test shader module creation from SPIR-V

### Integration Tests
- Test complete frame execution pipeline
- Test swapchain resize and recreation
- Test pipeline cache functionality
- Test multisampling and depth/stencil operations

### Performance Tests
- Measure pipeline creation time
- Measure frame execution time
- Measure swapchain acquire/present overhead
- Test different present modes and vsync options

### Stress Tests
- Test frame rate stability over time
- Test memory usage and leaks
- Test swapchain operation under high load
- Test pipeline state changes per frame
