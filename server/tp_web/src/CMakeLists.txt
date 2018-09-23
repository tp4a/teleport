cmake_minimum_required(VERSION 3.5)
project(tpweb)

#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${Project_SOURCE_DIR}/../out/server/x64/bin")

set(CMAKE_EXE_LINKER_FLAGS "-export-dynamic")

aux_source_directory(. DIR_SRCS)
aux_source_directory(../../../common/libex/src DIR_SRCS)
aux_source_directory(../../../common/pyshell/src DIR_SRCS)

include_directories(
        ../../../common/libex/include
        ../../../common/pyshell/include
        ../../../external/linux/release/include
        ../../../external/linux/release/include/python
)

link_directories(../../../external/linux/release/lib)

add_executable(tp_web ${DIR_SRCS})
#target_link_libraries(tp_web python3.7m ssl crypto dl pthread rt util)
target_link_libraries(tp_web python3.7m ssl crypto dl pthread rt util)
