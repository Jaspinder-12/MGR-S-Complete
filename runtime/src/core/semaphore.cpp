#include "mgrs/semaphore.h"

namespace mgrs {
    TimelineSemaphore* TimelineSemaphore::Create(Context* context) {
        return nullptr; // TODO: Implement
    }

    void TimelineSemaphore::Destroy(TimelineSemaphore* semaphore) {
        delete semaphore;
    }
}
