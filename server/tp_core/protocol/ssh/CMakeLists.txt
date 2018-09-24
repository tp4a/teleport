cmake_minimum_required(VERSION 3.5)
project(tpssh)

#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC")
#set(CMAKE_CFLAGS "${CMAKE_CFLAGS} -fPIC")
set(CMAKE_CXX_FLAGS "-fPIC")
set(CMAKE_C_FLAGS "-fPIC")

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${Project_SOURCE_DIR}/../out/server/x64/bin")


aux_source_directory(. DIR_SSH_SRCS)
aux_source_directory(../../common DIR_SSH_SRCS)
aux_source_directory(../../../../common/libex/src DIR_SSH_SRCS)
aux_source_directory(../../../../external/jsoncpp/src/lib_json DIR_SSH_SRCS)

list(REMOVE_ITEM DIR_SSH_SRCS "./dllmain.cpp")
list(REMOVE_ITEM DIR_SSH_SRCS "./stdafx.cpp")


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


add_library(tpssh SHARED ${DIR_SSH_SRCS})

IF (CMAKE_SYSTEM_NAME MATCHES "Linux")
#	target_link_libraries(tpssh ssh ssh_threads ssl crypto mbedx509 mbedtls mbedcrypto dl pthread rt util)
	target_link_libraries(tpssh ssh ssl crypto mbedx509 mbedtls mbedcrypto dl pthread rt util)
ELSEIF (CMAKE_SYSTEM_NAME MATCHES "Darwin")
	target_link_libraries(tpssh ssh ssh_threads ssl crypto mbedx509 mbedtls mbedcrypto dl pthread util)
ENDIF (CMAKE_SYSTEM_NAME MATCHES "Linux")

