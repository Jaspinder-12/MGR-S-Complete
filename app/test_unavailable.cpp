#include <iostream>
#include "ApplicationController.h"

int main() {
    try {
        std::cout << "=== Test ApplicationController with Unavailable Metrics ===\n";
        
        // Create application controller
        ApplicationController app;
        
        // Let's directly test the methods without initializing
        std::cout << "1. Not initialized state:\n";
        std::cout << "   Runtime State:  " << app.getStateString() << "\n";
        std::cout << "   API Version:    " << app.getApiVersionString() << "\n";
        std::cout << "   GPU Count:      " << app.getGpuCountString() << "\n";
        std::cout << "   Authority GPU:  " << app.getAuthorityGpuString() << "\n";
        
        std::cout << "\n2. Now initializing...\n";
        if (app.initialize()) {
            std::cout << "Initialization successful\n";
        } else {
            std::cout << "Initialization failed: " << app.getLastError() << "\n";
        }
        
        std::cout << "\n=== Test Complete ===\n";
        app.shutdown();
        
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "\nFatal error: " << e.what() << "\n";
        return 1;
    }
}
