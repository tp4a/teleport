# -*- coding: utf-8 -*-

"""
运行环境检测
"""

import os
import sys
import platform
from eom_common.common.const import *
from eom_common.eomcore.logger import log
from . import utils


class EomEnvBase(object):
    def __init__(self):
        self._os_type = OS_UNKNOWN
        self._linux_dist = OS_LINUX_UNKNOWN

        self._os_name = 'unknown'
        self._os_id = 0     # 0 = unknown, 1 = windows, 200=Linux, 201=Ubuntu...

        # # 脚本是由Python运行，还是由我们自己的主程序运行
        self._is_self_exec = False
        #
        # 是否运行于管理员身份
        self._is_run_as_root = False

        #
        self._app_path = ''
        self._conf_path = ''
        self._log_path = ''
        self._data_path = ''

        self._check()

    # def init(self, app_path):
    #     self._app_path = app_path
    #     self._conf_path = os.path.join(self._app_path, 'conf')
    #     # self._log_path = os.path.join(self._app_path, 'log')

    def _check(self):
        # 判断操作系统
        if 'win32' == sys.platform:
            self._os_type = OS_WIN32
            self._os_name = 'windows'
            self._os_id = 1
        elif 'linux' == sys.platform:
            self._os_type = OS_LINUX
            self._os_name = 'linux'
            self._os_id = 200
        elif 'darwin' == sys.platform:
            self._os_type = OS_MAC
            self._os_name = 'macos'
            self._os_id = 300
        else:
            log.e('[ERROR] Can not detect system type.\n')
            return

        # 如果是Linux，判断其发行版
        if OS_LINUX == self._os_type:
            (dist, ver, sys_id) = platform.dist()
            dist = dist.lower()
            if 'centos' == dist:
                self._linux_dist = OS_LINUX_CENTOS
                self._os_id = 201
            elif 'ubuntu' == dist:
                self._linux_dist = OS_LINUX_UBUNTU
                self._os_id = 202
            elif 'debian' == dist:
                self._linux_dist = OS_LINUX_DEBIAN
                self._os_id = 203
            elif 'redhat' == dist:
                self._linux_dist = OS_LINUX_REDHAT
                self._os_id = 204
            elif 'gentoo' == dist:
                self._linux_dist = OS_LINUX_GENTOO
                self._os_id = 205
            else:
                log.w('[WARNING] Can not detect linux distribution, try default settings.\n')
                self._linux_dist = OS_LINUX_DEFAULT

        # 判断宿主程序是python还是我们自己的主程序
        exec_names = os.path.split(sys.executable)
        # print(sys.executable)
        if 'python3' == exec_names[1] or 'python.exe' == exec_names[1]:
            self._is_self_exec = False
        else:
            self._is_self_exec = True

        # 判断是否是以root身份运行
        if self._os_type == OS_WIN32:
            # 在windows平台，没有直接的方式，可以尝试在特定目录下创建文件，然后根据成功与否来判断
            tmp_file = '%s\\System32\\6A5D77DDFCFB40CEB26A8444EEC5757E_%s.tmp' % (os.getenv('SystemRoot'), utils.gen_random(4))
            try:
                f = open(tmp_file, 'w')
                f.close()
                os.remove(tmp_file)
                self._is_run_as_root = True
            except IOError:
                pass
        else:
            if 0 == os.getuid():
                self._is_run_as_root = True

                # # 确定路径
                # tmp = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                # if tmp[-4:] == '.zip':
                #     self._app_path = os.path.abspath(os.path.join(tmp, '..', '..'))
                # else:
                #     self._app_path = os.path.abspath(os.path.join(tmp, '..'))

                # self._conf_path = os.path.join(self._app_path, 'conf')

    def is_self_exec(self):
        return self._is_self_exec

    def is_root(self):
        return self._is_run_as_root

    def get_os_type(self):
        return self._os_type

    def get_os_name(self):
        return self._os_name

    def get_os_id(self):
        return self._os_id

    def is_windows(self):
        return True if self._os_type == OS_WIN32 else False

    def is_macos(self):
        return True if self._os_type == OS_MAC else False

    def is_linux(self):
        return True if self._os_type == OS_LINUX else False

    def get_linux_dist(self):
        return self._linux_dist

    def is_ubuntu(self):
        return True if self._linux_dist == OS_LINUX_UBUNTU else False

    def is_centos(self):
        return True if self._linux_dist == OS_LINUX_CENTOS else False

    def is_debian(self):
        return True if self._linux_dist == OS_LINUX_DEBIAN else False

    def is_redhat(self):
        return True if self._linux_dist == OS_LINUX_REDHAT else False

    def is_gentoo(self):
        return True if self._linux_dist == OS_LINUX_GENTOO else False

    # def get_log_file_path(self):
    #     if self.is_windows():
    #         path = os.path.join(self.app_path, 'log', 'eom-agent')
    #     elif self.is_macos():
    #         path = '/var/log/eom-agent'
    #     else:
    #         path = '/var/log/eom-agent'
    #
    #     return path

    def log_path(self):
        return self._log_path

    @property
    def app_path(self):
        """
        返回的路径是app脚本文件所在路径的上一级路径，可用于合成log、conf等路径。

        :rtype : str
        """
        return self._app_path

    @property
    def conf_path(self):
        return self._conf_path

    @property
    def data_path(self):
        return self._data_path

#
#
# # eom_env = EomEnv()
# # del EomEnv
# eom_env = None
#
#
# def get_env():
#     """
#
#     :rtype : EomEnv
#     """
#     global eom_env
#     if eom_env is None:
#         eom_env = EomEnv()
#         # del EomEnv
#     return eom_env
