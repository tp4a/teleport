#!/bin/sh

set -e

REQUEST_VER_NO='3.2.2'

HOTFIX_CREATE_DAY=`date "+%Y%m%d"`
HOTFIX=tp-hotfix-${HOTFIX_CREATE_DAY}-${REQUEST_VER_NO}

PATH_ROOT=$(cd "$(dirname "$0")/../../.."; pwd)
PATH_THIS=$(cd "$(dirname "$0")"; pwd)
PATH_BASE=${PATH_THIS}/base
PATH_DATA=${PATH_THIS}/${HOTFIX}
PATH_FILES=${PATH_DATA}/files
NOW_DT_STR=`date "+%Y-%m-%d %H:%M:%S"`

echo "PATH_ROOT: ${PATH_ROOT}"
echo "PATH_THIS: ${PATH_THIS}"
echo "PATH_BASE: ${PATH_BASE}"
echo "PATH_DATA: ${PATH_DATA}"
echo "PATH_FILES: ${PATH_FILES}"

if [ -d "${PATH_DATA}" ]; then
    rm -rf "${PATH_DATA}"
fi

mkdir -p "${PATH_FILES}/controller"

cp "${PATH_BASE}/README.txt" "${PATH_DATA}/."
cp "${PATH_BASE}/tp-hotfix.sh" "${PATH_DATA}/."

cp "${PATH_ROOT}/server/www/teleport/webroot/app/controller/audit.py" "${PATH_FILES}/controller/."
cp "${PATH_ROOT}/server/www/teleport/webroot/app/controller/auth.py" "${PATH_FILES}/controller/."

# 替换脚本文件中的参数部分（第4/5行）
sed -i ".bak" "4s/.*/CREATE_DT='${NOW_DT_STR}'/" "${PATH_DATA}/tp-hotfix.sh"
sed -i ".bak" "5s/.*/REQUEST_VER_NO='${REQUEST_VER_NO}'/" "${PATH_DATA}/tp-hotfix.sh"

rm -rf "${PATH_DATA}/tp-hotfix.sh.bak"
chmod +x "${PATH_DATA}/tp-hotfix.sh"

tar zcvf "${HOTFIX}.tar.gz" ./${HOTFIX}
