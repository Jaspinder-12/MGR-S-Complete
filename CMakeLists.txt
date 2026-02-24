cmake_minimum_required(VERSION 3.15)

project(mgrs_project LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Vulkan
find_package(Vulkan REQUIRED)

# Add runtime library
add_library(mgrs STATIC
    runtime/src/core/context.cpp
    runtime/src/core/swapchain.cpp
    runtime/src/core/render_pass.cpp
    runtime/src/core/shader.cpp
    runtime/src/core/pipeline_layout.cpp
    runtime/src/core/pipeline.cpp
    runtime/src/core/command_buffer.cpp
    runtime/src/core/semaphore.cpp
    runtime/src/core/mgrs_scheduler.cpp
    vulkan/src/backend/vulkan_context.cpp
    vulkan/src/backend/vulkan_device.cpp
    vulkan/src/backend/vulkan_memory.cpp
    vulkan/src/backend/vulkan_swapchain.cpp
    vulkan/src/backend/vulkan_render_pass.cpp
    vulkan/src/backend/vulkan_shader.cpp
    vulkan/src/backend/vulkan_pipeline_layout.cpp
    vulkan/src/backend/vulkan_pipeline.cpp
    vulkan/src/backend/vulkan_command_buffer.cpp
    vulkan/src/backend/vulkan_semaphore.cpp
)

target_include_directories(mgrs
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/runtime/include>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/vulkan/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(mgrs
    PRIVATE
        Vulkan::Vulkan
)

# Add application
add_subdirectory(app)

# Optional: Add test directory if present
option(BUILD_TESTS "Build unit tests" OFF)
if(BUILD_TESTS AND EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/test)
    add_subdirectory(test)
endif()

# Optional: Add docs directory if present and contains CMakeLists.txt
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/docs AND EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/docs/CMakeLists.txt)
    add_subdirectory(docs)
endif()
