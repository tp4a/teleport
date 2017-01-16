#!/bin/env python3
# -*- coding: utf-8 -*-

import codecs
import shutil
import time
from core import colorconsole as cc
from core import makepyo
from core import utils
from core.context import *

ctx = BuildContext()

ROOT_PATH = utils.cfg.ROOT_PATH


class BuilderBase:
    def __init__(self):
        self.out_dir = ''

    def build_server(self):
        pass


class BuilderWin(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_server(self):
        cc.n('build web server ...')
        sln_file = os.path.join(ROOT_PATH, 'server', 'tp_web', 'src', 'tp_web.vs2015.sln')
        out_file = os.path.join(ROOT_PATH, 'out', 'server', ctx.bits_path, ctx.target_path, 'tp_web.exe')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.msvc_build(sln_file, 'tp_web', ctx.target_path, ctx.bits_path, False)
        utils.ensure_file_exists(out_file)

        cc.n('build core server ...')
        sln_file = os.path.join(ROOT_PATH, 'server', 'tp_core', 'core', 'tp_core.vs2015.sln')
        out_file = os.path.join(ROOT_PATH, 'out', 'server', ctx.bits_path, ctx.target_path, 'tp_core.exe')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.msvc_build(sln_file, 'tp_core', ctx.target_path, ctx.bits_path, False)
        utils.ensure_file_exists(out_file)

        cc.n('build SSH protocol ...')
        sln_file = os.path.join(ROOT_PATH, 'server', 'tp_core', 'protocol', 'ssh', 'tpssh.vs2015.sln')
        out_file = os.path.join(ROOT_PATH, 'out', 'server', ctx.bits_path, ctx.target_path, 'tpssh.dll')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.msvc_build(sln_file, 'tpssh', ctx.target_path, ctx.bits_path, False)
        utils.ensure_file_exists(out_file)

        #
        # s = os.path.join(ROOT_PATH, 'out', 'console', ctx.bits_path, ctx.target_path, 'console.exe')
        # t = os.path.join(ROOT_PATH, 'out', 'eom_agent', ctx.target_path, ctx.dist_path, 'eom_agent.com')
        # shutil.copy(s, t)
        # utils.ensure_file_exists(t)


class BuilderLinux(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_server(self):
        cc.n('build tp_web...')

        ###################
        # out_path = os.path.join(ROOT_PATH, 'out', 'eom_ts', ctx.target_path, ctx.dist_path)
        out_path = os.path.join(ROOT_PATH, 'out', 'server', ctx.bits_path, 'bin')
        out_file = os.path.join(out_path, 'tp_web')

        if os.path.exists(out_file):
            utils.remove(out_file)

        utils.makedirs(out_path)

        utils.cmake(os.path.join(ROOT_PATH, 'server', 'cmake-build'), ctx.target_path, False)
        utils.strip(out_file)


        # wscript_file = os.path.join(ROOT_PATH, 'wscript')
        # utils.waf_build(wscript_file, ctx.target_path, False)

        # chk_file = os.path.join(ROOT_PATH, 'waf_build', ctx.target_path, 'eom_ts')
        # utils.ensure_file_exists(chk_file)
        # os.chmod(chk_file, 0o777)

        # shutil.copy(chk_file, out_file)
        utils.ensure_file_exists(out_file)



def gen_builder(dist):
    if dist == 'windows':
        builder = BuilderWin()
    elif dist == 'linux':
        builder = BuilderLinux()
    else:
        raise RuntimeError('unsupported platform.')

    ctx.set_dist(dist)
    return builder


def main():
    builder = None

    argv = sys.argv[1:]

    for i in range(len(argv)):
        if 'debug' == argv[i]:
            ctx.set_target(TARGET_DEBUG)
        elif 'x86' == argv[i]:
            ctx.set_bits(BITS_32)
        elif 'x64' == argv[i]:
            ctx.set_bits(BITS_64)
        elif argv[i] in ctx.dist_all:
            builder = gen_builder(argv[i])

    if builder is None:
        builder = gen_builder(ctx.host_os)

    if 'server' in argv:
        builder.build_server()

    # if 'app' in argv:
    #     builder.build_app()

    # if 'installer' in argv:
    #     builder.build_installer()

    # if 'runtime' in argv:
    #     builder.build_runtime()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        cc.e(e.__str__())
    except:
        cc.f('got exception.')
