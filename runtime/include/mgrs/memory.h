#ifndef __MGRS_MEMORY_H
#define __MGRS_MEMORY_H

namespace mgrs {
    struct Memory {
        int initialize() { return 0; }
        void* allocate(size_t size) { return nullptr; }
        int free(void* ptr) { return 0; }
        int getFreeMemory() { return 0; } // in bytes
    };
}

#endif // __MGRS_MEMORY_H
