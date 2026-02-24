cmake_minimum_required(VERSION 3.15)

project(mgrs_app LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(mgrs_app
    main.cpp
    ApplicationController.h
    ApplicationController.cpp
)

add_executable(test_unavailable
    test_unavailable.cpp
    ApplicationController.h
    ApplicationController.cpp
)

add_executable(test_pipeline
    test_pipeline.cpp
)

add_executable(mgrs_bridge
    mgrs_bridge.cpp
)

target_include_directories(mgrs_app
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_SOURCE_DIR}/runtime/include
        ${CMAKE_SOURCE_DIR}/vulkan/include
)

target_include_directories(test_unavailable
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_SOURCE_DIR}/runtime/include
        ${CMAKE_SOURCE_DIR}/vulkan/include
)

target_include_directories(test_pipeline
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_SOURCE_DIR}/runtime/include
        ${CMAKE_SOURCE_DIR}/vulkan/include
)

target_include_directories(mgrs_bridge
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_SOURCE_DIR}/runtime/include
        ${CMAKE_SOURCE_DIR}/vulkan/include
)

# Link with MGR-S library
target_link_libraries(mgrs_app
    PRIVATE
        mgrs
)

target_link_libraries(test_unavailable
    PRIVATE
        mgrs
)

target_link_libraries(test_pipeline
    PRIVATE
        mgrs
)

target_link_libraries(mgrs_bridge
    PRIVATE
        mgrs
)

if(WIN32)
    # Copy Vulkan libraries if needed
    find_package(Vulkan REQUIRED)
    target_link_libraries(test_pipeline PRIVATE Vulkan::Vulkan)
endif()

if(WIN32)
    # Copy Vulkan libraries if needed
    find_package(Vulkan REQUIRED)
    target_link_libraries(mgrs_app PRIVATE Vulkan::Vulkan)
    target_link_libraries(test_unavailable PRIVATE Vulkan::Vulkan)
    target_link_libraries(mgrs_bridge PRIVATE Vulkan::Vulkan)
endif()

# Set output directory
set_target_properties(mgrs_app PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)

set_target_properties(test_unavailable PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)

set_target_properties(mgrs_bridge PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)
