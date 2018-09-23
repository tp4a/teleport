#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import py_compile
import shutil
import sys
import time
import platform

from . import colorconsole as cc
from . import utils

rm_file_every_level = ['.pyc', '.pyo']

PY_VER = platform.python_version_tuple()
cpython_mid_name = 'cpython-{}{}'.format(PY_VER[0], PY_VER[1])


def make(tmp_path):
    cc.v('Remove all old .pyc/.pyo files...')
    clean_folder(tmp_path)
    time.sleep(0.5)
    cc.v('Compile all .py into .pyo...')
    compile_files(tmp_path)
    time.sleep(0.5)
    cc.v('Remove all .py files...')
    fix_pyo(tmp_path)
    time.sleep(0.5)
    cc.v('Remove all `__pycache__` folders...')
    remove_cache(tmp_path)


def clean_folder(path):
    for parent, dir_list, file_list in os.walk(path):
        for d in dir_list:
            clean_folder(os.path.join(parent, d))

        for filename in file_list:
            _, ext = os.path.splitext(filename)
            if ext in rm_file_every_level:
                os.remove(os.path.join(parent, filename))


def remove_cache(path):
    for parent, dir_list, file_list in os.walk(path):
        for d in dir_list:
            d = d.lower()
            if d == '__pycache__':
                utils.remove(os.path.join(parent, d))
                continue
            remove_cache(os.path.join(parent, d))


def compile_files(path):
    for parent, dir_list, file_list in os.walk(path):
        for d in dir_list:
            compile_files(os.path.join(parent, d))

        for filename in file_list:
            n, ext = os.path.splitext(filename)
            # fileNameSplitList = filename.split(".")
            # ext = fileNameSplitList[len(fileNameSplitList) - 1].lower()
            if ext == '.py':
                py_compile.compile(os.path.join(parent, filename), os.path.join(parent, n)+'.pyc', optimize=2)
                # py_compile.compile(os.path.join(parent, filename), optimize=2)


def fix_pyo(path):
    for parent, dir_list, file_list in os.walk(path):
        for d in dir_list:
            fix_pyo(os.path.join(parent, d))

        for filename in file_list:
            _, ext = os.path.splitext(filename)
            if ext.lower() == '.py':
                os.remove(os.path.join(parent, filename))

            # names = filename.split(".")
            # ext = names[len(names) - 1].lower()
            # if ext.lower() == '.py':
            #     os.remove(os.path.join(parent, filename))
            # elif ext == 'pyo':
            #     cpython = names[len(names) - 2].lower()
            #     if cpython == cpython_mid_name:
            #         del names[len(names) - 2]
            #     else:
            #         continue
            #     t_name = os.path.abspath(os.path.join(parent, '..', '.'.join(names)))
            #     f_name = os.path.join(parent, filename)
            #     shutil.copy(f_name, t_name)


if __name__ == '__main__':
    make(sys.argv[1])
