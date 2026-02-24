#include "mgrs/vulkan/vulkan_shader.h"
#include "mgrs/vulkan/vulkan_context.h"
#include <cstring>

namespace mgrs {
    namespace vulkan {
        VulkanShader::VulkanShader()
            : m_context(nullptr)
            , m_shaderModule(VK_NULL_HANDLE)
            , m_stage(ShaderStage::Vertex)
            , m_entryPoint(nullptr)
        {}

        Result VulkanShader::Create(VulkanContext* context, const ShaderCreateInfo& info, VulkanShader** outShader) {
            if (!context || !outShader) {
                return Result::ErrorInvalidArgument;
            }

            auto shader = new VulkanShader();
            if (!shader) {
                return Result::ErrorOutOfMemory;
            }

            Result result = shader->Initialize(context, info);
            if (result != Result::Success) {
                delete shader;
                return result;
            }

            *outShader = shader;
            return Result::Success;
        }

        void VulkanShader::Destroy(VulkanShader* shader) {
            if (shader) {
                shader->Cleanup();
                delete shader;
            }
        }

        Result VulkanShader::Initialize(VulkanContext* context, const ShaderCreateInfo& info) {
            m_context = context;
            m_stage = info.stage;
            m_entryPoint = info.entryPoint;

            return CreateShaderModule(info);
        }

        Result VulkanShader::CreateShaderModule(const ShaderCreateInfo& info) {
            VkShaderModuleCreateInfo createInfo{};
            createInfo.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
            createInfo.codeSize = info.spirvSize;
            createInfo.pCode = reinterpret_cast<const uint32_t*>(info.spirvCode);

            // For now, we'll just create a dummy shader module
            m_shaderModule = reinterpret_cast<VkShaderModule>(1);

            return Result::Success;
        }

        ShaderStage VulkanShader::GetStage() const {
            return m_stage;
        }

        const char* VulkanShader::GetEntryPoint() const {
            return m_entryPoint;
        }

        VkShaderModule VulkanShader::GetVkShaderModule() const {
            return m_shaderModule;
        }

        VkShaderStageFlagBits VulkanShader::GetVkShaderStage() const {
            return (m_stage == ShaderStage::Vertex) ? VK_SHADER_STAGE_VERTEX_BIT : VK_SHADER_STAGE_FRAGMENT_BIT;
        }

        void VulkanShader::Cleanup() {
            m_shaderModule = VK_NULL_HANDLE;
            m_entryPoint = nullptr;
        }

        VulkanShader::~VulkanShader() {
            Cleanup();
        }
    }
}
