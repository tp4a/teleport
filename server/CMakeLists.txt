MESSAGE(STATUS "operation system is ${CMAKE_SYSTEM}")

cmake_minimum_required(VERSION 3.5)
#project(teleport)

#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

#set(SOURCE_FILES main.cpp)
#add_executable(teleport ${SOURCE_FILES})
#set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${teleport_SOURCE_DIR}/../out/server/x64/bin")


IF (CMAKE_SYSTEM_NAME MATCHES "Linux")
	MESSAGE(STATUS "build on Linux...")
	add_subdirectory(tp_web/src)
ELSEIF (CMAKE_SYSTEM_NAME MATCHES "Windows")
	MESSAGE(FATAL_ERROR "unsupported platform: Windows")
ELSEIF (CMAKE_SYSTEM_NAME MATCHES "Darwin")
	MESSAGE(STATUS "build on MacOS...")
ELSE ()
	MESSAGE(FATAL_ERROR "unsupported platform: ${CMAKE_SYSTEM_NAME}")
ENDIF (CMAKE_SYSTEM_NAME MATCHES "Linux")

add_subdirectory(tp_core/core)
add_subdirectory(tp_core/protocol/ssh)
add_subdirectory(tp_core/protocol/telnet)
#add_subdirectory(testssh/testssh)

IF (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/tp_core/protocol/rdp")
	add_subdirectory(tp_core/protocol/rdp)
ENDIF (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/tp_core/protocol/rdp")

