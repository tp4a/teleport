# -*- coding: utf8 -*-

import os
import platform
import sys

# __all__ = ['BuildContext', 'BITS_32', 'BITS_64', 'TARGET_DEBUG', 'TARGET_RELEASE']

BITS_UNKNOWN = 0
BITS_32 = 32
BITS_64 = 64

TARGET_UNKNOWN = 0
TARGET_DEBUG = 1
TARGET_RELEASE = 2


class BuildContext(object):
    def __init__(self):
        # self.dist_linux = ['ubuntu', 'centos', 'redhat']
        # self.dist_all = self.dist_linux + ['windows', 'macos']
        self.dist_all = ['windows', 'linux', 'macos']

        self.is_py2 = sys.version_info[0] == 2
        self.is_py3 = sys.version_info[0] == 3

        self.target = TARGET_RELEASE
        self.target_path = 'release'

        _py_ver = platform.python_version_tuple()
        self.py_ver = '%s%s' % (_py_ver[0], _py_ver[1])
        self.py_dot_ver = '%s.%s' % (_py_ver[0], _py_ver[1])

        self.bits = BITS_32
        self.bits_path = 'x86'

        _bits = platform.architecture()[0]
        if _bits == '64bit':
            self.bits = BITS_64
            self.bits_path = 'x64'

        _os = platform.system().lower()

        self.dist = ''
        if _os == 'windows':
            self.dist = 'windows'
        elif _os == 'linux':
            self.dist = 'linux'
            # (dist, ver, sys_id) = platform.dist()
            # dist = dist.lower()
            # if dist in self.dist_linux:
            #     self.dist = dist
            # else:
            #     raise RuntimeError('unsupported linux dist: %s' % dist)
        elif _os == 'darwin':
            self.dist = 'macos'

        self.host_os = self.dist
        if self.host_os == 'windows':
            self.host_os_is_win_x64 = 'PROGRAMFILES(X86)' in os.environ

        self.dist_path = ''
        self.make_dist_path()

    def make_dist_path(self):
        self.dist_path = '%s-py%s-%s' % (self.dist, self.py_ver, self.bits_path)

    def set_target(self, target):
        self.target = target
        if target == TARGET_DEBUG or target == 'debug':
            self.target_path = 'debug'
        elif target == TARGET_RELEASE or target == 'release':
            self.target_path = 'release'
        else:
            raise RuntimeError('unknown target mode.')

    def set_bits(self, bits):
        if bits == BITS_32 or bits == 'x86':
            self.bits = BITS_32
            self.bits_path = 'x86'
        elif bits == BITS_64 or bits == 'x64':
            self.bits = BITS_64
            self.bits_path = 'x64'
        else:
            raise RuntimeError('unknown bits.')

        self.make_dist_path()

    def set_dist(self, dist):
        if dist in self.dist_all:
            self.dist = dist
        else:
            raise RuntimeError('unsupported OS: %s' % dist)

        self.make_dist_path()


if __name__ == '__main__':
    pass
