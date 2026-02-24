#pragma once

#include "mgrs/types.h"

namespace mgrs {

class Context;

class TimelineSemaphore {
public:
    typedef TimelineSemaphore* (*CreateFunc)(Context*);
    static TimelineSemaphore* Create(Context* context);
    static void Destroy(TimelineSemaphore* semaphore);

    virtual uint64_t GetValue() const = 0;
    virtual Result WaitForValue(uint64_t value, uint64_t timeout = UINT64_MAX) = 0;
    virtual Result SignalValue(uint64_t value) = 0;

    virtual VkSemaphore GetVkSemaphore() const = 0;

protected:
    TimelineSemaphore() = default;
    virtual ~TimelineSemaphore() = default;
    TimelineSemaphore(const TimelineSemaphore&) = delete;
    TimelineSemaphore& operator=(const TimelineSemaphore&) = delete;
};

}  // namespace mgrs
