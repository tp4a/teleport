cmake_minimum_required(VERSION 3.5)
project(tpcore)

#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${Project_SOURCE_DIR}/../out/server/x64/bin")


ADD_DEFINITIONS(
        -DMG_ENABLE_THREADS
        -DMG_DISABLE_HTTP_DIGEST_AUTH
        -DMG_DISABLE_MQTT
        -DMG_DISABLE_SSI
        -DHAVE_CONFIG_H
        -DCS_COMMON_MD5_H_
        -DDISABLE_MD5
)

set(CMAKE_EXE_LINKER_FLAGS "-export-dynamic")

aux_source_directory(. DIR_SRCS)
aux_source_directory(../../../common/libex/src DIR_SRCS)
aux_source_directory(../../../external/mongoose DIR_SRCS)
aux_source_directory(../../../external/jsoncpp/src/lib_json DIR_SRCS)

#list(REMOVE_ITEM DIR_SRCS "./src/ts_win_service_helper.cpp")

include_directories(
        ../../../common/libex/include
        ../../../external/mongoose
        ../../../external/jsoncpp/include
        ../../../external/linux/release/include
)

link_directories(../../../external/linux/release/lib)

add_executable(tp_core ${DIR_SRCS})
target_link_libraries(tp_core ssl crypto mbedx509 mbedtls mbedcrypto sqlite3 dl pthread rt util)
