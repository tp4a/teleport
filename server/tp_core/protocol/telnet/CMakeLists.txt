cmake_minimum_required(VERSION 3.5)
project(tptelnet)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC")

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${Project_SOURCE_DIR}/../out/server/x64/bin")


aux_source_directory(. DIR_TELNET_SRCS)
aux_source_directory(../../common DIR_TELNET_SRCS)
aux_source_directory(../../../../common/libex/src DIR_TELNET_SRCS)
aux_source_directory(../../../../external/jsoncpp/src/lib_json DIR_TELNET_SRCS)

list(REMOVE_ITEM DIR_TELNET_SRCS "./dllmain.cpp")
list(REMOVE_ITEM DIR_TELNET_SRCS "./stdafx.cpp")


include_directories(
        ../../../../common/libex/include
		../../../../common/teleport
		../../../../external/jsoncpp/include
)

IF (CMAKE_SYSTEM_NAME MATCHES "Linux")
	include_directories(
	        ../../../../external/linux/release/include
	)
	link_directories(../../../../external/linux/release/lib)
ELSEIF (CMAKE_SYSTEM_NAME MATCHES "Darwin")
	include_directories(
	        ../../../../external/macos/release/include
	)
	link_directories(../../../../external/macos/release/lib)
ENDIF (CMAKE_SYSTEM_NAME MATCHES "Linux")


add_library(tptelnet SHARED ${DIR_TELNET_SRCS})

IF (CMAKE_SYSTEM_NAME MATCHES "Linux")
	#target_link_libraries(tptelnet uv mbedx509 mbedtls mbedcrypto dl pthread rt util)
	target_link_libraries(tptelnet uv dl pthread rt util)
ELSEIF (CMAKE_SYSTEM_NAME MATCHES "Darwin")
	#target_link_libraries(tptelnet uv mbedx509 mbedtls mbedcrypto dl pthread util)
	target_link_libraries(tptelnet uv dl pthread util)
ENDIF (CMAKE_SYSTEM_NAME MATCHES "Linux")

