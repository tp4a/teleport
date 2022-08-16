#!/bin/sh
set -e

CREATE_DT='_PLACE_HOLDER_'
REQUEST_VER_NO='_PLACE_HOLDER_'
REQUEST_VER_STAT='_PLACE_HOLDER_'

if [ `id -u` -ne 0 ];then
	echo ""
	echo "Error: please run hotfix as root."
	echo ""
	exit 1
fi

PATH_ROOT=$(cd "$(dirname "$0")"; pwd)
PATH_FILES=${PATH_ROOT}/files

DAEMON_FILE=/etc/init.d/teleport
NOW_DT=`date "+%Y%m%d.%H%M%S"`

echo '============================================='
echo "  Teleport Hotfix for ${REQUEST_VER_NO}-${REQUEST_VER_STAT}"
echo "  create at ${CREATE_DT}"
echo '============================================='

inst_path=`cat ${DAEMON_FILE} | grep "DAEMON_PATH=" | awk -F= '{print $2}'`
if [ 'x-$inst_path' == 'x-' ]; then
    echo "Error: teleport installation not detected on your system."
    echo "hotfix not patch, exit."
    exit 1
else
    echo "teleport installation detected at ${inst_path}"
fi

ver_file=${inst_path}/www/teleport/webroot/app/app_ver.py

ver_no=`cat ${ver_file} | grep "TP_SERVER_VER = " | awk -F= '{print $2}' | awk -F\" '{print $2}'`
ver_stat=`cat ${ver_file} | grep "TP_STATE_VER = " | awk -F= '{print $2}' | awk -F\" '{print $2}'`

miss_match_ver=0
if [ "${ver_no}" != "${REQUEST_VER_NO}" ]; then
    miss_match_ver=1
fi
if [ "${ver_stat}" != "${REQUEST_VER_STAT}" ]; then
    miss_match_ver=1
fi

if [ ${miss_match_ver} != 0 ]; then
    echo "Error: this hotfix works for ${REQUEST_VER_NO}-${REQUEST_VER_STAT}, but your installation is ${ver_no} ${ver_stat}"
    echo 'hotfix not patch, exit.'
    exit 1
fi

miss_match_file=0
if [ ! -f "${inst_path}/www/teleport/webroot/app/controller/audit.py" ]; then
    miss_match_file=1
fi
if [ ! -f "${inst_path}/www/teleport/webroot/app/controller/auth.py" ]; then
    miss_match_file=1
fi
if [ ${miss_match_ver} != 0 ]; then
    echo "Error: target file to be fix not found."
    echo 'hotfix not patch, exit.'
    exit 1
fi

echo "patching..."

echo "  backup ${inst_path}/www/teleport/webroot/app/controller/audit.py"
mv "${inst_path}/www/teleport/webroot/app/controller/audit.py" "${inst_path}/www/teleport/webroot/app/controller/audit.py.hotfix.${NOW_DT}"
echo "  backup ${inst_path}/www/teleport/webroot/app/controller/auth.py"
mv "${inst_path}/www/teleport/webroot/app/controller/auth.py" "${inst_path}/www/teleport/webroot/app/controller/auth.py.hotfix.${NOW_DT}"

echo "  fix ${inst_path}/www/teleport/webroot/app/controller/audit.py"
cp "${PATH_FILES}/controller/audit.py" "${inst_path}/www/teleport/webroot/app/controller/audit.py"
echo "  fix ${inst_path}/www/teleport/webroot/app/controller/auth.py"
cp "${PATH_FILES}/controller/auth.py" "${inst_path}/www/teleport/webroot/app/controller/auth.py"

echo ''
echo "done, now please restart teleport web server by following command:"
echo ''
echo 'sudo /etc/init.d/teleport restart web'
echo ''