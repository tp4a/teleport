# -*- coding: utf-8 -*-

"""
检测运行环境和相对定位文件路径
目录结构说明：
  PATH_APP_ROOT
    |- app
    |- res
    |- static
    \- view
"""

import os
import platform
import sys

__all__ = ['PATH_APP_ROOT', 'PATH_LOG', 'PATH_CONF', 'PATH_DATA']

PATH_LOG = ''
PATH_CONF = ''
PATH_DATA = ''

# 将Python安装的扩展库移除，避免开发调试与正式发布所依赖的库文件不一致导致发布的版本无法运行
x = []
for p in sys.path:
    if p.find('site-packages') != -1 or p.find('dist-packages') != -1:
        x.append(p)
for p in x:
    sys.path.remove(p)

is_dev_mode = False
path_of_this_file = os.path.abspath(os.path.dirname(__file__))

PATH_APP_ROOT = os.path.abspath(os.path.join(path_of_this_file, '..'))

# 根据源代码目录形式，检查是否是开发版本
if os.path.exists(os.path.join(PATH_APP_ROOT, '..', '..', 'share', 'etc')):
    is_dev_mode = True

# 检查操作系统，目前仅支持Win和Linux
PLATFORM = platform.system().lower()
if PLATFORM not in ['windows', 'linux', 'darwin']:
    print('TELEPORT WEB Server does not support `{}` platform yet.'.format(PLATFORM))
    sys.exit(1)

BITS = 'x64'
if '32bit' == platform.architecture()[0]:
    BITS = 'x86'

# 引入必要的扩展库
_ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-common'))
if _ext_path not in sys.path:
    sys.path.append(_ext_path)

_ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-{}'.format(PLATFORM), BITS))
if _ext_path not in sys.path:
    sys.path.append(_ext_path)

# 确定一些路径
if is_dev_mode:
    # 开发调试模式
    # _ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-common'))
    # if _ext_path not in sys.path:
    #     sys.path.append(_ext_path)
    #
    # _ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-{}'.format(PLATFORM), BITS))
    # if _ext_path not in sys.path:
    #     sys.path.append(_ext_path)
    #
    PATH_LOG = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'share', 'log'))
    PATH_CONF = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'share', 'etc'))
    PATH_DATA = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'share', 'data'))

else:
    # _ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-common'))
    # if _ext_path not in sys.path:
    #     sys.path.append(_ext_path)
    #
    # _ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-{}'.format(PLATFORM), BITS))
    # if _ext_path not in sys.path:
    #     sys.path.append(_ext_path)
    #
    PATH_LOG = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'log'))
    PATH_CONF = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'etc'))
    PATH_DATA = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'data'))

    if PLATFORM == 'linux':
        # 根据Linux目录规范建议设置各个必要的路径
        PATH_LOG = '/var/log/teleport'
        PATH_CONF = '/etc/teleport'
        PATH_DATA = '/var/lib/teleport'
