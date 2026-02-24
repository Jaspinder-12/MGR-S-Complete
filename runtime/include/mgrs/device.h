#ifndef __MGRS_DEVICE_H
#define __MGRS_DEVICE_H

namespace mgrs {
    struct Device {
        int initialize() { return 0; }
        int getDeviceType() { return 0; } // 0 for CPU, 1 for GPU, etc.
        int getMemorySize() { return 0; } // in bytes
    };
}

#endif // __MGRS_DEVICE_H
