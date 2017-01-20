#!/bin/bash

####################################################################
# EOM Teleport Server Uninstall Script
####################################################################

if [ `id -u` -ne 0 ];then
	echo ""
	echo -e "\e[31mPlease run the uninstaller with ROOT.\033[0m"
	echo ""
	exit 1
fi  


echo ""
echo "Uninstalling EOM Teleport Server..."

if [ -f /etc/init.d/eom_ts ]; then
	service eom_ts stop
	rm -rf /etc/init.d/eom_ts
fi
if [ -f /etc/rc2.d/S50eom_ts ]; then
	rm -rf /etc/rc2.d/S50eom_ts
fi

if [ -f /etc/init.d/teleport ]; then
	service teleport stop
	rm -rf /etc/init.d/teleport
fi
if [ -f /etc/rc2.d/S50teleport ]; then
	rm -rf /etc/rc2.d/S50teleport
fi


if [ -d /usr/local/eom/teleport ]; then
	rm -rf /usr/local/eom/teleport
fi

echo ""
echo -e "\e[32mUninstallation done.\033[0m"
echo ""
