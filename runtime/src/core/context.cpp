/*
 * Project: MGR-S (Multi-GPU Runtime System)
 * Author: Jaspinder
 * Description: Part of the MGR-S project
 * License: See LICENSE file
 */

#include "mgrs/context.h"
#include "mgrs/vulkan/vulkan_context.h"
#include <string>

namespace mgrs {

class ContextImpl : public Context {
public:
    ContextImpl(const ContextCreateInfo& info) : m_apiVersion(info.apiVersion) {
        // Initialize state
        m_state = RuntimeState::STARTING;
        
        // Mock device capabilities
        m_deviceCaps = {
            1000000000000, // 1 TFLOPS compute
            1000000000,    // 1 Gpixel/s raster
            100000000,     // 100 Mpixel/s raytrace
            8LL * 1024LL * 1024LL * 1024LL // 8 GB VRAM
        };
        
        // Transition to running state
        m_state = RuntimeState::RUNNING;
    }
    
    ~ContextImpl() override {
    }
    
    uint32_t GetDeviceCount() const override {
        return 1; // Assume we have 1 GPU for now
    }
    
    const DeviceCapabilities& GetDeviceCapabilities(uint32_t deviceIndex) const override {
        return m_deviceCaps;
    }
    
    RuntimeState GetState() const override {
        return m_state;
    }
    
    uint32_t GetApiVersion() const override {
        return m_apiVersion;
    }
    
    uint32_t GetGpuCount() const override {
        return 1; // Assume we have 1 GPU for now
    }
    
    uint32_t GetAuthorityGpuIndex() const override {
        return 0; // First device is authority
    }
    
    std::string GetDeviceName(uint32_t deviceIndex) const override {
        return "Default Device " + std::to_string(deviceIndex);
    }

private:
    RuntimeState m_state;
    DeviceCapabilities m_deviceCaps;
    uint32_t m_apiVersion;
};

Result Context::Create(const ContextCreateInfo& info, Context** outContext) {
    if (outContext == nullptr) {
        return Result::ErrorInvalidArgument;
    }
    
    // For now, always create a Vulkan context
    mgrs::vulkan::VulkanContext* vulkanContext;
    Result result = mgrs::vulkan::VulkanContext::Create(info, &vulkanContext);
    if (result != Result::Success) {
        return result;
    }
    
    *outContext = vulkanContext;
    return Result::Success;
}

void Context::Destroy(Context* context) {
    if (context != nullptr) {
        delete context;
    }
}

} // namespace mgrs
