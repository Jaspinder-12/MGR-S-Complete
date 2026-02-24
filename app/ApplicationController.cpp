/*
 * Project: MGR-S (Multi-GPU Runtime System)
 * Author: Jaspinder
 * Description: Part of the MGR-S project
 * License: See LICENSE file
 */

#include "ApplicationController.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <iomanip>
#include "mgrs/context.h"

struct ApplicationController::Impl {
    std::unique_ptr<mgrs::Context> context;
    bool initialized;
    std::string lastError;
    RuntimeState state;
    
    Impl() : initialized(false), state(RuntimeState::STARTING) {}
};

ApplicationController::ApplicationController() : m_impl(std::make_unique<Impl>()) {}

ApplicationController::~ApplicationController() {
    shutdown();
}

bool ApplicationController::initialize() {
    try {
        mgrs::ContextCreateInfo info;
        info.apiVersion = 0x10000000;  // VK_API_VERSION_1_0
        mgrs::Context* ctx;
        
        auto result = mgrs::Context::Create(info, &ctx);
        if (result != mgrs::Result::Success) {
            m_impl->lastError = "Failed to create context";
            m_impl->state = RuntimeState::ERROR;
            return false;
        }
        
        m_impl->context.reset(ctx);
        m_impl->initialized = true;
        
        // Check if we have valid device capabilities
        auto deviceCount = ctx->GetDeviceCount();
        bool hasValidCapabilities = (deviceCount > 0);
        
        if (deviceCount > 0) {
            for (uint32_t i = 0; i < deviceCount; ++i) {
                const auto& caps = ctx->GetDeviceCapabilities(i);
                if (caps.computeFlops == 0 && caps.rasterPixels == 0 && caps.raytraceTriangles == 0) {
                    hasValidCapabilities = false;
                    break;
                }
            }
        }
        
        if (hasValidCapabilities) {
            m_impl->state = RuntimeState::RUNNING;
        } else {
            m_impl->state = RuntimeState::DEGRADED;
            m_impl->lastError = "Device capabilities not properly measured";
        }
        
        return true;
        
    } catch (const std::exception& e) {
        m_impl->lastError = "Exception during initialization: " + std::string(e.what());
        m_impl->state = RuntimeState::ERROR;
        return false;
    }
}

void ApplicationController::printDashboard() {
    // No-op in UI version - dashboard is displayed in Qt interface
}

void ApplicationController::run() {
    if (!m_impl->initialized) {
        m_impl->lastError = "Application not initialized";
        m_impl->state = RuntimeState::ERROR;
        printDashboard();
        return;
    }
    
    // In UI version, the run method doesn't need to do anything
    // The UI will update the dashboard periodically
}

void ApplicationController::shutdown() {
    if (m_impl->initialized) {
        std::cout << "Shutting down application...\n";
        m_impl->context.reset();
        m_impl->initialized = false;
    }
}

ApplicationController::RuntimeState ApplicationController::getState() const {
    return m_impl->state;
}

std::string ApplicationController::getStateString() const {
    switch (m_impl->state) {
        case RuntimeState::STARTING:
            return "STARTING";
        case RuntimeState::RUNNING:
            return "RUNNING";
        case RuntimeState::DEGRADED:
            return "DEGRADED";
        case RuntimeState::ERROR:
            return "ERROR";
        default:
            return "UNKNOWN";
    }
}

const std::string& ApplicationController::getLastError() const {
    return m_impl->lastError;
}

std::string ApplicationController::getApiVersionString() const {
    if (!m_impl->initialized || !m_impl->context) {
        return "Unavailable (alpha)";
    }
    
    uint32_t apiVersion = m_impl->context->GetApiVersion();
    if (apiVersion == 0) {
        return "Unavailable (alpha)";
    }
    
    // Vulkan API version format: VK_MAKE_VERSION(major, minor, patch) = (major << 22) | (minor << 12) | patch
    uint32_t major = (apiVersion >> 22) & 0x7FF;
    uint32_t minor = (apiVersion >> 12) & 0x3FF;
    uint32_t patch = apiVersion & 0xFFF;
    
    return std::to_string(major) + "." + std::to_string(minor) + "." + std::to_string(patch);
}

std::string ApplicationController::getGpuCountString() const {
    if (!m_impl->initialized || !m_impl->context) {
        return "Unavailable (alpha)";
    }
    
    uint32_t gpuCount = m_impl->context->GetGpuCount();
    if (gpuCount == 0) {
        return "Unavailable (alpha)";
    }
    
    return std::to_string(gpuCount);
}

std::string ApplicationController::getAuthorityGpuString() const {
    if (!m_impl->initialized || !m_impl->context) {
        return "Unavailable (alpha)";
    }
    
    uint32_t deviceCount = m_impl->context->GetDeviceCount();
    uint32_t authorityIndex = m_impl->context->GetAuthorityGpuIndex();
    
    if (deviceCount == 0 || authorityIndex >= deviceCount) {
        return "Unavailable (alpha)";
    }
    
    return m_impl->context->GetDeviceName(authorityIndex);
}
