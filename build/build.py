#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt
import json
import os
import platform
import sys

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
BUILDER_PATH = os.path.join(THIS_PATH, 'builder')

sys.path.append(os.path.join(BUILDER_PATH))

try:
    import core.colorconsole as cc
except ImportError:
    print('can not import color console module.')
    sys.exit(1)

import core.utils as utils

try:
    from core.context import *
except ImportError:
    cc.e('can not import core context module.')
    sys.exit(1)

ctx = BuildContext()

if ctx.is_py2:
    _input = raw_input
else:
    _input = input

if ctx.host_os == 'windows':
    try:
        import win32api, win32con
    except:
        cc.e('can not import module `win32api`.')
        sys.exit(1)

options = list()
options_idx = 0


def main():
    cc.set_default(sep='', end='\n')

    action = None
    argv = sys.argv[1:]
    if len(argv) >= 1:
        for i in range(len(argv)):
            if 'debug' == argv[i]:
                ctx.set_target(TARGET_DEBUG)
            elif 'release' == argv[i]:
                ctx.set_target(TARGET_RELEASE)
            # elif 'x86' == argv[i]:
            #     ctx.set_bits(BITS_32)
            # elif 'x64' == argv[i]:
            #     ctx.set_bits(BITS_64)
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
    cc.v('remove compiler out path...')
    utils.remove(os.path.join(ROOT_PATH, 'out'))
    utils.remove(os.path.join(ROOT_PATH, 'waf_build'))
    utils.remove(os.path.join(ROOT_PATH, '.lock-waf_linux_build'))


def do_opt(opt):
    cc.v(opt)
    # PY_EXEC = cfg[opt['bits']]['PY_EXEC']

    arg = ''
    # if 'pysbase' == opt['name']:
    #     script = 'build-pysbase.py'

    if 'ver' == opt['name']:
        script = 'build-version.py'

    elif 'pysrt' == opt['name']:
        script = 'build-pysrt.py'

    elif 'external' == opt['name']:
        script = 'build-external.py'

    # elif 'agent-runtime' == opt['name']:
    #     script = 'build-agent.py'
    #     arg = '%s %s runtime' % (ctx.target_path, opt['bits'])
    elif 'server' == opt['name']:
        script = 'build-server.py'
        arg = '%s %s server' % (ctx.target_path, opt['bits'])

    elif 'installer' == opt['name']:
        script = 'build-installer.py'
        # arg = 'installer'
        arg = '%s %s installer' % (ctx.dist, opt['bits'])

    elif 'installer-ubuntu' == opt['name']:
        script = 'build-installer.py'
        arg = '%s %s installer' % ('ubuntu', opt['bits'])

    elif 'assist-exe' == opt['name']:
        script = 'build-assist.py'
        arg = '%s %s exe' % (ctx.target_path, opt['bits'])
    elif 'assist-rdp' == opt['name']:
        script = 'build-assist.py'
        arg = '%s rdp' % (opt['bits'])
    elif 'assist-installer' == opt['name']:
        script = 'build-assist.py'
        arg = '%s %s installer' % (ctx.dist, opt['bits'])

    # elif 'server' == opt['name']:
    #     script = 'build-server.py'
    #     # arg = 'installer'
    #     # arg = '%s %s' % (ctx.dist, ctx.bits_path)
    #     arg = '%s' % (opt['bits'])

    else:
        cc.e('unknown option: ', opt['name'])
        return

    # cmd = '%s "%s" %s' % (PY_EXEC, arg, ex_arg)
    cmd = '"%s" -B "%s/%s" %s' % (utils.cfg.py_exec, BUILDER_PATH, script, arg)
    cc.i(cmd)
    cc.v('')
    os.system(cmd)


def select_option_by_name(name):
    global options

    for o in range(len(options)):
        if options[o] is None:
            continue

        if name == options[o]['name']:
            return options[o]

    return None


def select_option_by_id(id):
    global options

    for o in range(len(options)):
        if options[o] is None:
            continue
        if options[o]['id'] == id:
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
    global options, options_idx, cfg

    # options = [{'name': 'config', 'disp': 'Configure'}]

    options = list()
    options_idx = 0
    # add_option(None, 'config', 'Configure')

    if ctx.host_os == 'windows':
        add_option('x86', 'ver', 'Update version setting')
        add_option('x86', 'pysrt', 'Make Python-Runtime for python%s-x86' % (utils.cfg.py_ver_str))
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
        add_option('x64', 'pysrt', 'Make Python-Runtime for python%s-x64' % (utils.cfg.py_ver_str))
        add_option('x64', 'external', 'Build external for Teleport-Server')
        add_split()
        add_option('x64', 'server', 'Teleport Server [%s]' % ctx.target_path)
        add_split()
        add_option('x64', 'installer', 'Teleport Installer for %s' % ctx.host_os)


def get_input(msg, log_func=cc.w):
    log_func(msg, end=' ')
    try:
        return _input()
    except EOFError:
        return ''


def show_logo():
    cc.v('[]=======================================================[]')
    cc.o((cc.CR_VERBOSE, ' | '), (cc.CR_INFO, 'Teleport Projects Builder'), (cc.CR_VERBOSE, '                                  |'))
    cc.v(' | auth: apexliu@eomsoft.net                             |')
    cc.v('[]=======================================================[]')


def show_menu():
    # cc.v(cfg)
    cc.v('')
    cc.v('=========================================================')
    for o in range(len(options)):
        if options[o] is None:
            cc.v('  -------------------------------------------------------')
            continue
        cc.o((cc.CR_NORMAL, '  ['), (cc.CR_INFO, '%2d' % options[o]['id']), (cc.CR_NORMAL, '] ', options[o]['disp']))

    cc.v('  -------------------------------------------------------')
    cc.o((cc.CR_NORMAL, '  ['), (cc.CR_INFO, ' C'), (cc.CR_NORMAL, '] clean build and dist env.'))

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
