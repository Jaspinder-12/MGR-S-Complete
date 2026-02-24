/*
 * Project: MGR-S (Multi-GPU Runtime System)
 * Author: Jaspinder
 * Description: Part of the MGR-S project
 * License: See LICENSE file
 */

#pragma once

#include "mgrs/context.h"
#include <vector>
#include <cstdint>

namespace mgrs {

enum class ShaderStage {
    Vertex,
    Fragment
};

struct ShaderCreateInfo {
    ShaderStage stage;
    const uint8_t* spirvCode;
    size_t spirvSize;
    const char* entryPoint;
};

class Shader {
public:
    static Result Create(Context* context, const ShaderCreateInfo& info, Shader** outShader);
    static void Destroy(Shader* shader);

    virtual ShaderStage GetStage() const = 0;
    virtual const char* GetEntryPoint() const = 0;

    virtual ~Shader() = default;
};

} // namespace mgrs
