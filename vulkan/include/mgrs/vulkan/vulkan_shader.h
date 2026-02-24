#ifndef __MGRS_VULKAN_SHADER_H
#define __MGRS_VULKAN_SHADER_H

#include "mgrs/shader.h"
#include "mgrs/vulkan/vulkan_context.h"
#include <vulkan/vulkan.h>

namespace mgrs {
    namespace vulkan {
        class VulkanShader : public Shader {
        public:
            static Result Create(VulkanContext* context, const ShaderCreateInfo& info, VulkanShader** outShader);
            static void Destroy(VulkanShader* shader);

            ShaderStage GetStage() const override;
            const char* GetEntryPoint() const override;

            VkShaderModule GetVkShaderModule() const;
            VkShaderStageFlagBits GetVkShaderStage() const;

            ~VulkanShader() override;

        private:
            VulkanShader();
            Result Initialize(VulkanContext* context, const ShaderCreateInfo& info);
            Result CreateShaderModule(const ShaderCreateInfo& info);
            void Cleanup();

            VulkanContext* m_context;
            VkShaderModule m_shaderModule;
            ShaderStage m_stage;
            const char* m_entryPoint;
        };
    }
}

#endif // __MGRS_VULKAN_SHADER_H
