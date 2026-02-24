#include "mgrs/context.h"
#include <iostream>

int main() {
    try {
        std::cout << "Testing MGR-S headers...\n";
        
        mgrs::ContextCreateInfo info;
        info.apiVersion = 0x10000000;  // VK_API_VERSION_1_0
        
        mgrs::Context* ctx;
        auto result = mgrs::Context::Create(info, &ctx);
        
        if (result == mgrs::Result::Success) {
            std::cout << "Successfully created MGR-S context!\n";
            std::cout << "Number of devices: " << ctx->GetDeviceCount() << "\n";
            
            if (ctx->GetDeviceCount() > 0) {
                const auto& caps = ctx->GetDeviceCapabilities(0);
                std::cout << "Device 0 capabilities:\n";
                std::cout << "  Compute: " << caps.computeFlops << " FLOPS\n";
                std::cout << "  Raster: " << caps.rasterPixels << " pixels/s\n";
                std::cout << "  Raytrace: " << caps.raytraceTriangles << " triangles/s\n";
                std::cout << "  VRAM: " << caps.vramTotal / (1024 * 1024 * 1024) << " GB\n";
            }
            
            mgrs::Context::Destroy(ctx);
        } else {
            std::cout << "Failed to create MGR-S context. Error: " << static_cast<int>(result) << "\n";
        }
        
        return 0;
        
    } catch (const std::exception& e) {
        std::cout << "Exception: " << e.what() << "\n";
        return 1;
    }
}
