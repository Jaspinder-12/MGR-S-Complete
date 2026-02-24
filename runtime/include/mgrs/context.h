/*
 * Project: MGR-S (Multi-GPU Runtime System)
 * Author: Jaspinder
 * Description: Part of the MGR-S project
 * License: See LICENSE file
 */

#pragma once

#include "mgrs/types.h"
#include <memory>
#include <string>
#include <vector>


namespace mgrs {

class Context {
public:
  // Create a new context
  static Result Create(const ContextCreateInfo &info, Context **outContext);

  // Destroy a context
  static void Destroy(Context *context);

  // Get the number of available devices
  virtual uint32_t GetDeviceCount() const = 0;

  // Get device capabilities
  virtual const DeviceCapabilities &
  GetDeviceCapabilities(uint32_t deviceIndex) const = 0;

  // Get current runtime state
  virtual RuntimeState GetState() const = 0;

  // Get API version
  virtual uint32_t GetApiVersion() const = 0;

  // Get GPU count
  virtual uint32_t GetGpuCount() const = 0;

  // Get authority GPU index
  virtual uint32_t GetAuthorityGpuIndex() const = 0;

  // Get device name
  virtual std::string GetDeviceName(uint32_t deviceIndex) const = 0;

  // Get driver version
  virtual std::string GetDriverVersion(uint32_t deviceIndex) const = 0;

  virtual ~Context() = default;
};

} // namespace mgrs
