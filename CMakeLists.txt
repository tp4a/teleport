cmake_minimum_required(VERSION 3.5)
project(teleport)

include(CMakeCfg.txt)

if (OS_LINUX)
    add_subdirectory(server/tp_web/src)
endif()

add_subdirectory(server/tp_core/core)
add_subdirectory(server/tp_core/protocol/ssh)
add_subdirectory(server/tp_core/protocol/telnet)
add_subdirectory(server/tp_core/testssh)

if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/server/tp_core/protocol/rdp")
    add_subdirectory(server/tp_core/protocol/rdp)
endif ()
