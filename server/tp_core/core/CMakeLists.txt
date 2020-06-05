cmake_minimum_required(VERSION 3.5)

MESSAGE(STATUS "=======================================================")
MESSAGE(STATUS "               tp_core")
MESSAGE(STATUS "=======================================================")
include(../../../CMakeCfg.txt)

ADD_DEFINITIONS(
    -DMG_ENABLE_THREADS
    -DMG_DISABLE_HTTP_DIGEST_AUTH
    -DMG_DISABLE_MQTT
    -DMG_DISABLE_SSI
    # -DMG_DISABLE_FILESYSTEM
    -DHAVE_CONFIG_H
    # -DCS_COMMON_MD5_H_
    -DCS_DISABLE_MD5
)

aux_source_directory(. DIR_SRCS)
aux_source_directory(../../../common/libex/src DIR_SRCS)
aux_source_directory(../../../external/mongoose DIR_SRCS)
aux_source_directory(../../../external/jsoncpp/src/lib_json DIR_SRCS)

include_directories(
        ../../../common/libex/include
        ../../../common/teleport
        ../../../external/mongoose
        ../../../external/jsoncpp/include
)

if (OS_LINUX)
    set(CMAKE_EXE_LINKER_FLAGS "-export-dynamic")
    include_directories(
        ${TP_EXTERNAL_RELEASE_DIR}/include
    )
    link_directories(${TP_EXTERNAL_RELEASE_DIR}/lib)
elseif (OS_MACOS)
    include_directories(
        /usr/local/opt/openssl/include
        ${TP_EXTERNAL_RELEASE_DIR}/include
    )
    link_directories(
        /usr/local/opt/openssl/lib
        ${TP_EXTERNAL_RELEASE_DIR}/lib
    )
endif ()

add_executable(tp_core ${DIR_SRCS})

if (OS_LINUX)
    target_link_libraries(tp_core ssl crypto mbedx509 mbedtls mbedcrypto dl pthread rt util)
elseif (OS_MACOS)
    target_link_libraries(tp_core ssl crypto mbedx509 mbedtls mbedcrypto dl pthread util)
endif ()
