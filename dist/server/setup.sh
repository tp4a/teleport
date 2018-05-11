#!/bin/bash

if [ `id -u` -ne 0 ];then
	echo ""
	echo -e "\e[31mPlease run setup as root.\033[0m"
	echo ""
	exit 1
fi  


PATH_ROOT=$(cd "$(dirname "$0")"; pwd)
PATH_TARGET=/usr/local/eom

"${PATH_ROOT}/data/bin/tp_web" --py "${PATH_ROOT}/script/main.py"

# echo ""
# echo -e "\e[32mInstallation done.\033[0m"
# echo ""
