# -*- coding: utf-8 -*-

# 检测运行环境和相对定位文件路径

import os
import platform
import sys

__all__ = ['PATH_APP_ROOT', 'PATH_LOG', 'PATH_CONF', 'PATH_DATA', 'DEV_MODE']

PATH_LOG = ''
PATH_CONF = ''
PATH_DATA = ''
DEV_MODE = False

# 将Python安装的扩展库移除，避免开发调试与正式发布所依赖的库文件不一致导致发布出去的版本无法运行
x = []
for p in sys.path:
    if p.find('site-packages') != -1 or p.find('dist-packages') != -1:
        x.append(p)
for p in x:
    sys.path.remove(p)

PLATFORM = platform.system().lower()
if PLATFORM not in ['windows', 'linux']:
    sys.exit(1)

BITS = 'x64'
if '32bit' == platform.architecture()[0]:
    BITS = 'x86'

path_of_this_file = os.path.abspath(os.path.dirname(__file__))
PATH_APP_ROOT = os.path.abspath(os.path.join(path_of_this_file, '..'))

# 如果没有打包，可能是开发版本，也可能是发布源代码版本，需要进一步判断
if os.path.exists(os.path.join(PATH_APP_ROOT, '..', '..', 'share', 'etc')):
    DEV_MODE = True
elif os.path.exists(os.path.join(PATH_APP_ROOT, '..', '..', 'etc')):
    DEV_MODE = False
else:
    print('invalid installation.\n')
    sys.exit(1)


if DEV_MODE:
    # 开发调试模式
    _ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-common'))
    if _ext_path not in sys.path:
        sys.path.append(_ext_path)

    _ext_path = os.path.abspath(
        os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-{}'.format(PLATFORM), BITS))
    if _ext_path not in sys.path:
        sys.path.append(_ext_path)

    PATH_LOG = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'share', 'log'))
    PATH_CONF = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'share', 'etc'))
    PATH_DATA = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'share', 'data'))

else:
    _ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-common'))
    if _ext_path not in sys.path:
        sys.path.append(_ext_path)

    _ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-{}'.format(PLATFORM), BITS))
    if _ext_path not in sys.path:
        sys.path.append(_ext_path)

    PATH_LOG = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'log'))
    PATH_CONF = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'etc'))
    PATH_DATA = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'data'))
