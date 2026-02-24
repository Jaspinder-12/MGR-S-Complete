#ifndef __MGRS_VULKAN_MEMORY_H
#define __MGRS_VULKAN_MEMORY_H

#include "mgrs/context.h"
#include "mgrs/vulkan/vulkan_device.h"

namespace mgrs {
    namespace vulkan {
        class VulkanMemory {
        public:
            // Create a new Vulkan memory manager
            static Result Create(VulkanDevice* device, VulkanMemory** outMemory);
            
            // Initialize the memory manager
            Result Initialize();
            
            // Allocate memory
            void* Allocate(size_t size);
            
            // Free memory
            Result Free(void* ptr);
            
            // Get free memory
            size_t GetFreeMemory() const;
            
            ~VulkanMemory();
        };
    }
}

#endif // __MGRS_VULKAN_MEMORY_H
