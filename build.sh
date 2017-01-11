#!/bin/bash

PATH_ROOT=$(cd "$(dirname "$0")"; pwd)
PYEXEC=${PATH_ROOT}/external/linux/release/bin/python3.4
PYSTATIC=${PATH_ROOT}/external/linux/release/lib/libpython3.4m.a

function on_error()
{
	echo -e "\033[01m\033[31m"
	echo "==================[ !! ERROR !! ]=================="
	echo -e $1
	echo "==================================================="
	echo -e "\033[0m"
	exit 1
}

if [ ! -f "${PYSTATIC}" ]; then
	echo "python static not found, now build it..."
	"${PATH_ROOT}/build/build-py-static.sh"

	if [ ! -f "${PYSTATIC}" ]; then
		on_error "can not build python static."
	fi
fi


${PYEXEC} -B "${PATH_ROOT}/build/build.py" $@
