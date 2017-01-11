cmake_minimum_required(VERSION 3.5)
project(tpssh)

#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC")

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${Project_SOURCE_DIR}/../out/server/x64/bin")


aux_source_directory(. DIR_SRCS)
aux_source_directory(../../common DIR_SRCS)
aux_source_directory(../../../../common/libex/src DIR_SRCS)
aux_source_directory(../../../../external/jsoncpp/src/lib_json DIR_SRCS)

list(REMOVE_ITEM DIR_SRCS "./dllmain.cpp")
list(REMOVE_ITEM DIR_SRCS "./stdafx.cpp")

include_directories(
        ../../../../common/libex/include
        ../../../../external/jsoncpp/include
        ../../../../external/linux/release/include
)

link_directories(../../../../external/linux/release/lib)

add_library(tpssh SHARED ${DIR_SRCS})
target_link_libraries(tpssh ssh ssl crypto mbedx509 mbedtls mbedcrypto dl pthread rt util)
#target_link_libraries(tpssh ssh mbedx509 mbedtls mbedcrypto dl pthread rt util)
