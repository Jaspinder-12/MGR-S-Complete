#include <iostream>
#include <fstream>
#include <vector>
#include <windows.h>
#include "mgrs/context.h"
#include "mgrs/shader.h"
#include "mgrs/pipeline_layout.h"
#include "mgrs/pipeline.h"
#include "mgrs/render_pass.h"
#include "mgrs/command_buffer.h"

std::vector<uint8_t> readFile(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << filename << "\n";
        return {};
    }

    file.seekg(0, std::ios::end);
    size_t size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::vector<uint8_t> buffer(size);
    file.read(reinterpret_cast<char*>(buffer.data()), size);
    return buffer;
}

int main() {
    try {
        std::cout << "=== Test Pipeline Creation and Command Buffer Integration ===\n";

        // Create context
        mgrs::ContextCreateInfo contextInfo;
        mgrs::Context* context;
        mgrs::Result result = mgrs::Context::Create(contextInfo, &context);
        if (result != mgrs::Result::Success) {
            std::cerr << "Failed to create context\n";
            return 1;
        }

        std::cout << "Context created successfully\n";

        // Load vertex shader
        std::vector<uint8_t> vertexShaderCode = readFile("j:/GPU linking/assets/shaders/simple.vert.spv");
        if (vertexShaderCode.empty()) {
            std::cerr << "Failed to read vertex shader file\n";
            mgrs::Context::Destroy(context);
            return 1;
        }

        mgrs::ShaderCreateInfo shaderInfo;
        shaderInfo.stage = mgrs::ShaderStage::Vertex;
        shaderInfo.spirvCode = vertexShaderCode.data();
        shaderInfo.spirvSize = vertexShaderCode.size();
        shaderInfo.entryPoint = "main";

        mgrs::Shader* vertexShader;
        result = mgrs::Shader::Create(context, shaderInfo, &vertexShader);
        if (result != mgrs::Result::Success) {
            std::cerr << "Failed to create vertex shader\n";
            mgrs::Context::Destroy(context);
            return 1;
        }

        std::cout << "Vertex shader created successfully\n";

        // Load fragment shader
        std::vector<uint8_t> fragmentShaderCode = readFile("j:/GPU linking/assets/shaders/simple.frag.spv");
        if (fragmentShaderCode.empty()) {
            std::cerr << "Failed to read fragment shader file\n";
            mgrs::Shader::Destroy(vertexShader);
            mgrs::Context::Destroy(context);
            return 1;
        }

        shaderInfo.stage = mgrs::ShaderStage::Fragment;
        shaderInfo.spirvCode = fragmentShaderCode.data();
        shaderInfo.spirvSize = fragmentShaderCode.size();
        mgrs::Shader* fragmentShader;
        result = mgrs::Shader::Create(context, shaderInfo, &fragmentShader);
        if (result != mgrs::Result::Success) {
            std::cerr << "Failed to create fragment shader\n";
            mgrs::Shader::Destroy(vertexShader);
            mgrs::Context::Destroy(context);
            return 1;
        }

        std::cout << "Fragment shader created successfully\n";

        // Create dummy pipeline layout
        mgrs::PipelineLayoutCreateInfo layoutInfo;
        mgrs::PipelineLayout* pipelineLayout;
        result = mgrs::PipelineLayout::Create(context, layoutInfo, &pipelineLayout);
        if (result != mgrs::Result::Success) {
            std::cerr << "Failed to create pipeline layout\n";
            mgrs::Shader::Destroy(vertexShader);
            mgrs::Shader::Destroy(fragmentShader);
            mgrs::Context::Destroy(context);
            return 1;
        }

        std::cout << "Pipeline layout created successfully\n";

        // Create dummy render pass
        mgrs::RenderPassCreateInfo renderPassInfo;
        mgrs::RenderPass* renderPass;
        result = mgrs::RenderPass::Create(context, renderPassInfo, &renderPass);
        if (result != mgrs::Result::Success) {
            std::cerr << "Failed to create render pass\n";
            mgrs::PipelineLayout::Destroy(pipelineLayout);
            mgrs::Shader::Destroy(vertexShader);
            mgrs::Shader::Destroy(fragmentShader);
            mgrs::Context::Destroy(context);
            return 1;
        }

        std::cout << "Render pass created successfully\n";

        // Create pipeline
        mgrs::GraphicsPipelineCreateInfo pipelineInfo;
        pipelineInfo.renderPass = renderPass;
        pipelineInfo.subpass = 0;
        pipelineInfo.shaders.push_back(vertexShader);
        pipelineInfo.shaders.push_back(fragmentShader);
        pipelineInfo.pipelineLayout = pipelineLayout;

        mgrs::Pipeline* pipeline;
        result = mgrs::Pipeline::Create(context, pipelineInfo, &pipeline);
        if (result != mgrs::Result::Success) {
            std::cerr << "Failed to create pipeline\n";
            mgrs::RenderPass::Destroy(renderPass);
            mgrs::PipelineLayout::Destroy(pipelineLayout);
            mgrs::Shader::Destroy(vertexShader);
            mgrs::Shader::Destroy(fragmentShader);
            mgrs::Context::Destroy(context);
            return 1;
        }

        std::cout << "Pipeline created successfully\n";

        // Create command buffer
        mgrs::CommandBuffer* commandBuffer;
        result = mgrs::CommandBuffer::Create(context, &commandBuffer);
        if (result != mgrs::Result::Success) {
            std::cerr << "Failed to create command buffer\n";
            mgrs::Pipeline::Destroy(pipeline);
            mgrs::RenderPass::Destroy(renderPass);
            mgrs::PipelineLayout::Destroy(pipelineLayout);
            mgrs::Shader::Destroy(vertexShader);
            mgrs::Shader::Destroy(fragmentShader);
            mgrs::Context::Destroy(context);
            return 1;
        }

        std::cout << "Command buffer created successfully\n";

        // Test pipeline binding
        result = commandBuffer->Begin();
        if (result != mgrs::Result::Success) {
            std::cerr << "Failed to begin command buffer\n";
        } else {
            result = commandBuffer->BindPipeline(pipeline);
            if (result != mgrs::Result::Success) {
                std::cerr << "Failed to bind pipeline\n";
            } else {
                std::cout << "Pipeline bound successfully\n";
            }

            result = commandBuffer->End();
            if (result != mgrs::Result::Success) {
                std::cerr << "Failed to end command buffer\n";
            }
        }

        // Cleanup
        mgrs::CommandBuffer::Destroy(commandBuffer);
        mgrs::Pipeline::Destroy(pipeline);
        mgrs::RenderPass::Destroy(renderPass);
        mgrs::PipelineLayout::Destroy(pipelineLayout);
        mgrs::Shader::Destroy(vertexShader);
        mgrs::Shader::Destroy(fragmentShader);
        mgrs::Context::Destroy(context);

        std::cout << "\n=== Test Complete ===\n";
        return 0;

    } catch (const std::exception& e) {
        std::cerr << "\nFatal error: " << e.what() << "\n";
        return 1;
    }
}
