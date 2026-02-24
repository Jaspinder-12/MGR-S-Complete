#pragma once

#include "mgrs/types.h"

namespace mgrs {

class Context;

class Resource {
public:
    virtual const ResourceDesc& GetDesc() const;
    virtual uint32_t GetOwnerDeviceIndex() const;

    // Buffer operations
    virtual VkBuffer GetVkBuffer() const;

    // Image operations
    virtual VkImage GetVkImage() const;
    virtual VkImageView GetVkImageView() const;

    // Memory operations
    virtual void* Map();
    virtual void Unmap();

protected:
    Resource();
    virtual ~Resource();
    Resource(const Resource&) = delete;
    Resource& operator=(const Resource&) = delete;

    class Impl;
    Impl* mImpl;
};

}  // namespace mgrs