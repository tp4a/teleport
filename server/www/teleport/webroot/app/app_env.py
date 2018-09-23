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

__all__ = ['PATH_APP_ROOT', 'PATH_DATA']

PATH_DATA = ''

# 将Python安装的扩展库移除，避免开发调试与正式发布所依赖的库文件不一致导致发布的版本无法运行
x = []
for p in sys.path:
    if p.find('site-packages') != -1 or p.find('dist-packages') != -1:
        x.append(p)
for p in x:
    sys.path.remove(p)

PATH_APP_ROOT = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..'))

# 检查操作系统，目前支持Win/Linux/MacOS
PLATFORM = platform.system().lower()
if PLATFORM not in ['windows', 'linux', 'darwin']:
    print('web server does not support `{}` platform yet.'.format(PLATFORM))
    sys.exit(1)

BITS = 'x64'
if '32bit' == platform.architecture()[0]:
    BITS = 'x86'

# 引入必要的扩展库
_ext_path = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', 'packages', 'packages-{}'.format(PLATFORM), BITS))
if _ext_path not in sys.path:
    sys.path.append(_ext_path)

# 确定一些路径
if os.path.exists(os.path.join(os.path.dirname(sys.executable), 'dev_mode')):
    # 开发调试模式
    PATH_DATA = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'share'))

else:
    PATH_DATA = os.path.abspath(os.path.join(PATH_APP_ROOT, '..', '..', 'data'))
