cmake_minimum_required(VERSION 3.5)
#project(teleport)

#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

#set(SOURCE_FILES main.cpp)
#add_executable(teleport ${SOURCE_FILES})
#set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${teleport_SOURCE_DIR}/../out/server/x64/bin")

add_subdirectory(tp_web/src)
add_subdirectory(tp_core/core)
#add_subdirectory(tp_core/protocol/ssh)
