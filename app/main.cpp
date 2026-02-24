#include <iostream>
#include <atomic>
#include <thread>
#include <chrono>
#include "ApplicationController.h"

std::atomic<bool> g_shutdownRequested(false);

void handleInput() {
    std::cout << "\nPress 'q' to quit...\n";
    char input;
    while (!g_shutdownRequested) {
        if (std::cin.peek() == 'q') {
            std::cin.get(input);
            g_shutdownRequested = true;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

int main() {
    try {
        // Start input handler in separate thread
        std::thread inputThread(handleInput);
        
        // Create application controller
        ApplicationController app;
        
        if (!app.initialize()) {
            std::cerr << "Failed to initialize application\n";
            g_shutdownRequested = true;
            inputThread.join();
            return 1;
        }
        
        // Run main application logic
        app.run();
        
        // Wait for shutdown
        while (!g_shutdownRequested) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
        // Cleanup
        inputThread.join();
        app.shutdown();
        
        std::cout << "\nApplication shutdown complete\n";
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "\nFatal error: " << e.what() << "\n";
        return 1;
    }
}
