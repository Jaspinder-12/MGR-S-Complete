#include "mgrs/context.h"
#include "mgrs/scheduler.h"
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

std::string ToHex(const uint8_t *bytes, size_t size) {
  std::stringstream ss;
  for (size_t i = 0; i < size; ++i) {
    ss << std::hex << std::setw(2) << std::setfill('0') << (int)bytes[i];
  }
  return ss.str();
}

int main() {
  mgrs::ContextCreateInfo info = {};
  info.apiVersion = VK_API_VERSION_1_2;

  mgrs::Context *context = nullptr;
  mgrs::Result result = mgrs::Context::Create(info, &context);

  if (result != mgrs::Result::Success) {
    std::cout << "{\"error\": \"Failed to create Vulkan context\", \"code\": "
              << (int)result << "}" << std::endl;
    return 1;
  }

  uint32_t gpuCount = context->GetGpuCount();
  uint32_t authIndex = context->GetAuthorityGpuIndex();

  std::cout << "{" << std::endl;
  std::cout << "  \"gpu_count\": " << gpuCount << "," << std::endl;
  std::cout << "  \"authority_index\": " << authIndex << "," << std::endl;
  std::cout << "  \"gpus\": [" << std::endl;

  std::vector<mgrs::DeviceCapabilities> allCaps;
  for (uint32_t i = 0; i < gpuCount; ++i) {
    const auto &caps = context->GetDeviceCapabilities(i);
    allCaps.push_back(caps);

    std::cout << "    {" << std::endl;
    std::cout << "      \"index\": " << i << "," << std::endl;
    std::cout << "      \"name\": \"" << context->GetDeviceName(i) << "\","
              << std::endl;
    std::cout << "      \"driver_version\": \"" << context->GetDriverVersion(i)
              << "\"," << std::endl;
    std::cout << "      \"vram_mb\": " << (caps.vramTotal / (1024 * 1024))
              << "," << std::endl;
    std::cout << "      \"compute_flops\": " << caps.computeFlops << ","
              << std::endl;
    std::cout << "      \"raster_pixels\": " << caps.rasterPixels << ","
              << std::endl;
    std::cout << "      \"raytrace_triangles\": " << caps.raytraceTriangles
              << "," << std::endl;
    std::cout << "      \"luid\": \""
              << (caps.hasLUID ? ToHex(caps.deviceLUID, VK_LUID_SIZE) : "")
              << "\"" << std::endl;
    std::cout << "    }" << (i < gpuCount - 1 ? "," : "") << std::endl;
  }
  std::cout << "  ]," << std::endl;

  // Runtime Loop (Prototype v0.3)
  mgrs::EamrScheduler scheduler(allCaps);
  std::cout << "  \"runtime_loop\": [" << std::endl;

  for (int frame = 0; frame < 60; ++frame) {
    auto tasks = scheduler.BuildFramePackets(3840, 2160);

    std::cout << "    {" << std::endl;
    std::cout << "      \"frame_id\": " << frame << "," << std::endl;
    std::cout << "      \"tasks\": [" << std::endl;
    for (size_t i = 0; i < tasks.size(); ++i) {
      std::cout << "        {\"gpu\": " << tasks[i].gpuIndex
                << ", \"w\": " << tasks[i].w
                << ", \"sig\": " << tasks[i].signalValue << "}"
                << (i < tasks.size() - 1 ? "," : "") << std::endl;
    }
    std::cout << "      ]" << std::endl;
    std::cout << "    }" << (frame < 59 ? "," : "") << std::endl;

    // Simulate work: GPU0 is fast, GPU1 is slow
    scheduler.RecordCompletion(0, 8.0f); // 8ms
    scheduler.RecordCompletion(
        1, 24.0f); // 24ms (Slow node triggers PID reduction)
  }

  std::cout << "  ]" << std::endl;
  std::cout << "}" << std::endl;

  mgrs::Context::Destroy(context);
  return 0;
}
