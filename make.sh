#!/bin/bash

PATH_ROOT=$(cd "$(dirname "$0")"; pwd)
CFG_FILE=config.json

function build_win
{
	# find pyexec from json file
	pyexec=$(grep -P '"pyexec":' ./${CFG_FILE} | grep -Po '(?<="pyexec":)([[:space:]]*)"(.*)"')
	# remove left "
	pyexec=${pyexec#*\"}
	# remove right "
	pyexec=${pyexec%\"*}

	# make sure configuration item exists.
	if [ "${pyexec}-x" = "-x" ] ; then
		on_error "\`pyexec\` not set, please check your \`${CFG_FILE}\`"
	fi

	pyexec=$(cygpath -u ${pyexec})

	if [ ! -f "${pyexec}" ] ; then
		pyexec=$(cygpath -m ${pyexec})
		on_error "Sorry, need Python 3.7 or above (x86 version) to\nbuild Teleport on Windows Platform.\n\nPython interpreter not exists: ${pyexec}"
	fi

	# check version and architecture of python.
	# version should >= 3.7
	$("${pyexec}" -c "import platform;import sys;pyv=platform.python_version_tuple();ret=0 if int(pyv[0])>=3 and int(pyv[1])>=7 else 1;sys.exit(ret)")
	if [ $? -ne 0 ]; then
		on_error "Sorry, need x86 version of Python 3.7 or above."
	fi
	# and must be x86 version.
	$("${pyexec}" -c "import platform;import sys;ret=0 if platform.architecture()[0]=='32bit' else 1;sys.exit(ret)")
	if [ $? -ne 0 ]; then
		on_error "Sorry, need x86 version of Python 3.7 or above."
	fi

	${pyexec} -B "${PATH_ROOT}/build/build.py" $@
}

function build_linux
{
	if [ `id -u` -eq 0 ]; then
		on_error "Do not build as root."
	fi

	if [ ! -f "/etc/centos-release" ] ; then
		on_error "Sorry, build script works on CentOS 7 only."
	fi

	X=$(yum list installed | grep "libffi-devel")
	if [ "$X-x" = "-x" ] ; then
		on_error "Need libffi-devel to build Python, try:\r\n    sudo yum install libffi-devel"
	fi

	X=$(yum list installed | grep "zlib-devel")
	if [ "$X-x" = "-x" ] ; then
		on_error "Need zlib-devel to build Python, try:\r\n    sudo yum install zlib-devel"
	fi

	PYEXEC=${PATH_ROOT}/external/linux/release/bin/python3.7
	PYSTATIC=${PATH_ROOT}/external/linux/release/lib/libpython3.7m.a

	if [ ! -f "${PYSTATIC}" ] ; then
		echo "python static not found, now build it..."
		"${PATH_ROOT}/build/build-py-static.sh"

		if [ ! -f "${PYSTATIC}" ] ; then
			on_error "can not build python static."
		fi
	fi


	${PYEXEC} -B "${PATH_ROOT}/build/build.py" $@
}

function build_macos
{
	python3 -B "${PATH_ROOT}/build/build.py" $@
}

function on_error()
{
	echo -e "\033[01m\033[31m"
	echo "==================[ !! ERROR !! ]=================="
	echo ""
	echo -e $1
	echo ""
	echo "==================================================="
	echo -e "\033[0m"
	exit 1
}

function on_error_begin()
{
	echo ""
	echo -e "\033[01m\033[31mERROR: ${1}\033[0m"
	echo ""
}
function on_error_end()
{
	exit 1
}


##############################################
# main
##############################################

if [ ! -f "./${CFG_FILE}" ] ; then
	on_error_begin "\`${CFG_FILE}\` does not exists."
	echo "please copy \`${CFG_FILE}.in\` into \`${CFG_FILE}\`"
	echo "and modify it to fit your condition, then try again."
	on_error_end
fi

export TP_BUILD_SYSTEM="start"

SYSTEM=`uname -s`
SYSTEM=${SYSTEM:0:4}	# cut first 4 char.
SYSTEM=${SYSTEM^^}		# upper case
if [ $SYSTEM = "LINU" ] ; then
	build_linux $@
elif [ $SYSTEM = "DARW" ] ; then   
	build_macos $@
elif [ $SYSTEM == "MSYS" ] ; then
	build_win $@
else 
	on_error_begin "Unsupported platform."
	echo "To build teleport on Windows, please read document at:"
	echo "    https://docs.tp4a.com/develop/windows"
	on_error_end
fi
