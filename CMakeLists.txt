cmake_minimum_required(VERSION 3.5)
project(teleport)

include(CMakeCfg.txt)

#MESSAGE(STATUS "operation system is ${CMAKE_SYSTEM}")
#MESSAGE(STATUS "current source directory is ${CMAKE_CURRENT_SOURCE_DIR}")
#
#set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/out/server/x64/bin")
#set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/out/server/x64/bin")
#
#set(CMAKE_CONFIGURATION_TYPES Debug Release)
#
## Determine the platform.
#if ("${CMAKE_SYSTEM_NAME}" STREQUAL "Darwin")
#    MESSAGE(STATUS "build on macOS...")
#    set(OS_MACOS 1)
#    set(OS_POSIX 1)
#    set(TP_EXTERNAL_RELEASE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external/macos/release")
#elseif ("${CMAKE_SYSTEM_NAME}" STREQUAL "Linux")
#    set(OS_LINUX 1)
#    set(OS_POSIX 1)
#    MESSAGE(STATUS "build on Linux...")
#    add_subdirectory(server/tp_web/src)
#    set(TP_EXTERNAL_RELEASE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external/linux/release")
#elseif ("${CMAKE_SYSTEM_NAME}" STREQUAL "Windows")
#    #    MESSAGE(FATAL_ERROR "unsupported platform: Windows")
#else ()
#    MESSAGE(FATAL_ERROR "unsupported platform: ${CMAKE_SYSTEM_NAME}")
#endif ()

if (OS_LINUX)
    add_subdirectory(server/tp_web/src)
endif()

add_subdirectory(server/tp_core/core)
add_subdirectory(server/tp_core/protocol/ssh)
add_subdirectory(server/tp_core/protocol/telnet)
#add_subdirectory(server/testssh/testssh)

if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/server/tp_core/protocol/rdp")
    add_subdirectory(server/tp_core/protocol/rdp)
endif ()
