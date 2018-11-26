cmake_minimum_required(VERSION 3.5)

MESSAGE(STATUS "=======================================================")
MESSAGE(STATUS "               libtptelnet")
MESSAGE(STATUS "=======================================================")
#MESSAGE(STATUS "operation system is ${CMAKE_SYSTEM}")
#MESSAGE(STATUS "current source directory is ${CMAKE_CURRENT_SOURCE_DIR}")

include(../../../CMakeCfg.txt)

#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

set(CMAKE_EXE_LINKER_FLAGS "-export-dynamic")

aux_source_directory(. DIR_SRCS)
aux_source_directory(../../../common/libex/src DIR_SRCS)
aux_source_directory(../../../common/pyshell/src DIR_SRCS)

include_directories(
        ../../../common/libex/include
        ../../../common/pyshell/include
)

include_directories(
        ${TP_EXTERNAL_RELEASE_DIR}/include
        ${TP_EXTERNAL_RELEASE_DIR}/include/python
)
link_directories(${TP_EXTERNAL_RELEASE_DIR}/lib)

add_executable(tp_web ${DIR_SRCS})
target_link_libraries(tp_web python3.7m ssl crypto dl pthread rt util)
