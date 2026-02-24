#ifndef __MGRS_VULKAN_SEMAPHORE_H
#define __MGRS_VULKAN_SEMAPHORE_H

#include "mgrs/semaphore.h"
#include "mgrs/vulkan/vulkan_context.h"
#include <vulkan/vulkan.h>

namespace mgrs {
    namespace vulkan {
        class VulkanTimelineSemaphore : public TimelineSemaphore {
        public:
            static VulkanTimelineSemaphore* Create(VulkanContext* context);
            static void Destroy(VulkanTimelineSemaphore* semaphore);

            uint64_t GetValue() const override;
            Result WaitForValue(uint64_t value, uint64_t timeout = UINT64_MAX) override;
            Result SignalValue(uint64_t value) override;

            VkSemaphore GetVkSemaphore() const override;

            ~VulkanTimelineSemaphore() override;

        private:
            VulkanTimelineSemaphore();
            Result Initialize(VulkanContext* context);
            void Cleanup();

            VulkanContext* m_context;
            VkSemaphore m_semaphore;
            uint64_t m_value;
        };
    }
}

#endif // __MGRS_VULKAN_SEMAPHORE_H
