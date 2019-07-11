cmake_minimum_required(VERSION 3.5)

MESSAGE(STATUS "=======================================================")
MESSAGE(STATUS "               testssh")
MESSAGE(STATUS "=======================================================")
include(../../../CMakeCfg.txt)

aux_source_directory(. DIR_SRCS)
aux_source_directory(../../../common/libex/src DIR_SRCS)

list(REMOVE_ITEM DIR_SRCS "./stdafx.cpp")

include_directories(
        ../../../common/libex/include
)

include_directories(
        ${TP_EXTERNAL_RELEASE_DIR}/include
)
link_directories(${TP_EXTERNAL_RELEASE_DIR}/lib)


add_executable(testssh ${DIR_SRCS})

if (OS_LINUX)
    set(CMAKE_EXE_LINKER_FLAGS "-export-dynamic")
    target_link_libraries(testssh ssh ssl crypto dl pthread rt util)
elseif (OS_MACOS)
    target_link_libraries(testssh ssh ssl crypto dl pthread util)
endif ()
