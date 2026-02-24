/*
 * Project: MGR-S (Multi-GPU Runtime System)
 * Author: Jaspinder
 * Description: Part of the MGR-S project
 * License: See LICENSE file
 */

#include "mgrs/shader.h"
#include "mgrs/vulkan/vulkan_shader.h"
#include "mgrs/vulkan/vulkan_context.h"

namespace mgrs {

Result Shader::Create(Context* context, const ShaderCreateInfo& info, Shader** outShader) {
    if (!context || !outShader) {
        return Result::ErrorInvalidArgument;
    }

    auto vulkanContext = dynamic_cast<vulkan::VulkanContext*>(context);
    if (vulkanContext) {
        return vulkan::VulkanShader::Create(vulkanContext, info, reinterpret_cast<vulkan::VulkanShader**>(outShader));
    }

    return Result::ErrorDeviceNotFound;
}

void Shader::Destroy(Shader* shader) {
    if (!shader) {
        return;
    }

    auto vulkanShader = dynamic_cast<vulkan::VulkanShader*>(shader);
    if (vulkanShader) {
        vulkan::VulkanShader::Destroy(vulkanShader);
        return;
    }

    delete shader;
}

} // namespace mgrs
