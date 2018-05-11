cmake_minimum_required(VERSION 3.5)
project(tpcore)

#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${Project_SOURCE_DIR}/../out/server/x64/bin")


ADD_DEFINITIONS(
        -DMG_ENABLE_THREADS
        -DMG_DISABLE_HTTP_DIGEST_AUTH
        -DMG_DISABLE_MQTT
        -DMG_DISABLE_SSI
#        -DMG_DISABLE_FILESYSTEM
        -DHAVE_CONFIG_H
#        -DCS_COMMON_MD5_H_
        -DCS_DISABLE_MD5
)

aux_source_directory(. DIR_SRCS)
aux_source_directory(../../../common/libex/src DIR_SRCS)
aux_source_directory(../../../external/mongoose DIR_SRCS)
aux_source_directory(../../../external/jsoncpp/src/lib_json DIR_SRCS)


#list(REMOVE_ITEM DIR_SRCS "./src/ts_win_service_helper.cpp")

include_directories(
        ../../../common/libex/include
        ../../../common/teleport
        ../../../external/mongoose
        ../../../external/jsoncpp/include
)

IF (CMAKE_SYSTEM_NAME MATCHES "Linux")
        set(CMAKE_EXE_LINKER_FLAGS "-export-dynamic")
        include_directories(
                ../../../external/linux/release/include
        )
        link_directories(../../../external/linux/release/lib)
ELSEIF (CMAKE_SYSTEM_NAME MATCHES "Darwin")
        include_directories(
                ../../../external/macos/release/include
        )
        link_directories(../../../external/macos/release/lib)
ENDIF (CMAKE_SYSTEM_NAME MATCHES "Linux")


add_executable(tp_core ${DIR_SRCS})

IF (CMAKE_SYSTEM_NAME MATCHES "Linux")
        target_link_libraries(tp_core ssl crypto mbedx509 mbedtls mbedcrypto dl pthread rt util)
ELSEIF (CMAKE_SYSTEM_NAME MATCHES "Darwin")
        target_link_libraries(tp_core ssl crypto mbedx509 mbedtls mbedcrypto dl pthread util)
ENDIF (CMAKE_SYSTEM_NAME MATCHES "Linux")
