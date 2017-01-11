#!/bin/bash

################################################################
# Basic settings.
################################################################
VER_PYTHON="3.4.4"
VER_PYTHON_SHORT="3.4"
VER_OPENSSL="1.0.2h"
VER_SQLITE="3160200"
VER_PSUTIL="4.2.0"
VER_PYTHON_LIB="${VER_PYTHON_SHORT}m"

################################################################
# DO NOT TOUCH FOLLOWING CODE
################################################################

FILE_PYTHON_STATIC_LIB="libpython${VER_PYTHON_LIB}.a"

PATH_ROOT=$(cd "$(dirname "$0")"/..; pwd)
PATH_EXT=${PATH_ROOT}/external
PATH_DOWNLOAD=${PATH_EXT}/_download_
PATH_TMP=${PATH_EXT}/linux/tmp
PATH_FIX=${PATH_EXT}/fix-external
PATH_RELEASE=${PATH_EXT}/linux/release


PY_PATH_SRC=${PATH_TMP}/Python-${VER_PYTHON}
#PATH_SRC=${PATH_TMP}/${VER_PYTHON}
#PATH_INST=${PATH_RELEASE}/python
OSSL_PATH_SRC=${PATH_TMP}/openssl-${VER_OPENSSL}

function on_error()
{
	echo -e "\033[01m\033[31m"
	echo "==================[ !! ERROR !! ]=================="
	echo -e $1
	echo "==================================================="
	echo -e "\033[0m"
	exit 1
}

function setp_build_git()
{
	# su -s
	# yum install zlib-devel expat-devel libcurl-devel
	# make prefix=/usr/local
	# make prefix=/usr/local install
	echo 'skip build git now.'
}

function dlfile()
{
	echo -n "Downloading $1 ..."
	if [ ! -f "$4/$3" ]; then
		echo ""
		# curl --insecure https://www.python.org/ftp/python/3.4.3/${VER_PYTHON}.tgz -o "${PATH_PYTHON}/${VER_PYTHON}.tgz"
		echo wget $2$3 -O "$4/$3"
		wget --no-check-certificate $2$3 -O "$4/$3"

		if [ ! -f "$4/$3" ]; then
			on_error "Can not download $1: $3"
		fi
	else
		echo " already exists, skip."
	fi
}

function step_download_files()
{
	echo "download necessary source tarball ..."

	if [ ! -d "${PATH_DOWNLOAD}" ]; then
		mkdir -p "${PATH_DOWNLOAD}"
		if [ ! -d "${PATH_DOWNLOAD}" ]; then
			on_error "Can not create folder for download files."
		fi
	fi

	dlfile "python source tarball"  "https://www.python.org/ftp/python/${VER_PYTHON}/" "Python-${VER_PYTHON}.tgz" ${PATH_DOWNLOAD}
	dlfile "openssl source tarball" "https://www.openssl.org/source/" "openssl-${VER_OPENSSL}.tar.gz" ${PATH_DOWNLOAD}
	dlfile "sqlite source tarball"  "http://sqlite.org/2017/" "sqlite-autoconf-${VER_SQLITE}.tar.gz" ${PATH_DOWNLOAD}

	# dlfile "psutil source tarball"  "https://pypi.python.org/packages/source/p/psutil/" "psutil-${VER_PSUTIL}.tar.gz" ${PATH_DOWNLOAD}
	# https://pypi.python.org/pypi?:action=display&name=psutil#downloads

	# echo -n "Downloading psutil source tarball ..."
	# if [ ! -f "${PATH_DOWNLOAD}/psutil-${VER_PSUTIL}.tar.gz" ]; then
	# 	echo ""
	# 	echo "Because pypi.python.org limit, can not auto-download psutil, please visit following url:"
	# 	echo "  https://pypi.python.org/pypi?:action=display&name=psutil#downloads"
	# 	echo "and download psutil-${VER_PSUTIL}.tar.gz and put it into folder:"
	# 	echo "  ${PATH_DOWNLOAD}"
	# 	echo "after download, try again."
	# 	on_error "psutil source tarball not exists."
	# else
	# 	echo " already exists, skip."
	# fi
}


function step_prepare_source()
{
	echo "prepare source ..."

	if [ ! -d "${PATH_TMP}" ]; then
		mkdir -p "${PATH_TMP}"
		if [ ! -d "${PATH_TMP}" ]; then
			on_error "Can not create folder for tmp files."
		fi
	fi

	if [ ! -d "${PATH_TMP}/Python-${VER_PYTHON}" ]; then
		tar -zxvf "${PATH_DOWNLOAD}/Python-${VER_PYTHON}.tgz" -C "${PATH_TMP}"
	fi

	if [ ! -d "${PATH_TMP}/openssl-${VER_OPENSSL}" ]; then
		tar -zxvf "${PATH_DOWNLOAD}/openssl-${VER_OPENSSL}.tar.gz" -C "${PATH_TMP}"
	fi


	if [ ! -d "${PATH_TMP}/sqlite-autoconf-${VER_SQLITE}" ]; then
		tar -zxvf "${PATH_DOWNLOAD}/sqlite-autoconf-${VER_SQLITE}.tar.gz" -C "${PATH_TMP}"
	fi

	# if [ ! -d "${PATH_TMP}/psutil-${VER_PSUTIL}" ]; then
	# 	tar -zxvf "${PATH_DOWNLOAD}/psutil-${VER_PSUTIL}.tar.gz" -C "${PATH_TMP}"
	# fi

	# cp -r "${PATH_TMP}/psutil-${VER_PSUTIL}/psutil" "${PATH_TMP}/Python-${VER_PYTHON}/Modules/." 
	cp -r "${PATH_TMP}/sqlite-autoconf-${VER_SQLITE}" "${PATH_TMP}/Python-${VER_PYTHON}/Modules/_sqlite/sqlite3" 
	cp -r "${PATH_FIX}/Python-${VER_PYTHON}" "${PATH_TMP}" 
}

function step_build_openssl()
{
	echo -n "build openssl static library ..."

	if [ ! -f "${PATH_RELEASE}/lib/libssl.a" ] || [ ! -f "${PATH_RELEASE}/lib/libcrypto.a" ]; then
		echo ""
		cd "${OSSL_PATH_SRC}"
		./config --prefix=${PATH_RELEASE} --openssldir=${PATH_RELEASE}/openssl no-zlib no-shared
		make
		make install
		cd "${PATH_ROOT}"

		if [ ! -f "${PATH_RELEASE}/lib/libssl.a" ] || [ ! -f "${PATH_RELEASE}/lib/libcrypto.a" ]; then
			on_error "Build openssl failed."
		fi

	else
		echo " already exists, skip."
	fi
}


function step_build_python()
{
	echo -n "build python static library ..."

	if [ ! -f "${PATH_RELEASE}/lib/${FILE_PYTHON_STATIC_LIB}" ]; then
		cd "${PY_PATH_SRC}"
		cp "${PY_PATH_SRC}/Modules/Setup.dist" "${PY_PATH_SRC}/Modules/Setup"
		LDFLAGS=-lrt ./configure --disable-shared  --prefix=${PATH_RELEASE}
		make
		make altinstall
		cd "${PATH_ROOT}"

		if [ ! -f "${PATH_RELEASE}/lib/${FILE_PYTHON_STATIC_LIB}" ]; then
			on_error "Build python failed."
		fi

	else
		echo " already exists, skip."
	fi
}

function step_finalize()
{
	# copy psutil *.py for release.
	echo "finalize ..."

	if [ ! -d "${PATH_RELEASE}/lib/python${VER_PYTHON_SHORT}/site-packages" ]; then
		on_error "something goes wrong."
	fi


	# cp -r "${PATH_FIX}/psutil-${VER_PSUTIL}/psutil" "${PATH_RELEASE}/lib/python${VER_PYTHON_SHORT}/site-packages/psutil" 
}


step_download_files
step_prepare_source
step_build_openssl
step_build_python
step_finalize
