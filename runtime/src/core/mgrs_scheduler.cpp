#include "mgrs/scheduler.h"
#include <algorithm>
#include <numeric>

namespace mgrs {

EamrScheduler::EamrScheduler(const std::vector<DeviceCapabilities> &caps)
    : m_caps(caps), m_authorityIndex(0), m_targetFrameTime(16.67f),
      m_frameCount(0) // Default 60 FPS
{
  m_weights.resize(caps.size());
  m_pidStates.resize(caps.size());
  uint64_t totalVram = 0;

  // Initial weighting based on VRAM as a proxy for performance
  for (size_t i = 0; i < caps.size(); ++i) {
    m_weights[i] = static_cast<float>(caps[i].vramTotal);
    if (caps[i].vramTotal > totalVram) {
      totalVram = caps[i].vramTotal;
      m_authorityIndex = static_cast<uint32_t>(i);
    }
  }

  float sum = std::accumulate(m_weights.begin(), m_weights.end(), 0.0f);
  if (sum > 0) {
    for (auto &w : m_weights)
      w /= sum;
  } else {
    std::fill(m_weights.begin(), m_weights.end(), 1.0f / caps.size());
  }
}

std::vector<FrameTask> EamrScheduler::BuildFramePackets(uint32_t screenWidth,
                                                        uint32_t screenHeight) {
  std::vector<FrameTask> tasks;
  uint32_t currentX = 0;
  m_frameCount++;

  for (uint32_t i = 0; i < m_weights.size(); ++i) {
    uint32_t tileW = static_cast<uint32_t>(screenWidth * m_weights[i]);

    // Ensure last GPU fills the screen
    if (i == m_weights.size() - 1) {
      tileW = screenWidth - currentX;
    }

    if (tileW > 0) {
      FrameTask task;
      task.gpuIndex = i;
      task.x = currentX;
      task.y = 0;
      task.w = tileW;
      task.h = screenHeight;
      task.type =
          (i == m_authorityIndex) ? TaskType::G_BUFFER : TaskType::SHADOW_OR_GI;

      // Every frame, a GPU signals its completion value
      // Assistant GPUs signal, Authority waits before COMPOSITE
      task.waitValue =
          0; // Standard tasks usually don't wait on previous frames here
      task.signalValue = m_frameCount;

      tasks.push_back(task);
      currentX += tileW;
    }
  }

  return tasks;
}

void EamrScheduler::RecordCompletion(uint32_t gpuIndex, float actualMs) {
  if (gpuIndex >= m_weights.size())
    return;

  // PID Balancer logic
  float error = std::max(0.0f, actualMs - m_targetFrameTime);
  auto &pid = m_pidStates[gpuIndex];

  pid.integral += error;
  float derivative = error - pid.prevError;
  float output =
      (pid.kp * error) + (pid.ki * pid.integral) + (pid.kd * derivative);
  pid.prevError = error;

  // Adjust weight based on PID output (inverse relationship: more output =
  // slower = less weight)
  if (output > 0.01f) {
    m_weights[gpuIndex] *= (1.0f - std::min(0.05f, output * 0.1f));
  } else if (actualMs < m_targetFrameTime * 0.9f) {
    m_weights[gpuIndex] *= 1.02f; // Slight boost if significantly faster
  }

  // Re-normalize
  float sum = std::accumulate(m_weights.begin(), m_weights.end(), 0.0f);
  if (sum > 0) {
    for (auto &w : m_weights)
      w /= sum;
  }
}

} // namespace mgrs
