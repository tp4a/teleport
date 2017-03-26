#!/bin/bash

if [ `id -u` -ne 0 ];then
	echo ""
	echo -e "\e[31mPlease run setup with ROOT.\033[0m"
	echo ""
	exit 1
fi  


PATH_ROOT=$(cd "$(dirname "$0")"; pwd)
PATH_TARGET=/usr/local/eom

"${PATH_ROOT}/data/bin/tp_web" --py "${PATH_ROOT}/script/main.py"
exit 0


if [ ! -d "${PATH_TARGET}" ]; then
	mkdir -p "${PATH_TARGET}"
fi

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

sleep 1
echo ""
echo "Installing EOM Teleport Server..."

cd "${PATH_TARGET}"
tar -zxvf "${PATH_ROOT}/data/teleport.tar.gz" >/dev/null
cd "${PATH_ROOT}"

if [ ! -d "${PATH_TARGET}/teleport/etc" ]; then
	cp -r "${PATH_TARGET}/teleport/tmp/etc" "${PATH_TARGET}/teleport/etc"
else
	if [ ! -f "${PATH_TARGET}/teleport/etc/web.ini" ]; then
		cp "${PATH_TARGET}/teleport/tmp/etc/web.ini" "${PATH_TARGET}/teleport/etc/web.ini"
	fi
	if [ ! -f "${PATH_TARGET}/teleport/etc/core.ini" ]; then
		cp "${PATH_TARGET}/teleport/tmp/etc/core.ini" "${PATH_TARGET}/teleport/etc/core.ini"
	fi
fi

if [ ! -d "${PATH_TARGET}/teleport/data" ]; then
	cp -r "${PATH_TARGET}/teleport/tmp/data" "${PATH_TARGET}/teleport/data"
fi

chmod +x "${PATH_TARGET}/teleport/bin/tp_core"
chmod +x "${PATH_TARGET}/teleport/bin/tp_web"

echo "Generate daemon startup script..."

cp "${PATH_ROOT}/data/start.sh" "${PATH_TARGET}/teleport/."
chmod +x "${PATH_TARGET}/teleport/start.sh"
cp "${PATH_ROOT}/data/stop.sh" "${PATH_TARGET}/teleport/."
chmod +x "${PATH_TARGET}/teleport/stop.sh"
cp "${PATH_ROOT}/data/status.sh" "${PATH_TARGET}/teleport/."
chmod +x "${PATH_TARGET}/teleport/status.sh"

cp "${PATH_ROOT}/data/daemon" /etc/init.d/teleport
chmod +x /etc/init.d/teleport

ln -s /etc/init.d/teleport /etc/rc2.d/S50teleport
ln -s /etc/init.d/teleport /etc/rc3.d/S50teleport
ln -s /etc/init.d/teleport /etc/rc4.d/S50teleport
ln -s /etc/init.d/teleport /etc/rc5.d/S50teleport

# Upgrade database...
"${PATH_TARGET}/teleport/bin/tp_web" --py "${PATH_TARGET}/teleport/www/teleport/app/eom_upgrade.py"

echo ""
echo "Start teleport server..."
echo ""
service teleport start
echo ""
sleep 1
echo "Check teleport server status..."
echo ""
service teleport status
echo ""


echo ""
echo -e "\e[32mInstallation done.\033[0m"
echo ""
