#ifndef __MGRS_VULKAN_SWAPCHAIN_H
#define __MGRS_VULKAN_SWAPCHAIN_H

#include "mgrs/swapchain.h"
#include "mgrs/vulkan/vulkan_context.h"
#include <vector>
#include <vulkan/vulkan.h>

namespace mgrs {
    namespace vulkan {
        class VulkanSwapchain : public Swapchain {
        public:
            static Result Create(VulkanContext* context, const SwapchainCreateInfo& info, VulkanSwapchain** outSwapchain);
            static void Destroy(VulkanSwapchain* swapchain);

            uint32_t GetImageCount() const override;
            VkImage GetImage(uint32_t index) const override;
            VkImageView GetImageView(uint32_t index) const override;
            Result AcquireNextImage(TimelineSemaphore* semaphore, uint64_t signalValue, uint32_t* outImageIndex) override;
            Result Present(uint32_t imageIndex, TimelineSemaphore* waitSemaphore, uint64_t waitValue) override;
            Result Recreate(const SwapchainCreateInfo& info) override;
            bool IsOutOfDate() const override;

            ~VulkanSwapchain() override;

        private:
            VulkanSwapchain(); // Private constructor to enforce Create method
            Result Initialize(VulkanContext* context, const SwapchainCreateInfo& info);
            Result CreateSwapchain(const SwapchainCreateInfo& info);
            Result CreateImageViews();
            void Cleanup();

            VulkanContext* m_context;
            VkSwapchainKHR m_swapchain;
            std::vector<VkImage> m_images;
            std::vector<VkImageView> m_imageViews;
            VkFormat m_imageFormat;
            VkExtent2D m_extent;
            bool m_outOfDate;
        };
    }
}

#endif // __MGRS_VULKAN_SWAPCHAIN_H
