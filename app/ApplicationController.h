/*
 * Project: MGR-S (Multi-GPU Runtime System)
 * Author: Jaspinder
 * Description: Part of the MGR-S project
 * License: See LICENSE file
 */

#pragma once

#include <memory>
#include <string>

class ApplicationController {
public:
    enum class RuntimeState {
        STARTING,
        RUNNING,
        DEGRADED,
        ERROR
    };

    ApplicationController();
    ~ApplicationController();
    
    bool initialize();
    void run();
    void shutdown();
    
    const std::string& getLastError() const;
    RuntimeState getState() const;
    std::string getStateString() const;
    
    // Metrics accessors
    std::string getApiVersionString() const;
    std::string getGpuCountString() const;
    std::string getAuthorityGpuString() const;

private:
    void printDashboard();
    
    struct Impl;
    std::unique_ptr<Impl> m_impl;
};
