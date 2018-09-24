# -*- coding: utf-8 -*-

import getopt
import json
import os
import platform
import sys

from builder.core.env import env
import builder.core.colorconsole as cc
import builder.core.utils as utils
from builder.core.context import *

if env.is_py2:
    _input = raw_input
else:
    _input = input

options = list()
options_idx = 0
ctx = BuildContext()


def main():
    cc.set_default(sep='', end='\n')

    if not env.init(warn_miss_tool=True):
        return

    action = None
    argv = sys.argv[1:]
    if len(argv) >= 1:
        for i in range(len(argv)):
            if 'debug' == argv[i]:
                ctx.set_target(TARGET_DEBUG)
            elif 'release' == argv[i]:
                ctx.set_target(TARGET_RELEASE)
            elif argv[i] in ctx.dist_all:
                ctx.set_dist(argv[i])
            else:
                action = argv[i]

    make_options()

    if action is not None:
        cc.v(action)
        opt = select_option_by_name(action)
        if opt is None:
            cc.e('unknown config: ', action)
            return

        do_opt(opt)
        return

    show_logo()
    while True:
        x = show_menu()
        if x == 'q':
            break

        if x == 'c':
            clean_all()
            continue
        elif x == 'a':
            clean_everything()
            continue

        try:
            x = int(x)
        except:
            cc.e('invalid input.')
            continue

        opt = select_option_by_id(int(x))
        if 'config' == opt['name']:
            if make_config():
                make_options()
            continue

        if opt is None:
            cc.e('unknown selection: ', x)
            continue

        do_opt(opt)

        cc.w('\ntask finished, press Enter to continue or Q to quit...', end='')
        try:
            x = _input()
        except EOFError:
            x = 'q'
        if x == 'q':
            break


def clean_all():
    # cc.e('sorry, clean not implemented yet.')
    utils.remove(os.path.join(env.root_path, 'out'))


def clean_everything():
    utils.remove(os.path.join(env.root_path, 'out'))
    utils.remove(os.path.join(env.root_path, 'external', 'jsoncpp'))
    utils.remove(os.path.join(env.root_path, 'external', 'libuv'))
    utils.remove(os.path.join(env.root_path, 'external', 'mbedtls'))
    utils.remove(os.path.join(env.root_path, 'external', 'mongoose'))
    utils.remove(os.path.join(env.root_path, 'external', 'openssl'))
    utils.remove(os.path.join(env.root_path, 'external', 'python'))
    utils.remove(os.path.join(env.root_path, 'external', 'libssh-win-static', 'lib'))
    utils.remove(os.path.join(env.root_path, 'external', 'libssh-win-static', 'src'))
    utils.remove(os.path.join(env.root_path, 'external', 'linux', 'tmp'))
    utils.remove(os.path.join(env.root_path, 'external', 'linux', 'release', 'lib', 'libmbedcrypto.a'))
    utils.remove(os.path.join(env.root_path, 'external', 'linux', 'release', 'lib', 'libmbedtls.a'))
    utils.remove(os.path.join(env.root_path, 'external', 'linux', 'release', 'lib', 'libmbedx509.a'))
    utils.remove(os.path.join(env.root_path, 'external', 'linux', 'release', 'lib', 'libsqlite3.a'))
    utils.remove(os.path.join(env.root_path, 'external', 'linux', 'release', 'lib', 'libssh.a'))
    utils.remove(os.path.join(env.root_path, 'external', 'linux', 'release', 'lib', 'libssh_threads.a'))
    utils.remove(os.path.join(env.root_path, 'external', 'linux', 'release', 'lib', 'libuv.a'))


def do_opt(opt):
    arg = ''

    if 'ver' == opt['name']:
        script = 'build-version.py'

    elif 'pysrt' == opt['name']:
        script = 'build-pysrt.py'

    elif 'external' == opt['name']:
        script = 'build-external.py'
        arg = '%s %s' % (ctx.target_path, opt['bits'])

    elif 'server' == opt['name']:
        script = 'build-server.py'
        arg = '%s %s server' % (ctx.target_path, opt['bits'])

    elif 'installer' == opt['name']:
        script = 'build-installer.py'
        # arg = 'installer'
        arg = '%s %s installer' % (ctx.dist, opt['bits'])

    elif 'assist-exe' == opt['name']:
        script = 'build-assist.py'
        arg = '%s %s exe' % (ctx.target_path, opt['bits'])
    # elif 'assist-rdp' == opt['name']:
    #     script = 'build-assist.py'
    #     arg = '%s rdp' % (opt['bits'])
    elif 'assist-installer' == opt['name']:
        script = 'build-assist.py'
        arg = '%s %s installer' % (ctx.dist, opt['bits'])

    else:
        cc.e('unknown option: ', opt['name'])
        return

    # cmd = '"%s" -B "%s" %s' % (utils.cfg.py_exec, os.path.join(BUILDER_PATH, script), arg)
    cmd = '%s -B %s %s' % (env.py_exec, os.path.join(env.builder_path, script), arg)
    os.system(cmd)


def select_option_by_name(name):
    global options

    for o in range(len(options)):
        if options[o] is None:
            continue

        if name == options[o]['name']:
            return options[o]

    return None


def select_option_by_id(_id):
    global options

    for o in range(len(options)):
        if options[o] is None:
            continue
        if options[o]['id'] == _id:
            return options[o]
    return None


def add_option(bits, name, disp):
    global options, options_idx
    options_idx += 1
    # if bits is not None:
    #     disp = '[%s] %s' % (bits, disp)
    options.append({'id': options_idx, 'name': name, 'disp': disp, 'bits': bits})


def add_split():
    global options
    options.append(None)


def make_options():
    # global options, options_idx
    #
    # options = list()
    # options_idx = 0

    if ctx.host_os in ['windows', 'macos']:
        add_option('x86', 'ver', 'Update version setting')
        add_option('x86', 'pysrt', 'Make Python-Runtime for python%s-x86' % env.py_ver_str)
        add_option('x64', 'external', 'Build external dependency')
        add_split()
        add_option('x86', 'assist-exe', 'Assist Execute [%s]' % ctx.target_path)
        # add_option('x86', 'assist-rdp', 'Teleport RDP [%s]' % ctx.target_path)
        add_option('x86', 'assist-installer', 'Assist Installer')
        add_split()
        add_option('x86', 'server', 'Teleport Server [%s]' % ctx.target_path)
        add_split()
        add_option('x86', 'installer', 'Teleport Installer for %s' % ctx.host_os)
    else:
        add_option('x64', 'ver', 'Update version setting')
        add_option('x64', 'pysrt', 'Make Python-Runtime for python%s-x64' % env.py_ver_str)
        add_option('x64', 'external', 'Build external dependency')
        add_split()
        add_option('x64', 'server', 'Build server app [%s]' % ctx.target_path)
        add_split()
        add_option('x64', 'installer', 'Make server installer for %s' % ctx.host_os)


def get_input(msg, log_func=cc.w):
    log_func(msg, end=' ')
    try:
        return _input()
    except EOFError:
        return ''


def show_logo():
    cc.v('[]=======================================================[]')
    cc.o((cc.CR_VERBOSE, ' | '), (cc.CR_INFO, 'Teleport Projects Builder'), (cc.CR_VERBOSE, '                             |'))
    cc.v(' | auth: apex.liu@qq.com                                 |')
    cc.v('[]=======================================================[]')


def show_menu():
    cc.v('')
    cc.v('=========================================================')
    for o in range(len(options)):
        if options[o] is None:
            cc.v('  -------------------------------------------------------')
            continue
        cc.o((cc.CR_NORMAL, '  ['), (cc.CR_INFO, '%2d' % options[o]['id']), (cc.CR_NORMAL, '] ', options[o]['disp']))

    cc.v('  -------------------------------------------------------')
    cc.o((cc.CR_NORMAL, '  ['), (cc.CR_INFO, ' C'), (cc.CR_NORMAL, '] clean build and dist.'))
    cc.o((cc.CR_NORMAL, '  ['), (cc.CR_INFO, ' A'), (cc.CR_NORMAL, '] clean everything.'))

    cc.v('  -------------------------------------------------------')
    cc.o((cc.CR_NORMAL, '  ['), (cc.CR_INFO, ' Q'), (cc.CR_NORMAL, '] exit'))

    cc.w('\nselect action: ', end='')
    try:
        x = _input()
    except EOFError:
        x = 'q'

    cc.n('')
    return x.lower()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        cc.e(e.__str__())
    except:
        cc.f('got exception.')
