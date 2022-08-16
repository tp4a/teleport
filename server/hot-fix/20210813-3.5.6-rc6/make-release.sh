#!/bin/sh

set -e

HOTFIX=tp-hotfix-20210813-3.5.6-rc6

PATH_ROOT=$(cd "$(dirname "$0")/../../.."; pwd)
PATH_THIS=$(cd "$(dirname "$0")"; pwd)
PATH_DATA=${PATH_THIS}/${HOTFIX}
PATH_FILES=${PATH_DATA}/files
NOW_DT_STR=`date "+%Y-%m-%d %H:%M:%S"`

echo $PATH_ROOT
echo $PATH_THIS
echo $PATH_DATA
echo $PATH_FILES

if [ -d "${PATH_FILES}" ]; then
    rm -rf "${PATH_FILES}"
fi

mkdir -p "${PATH_FILES}/controller"
mkdir -p "${PATH_FILES}/model"

cp "${PATH_ROOT}/server/www/teleport/webroot/app/controller/auth.py" "${PATH_FILES}/controller/."
cp "${PATH_ROOT}/server/www/teleport/webroot/app/model/user.py" "${PATH_FILES}/model/."

# cp "${PATH_THIS}/tp-hotfix.sh" "${PATH_DATA}/."

# 将脚本文件第4行替换掉
CREATE_DT=`date "+%Y-%m-%d %H:%M:%S"`
# CREATE_DT=date
echo ${CREATE_DT}

#echo "sed -i '4s/.*/CREATE_DT\=${CREATE_DT}/' '${PATH_DATA}/tp-hotfix.sh'"
sed -i ".bak" "4s/.*/CREATE_DT='${CREATE_DT}'/" "${PATH_DATA}/tp-hotfix.sh"
#sed -i "'4s/.*/CREATE_DT=${CREATE_DT}/'" "${PATH_DATA}/tp-hotfix.sh"

rm -rf "${PATH_DATA}/tp-hotfix.sh.bak"
chmod +x "${PATH_DATA}/tp-hotfix.sh"

tar zcvf "${HOTFIX}.tar.gz" ./${HOTFIX}
