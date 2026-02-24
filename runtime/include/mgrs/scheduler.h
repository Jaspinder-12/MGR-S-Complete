#ifndef __MGRS_SCHEDULER_H
#define __MGRS_SCHEDULER_H

#include "mgrs/types.h"
#include <cstdint>
#include <vector>

namespace mgrs {

enum class TaskType { G_BUFFER, SHADOW_OR_GI, COMPOSITE, PHYSICS };

struct FrameTask {
  uint32_t gpuIndex;
  uint32_t x, y, w, h;
  TaskType type;

  // Synchronization
  uint64_t waitValue;   // Timeline semaphore value to wait on
  uint64_t signalValue; // Timeline semaphore value to signal
};

class EamrScheduler {
public:
  explicit EamrScheduler(const std::vector<DeviceCapabilities> &caps);

  std::vector<FrameTask> BuildFramePackets(uint32_t screenWidth = 3840,
                                           uint32_t screenHeight = 2160);
  void RecordCompletion(uint32_t gpuIndex, float actualMs);

private:
  std::vector<DeviceCapabilities> m_caps;
  std::vector<float> m_weights;
  uint32_t m_authorityIndex;
  float m_targetFrameTime;
  uint64_t m_frameCount;

  // PID Balancer state
  struct PidState {
    float kp = 0.05f;
    float ki = 0.01f;
    float kd = 0.01f;
    float integral = 0.0f;
    float prevError = 0.0f;
  };
  std::vector<PidState> m_pidStates;
};
} // namespace mgrs

#endif // __MGRS_SCHEDULER_H
