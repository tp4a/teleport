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
rm -rf /etc/rc2.d/S50eom_ts
rm -rf /etc/rc3.d/S50eom_ts
rm -rf /etc/rc4.d/S50eom_ts
rm -rf /etc/rc5.d/S50eom_ts


if [ -f /etc/init.d/teleport ]; then
	service teleport stop
	rm -rf /etc/init.d/teleport
fi
rm -rf /etc/rc2.d/S50teleport
rm -rf /etc/rc3.d/S50teleport
rm -rf /etc/rc4.d/S50teleport
rm -rf /etc/rc5.d/S50teleport


if [ -d /usr/local/eom/teleport ]; then
	rm -rf /usr/local/eom/teleport
fi

echo ""
echo -e "\e[32mUninstallation done.\033[0m"
echo ""
