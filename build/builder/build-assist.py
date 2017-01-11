#!/bin/env python3
# -*- coding: utf-8 -*-

from core import colorconsole as cc
from core import utils
from core.context import *
from core.ver import *

ctx = BuildContext()

ROOT_PATH = utils.cfg.ROOT_PATH


class BuilderBase:
    def __init__(self):
        self.out_dir = ''

    def build_exe(self):
        pass

    def build_rdp(self):
        pass

    def build_installer(self):
        pass


class BuilderWin(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_exe(self):
        cc.n('build tp_assist...')
        sln_file = os.path.join(ROOT_PATH, 'tp_assist', 'tp_assist.vs2015.sln')
        out_file = os.path.join(ROOT_PATH, 'out', 'tp_assist', ctx.bits_path, ctx.target_path, 'tp_assist.exe')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.msvc_build(sln_file, 'tp_assist', ctx.target_path, ctx.bits_path, False)
        utils.ensure_file_exists(out_file)

    # def build_rdp(self):
    #     cc.n('build tp_rdp...')
    #     sln_file = os.path.join(ROOT_PATH, 'tp_rdp', 'tp_rdp.2015.sln')
    #     out_file = os.path.join(ROOT_PATH, 'out', 'tp_rdp', ctx.bits_path, ctx.target_path, 'tp_rdp.exe')
    #     if os.path.exists(out_file):
    #         utils.remove(out_file)
    #     utils.msvc_build(sln_file, 'tp_rdp', ctx.target_path, ctx.bits_path, False)
    #     utils.ensure_file_exists(out_file)

    def build_installer(self):
        cc.n('build assist package for website...')

        name = 'teleport-assist-windows-{}-{}'.format(ctx.bits_path, VER_TELEPORT_ASSIST)
        utils.remove(os.path.join(ROOT_PATH, 'dist', '{}.zip'.format(name)))
        self._build_installer(name)

        last_ver = 'teleport-assist-last-win.zip'
        if os.path.exists(os.path.join(ROOT_PATH, 'dist', last_ver)):
            utils.remove(os.path.join(ROOT_PATH, 'dist', last_ver))

        utils.copy_file(os.path.join(ROOT_PATH, 'dist'), os.path.join(ROOT_PATH, 'dist'), ('{}.zip'.format(name), last_ver))

        # cc.n('build assist package for backend...')
        # name = 'teleport-assist-last-win'
        # utils.remove(os.path.join(ROOT_PATH, 'dist', '{}.zip'.format(name)))
        # self._build_installer(name)

        # utils.copy_file(os.path.join(ROOT_PATH, 'dist'), os.path.join(ROOT_PATH, 'web', 'site', 'teleport', 'static', 'download'), 'teleport-assist-win.zip')

    @staticmethod
    def _build_installer(name):
        base_path = os.path.join(ROOT_PATH, 'out', 'tp_assist')
        base_tmp = os.path.join(base_path, '_tmp_')
        tmp_path = os.path.join(base_tmp, name)

        if os.path.exists(base_tmp):
            utils.remove(base_tmp)

        utils.makedirs(tmp_path)

        utils.copy_file(os.path.join(ROOT_PATH, 'out', 'tp_assist', ctx.bits_path, ctx.target_path), tmp_path, 'tp_assist.exe')
        utils.copy_file(os.path.join(ROOT_PATH, 'tp_assist'), tmp_path, ('ssh_client.orig.ini', 'ssh_client.ini'))
        utils.copy_file(os.path.join(ROOT_PATH, 'tp_assist'), tmp_path, ('scp_client.orig.ini', 'scp_client.ini'))
        utils.copy_file(os.path.join(ROOT_PATH, 'tp_assist'), tmp_path, ('telnet_client.orig.ini', 'telnet_client.ini'))

        utils.copy_ex(os.path.join(ROOT_PATH, 'tp_assist'), tmp_path, 'site')

        utils.makedirs(os.path.join(tmp_path, 'tools', 'tprdp'))
        utils.makedirs(os.path.join(tmp_path, 'tools', 'putty'))
        utils.makedirs(os.path.join(tmp_path, 'tools', 'winscp'))
        # utils.copy_file(os.path.join(ROOT_PATH, 'out', 'tp_rdp', ctx.bits_path, ctx.target_path), os.path.join(tmp_path, 'tools', 'tprdp'), 'tp_rdp.exe')
        utils.copy_file(os.path.join(ROOT_PATH, 'tools', 'tprdp'), os.path.join(tmp_path, 'tools', 'tprdp'), 'tprdp-client.exe')
        utils.copy_file(os.path.join(ROOT_PATH, 'tools', 'tprdp'), os.path.join(tmp_path, 'tools', 'tprdp'), 'tprdp-replay.exe')
        utils.copy_file(os.path.join(ROOT_PATH, 'tools', 'putty'), os.path.join(tmp_path, 'tools', 'putty'), 'putty.exe')
        utils.copy_file(os.path.join(ROOT_PATH, 'tools', 'winscp'), os.path.join(tmp_path, 'tools', 'winscp'), 'WinSCP.exe')
        utils.copy_file(os.path.join(ROOT_PATH, 'tools', 'winscp'), os.path.join(tmp_path, 'tools', 'winscp'), 'license.txt')
        utils.copy_file(os.path.join(ROOT_PATH, 'tools'), os.path.join(tmp_path, 'tools'), 'securecrt-telnet.vbs')

        # utils.makedirs(os.path.join(tmp_path, 'data'))
        # utils.copy_file(os.path.join(ROOT_PATH, 'tp_assist'), os.path.join(tmp_path, 'data'), 'ssl.cert')

        out_file = os.path.join(ROOT_PATH, 'dist', '{}.zip'.format(name))
        utils.make_zip(base_tmp, out_file)


class BuilderLinux(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_exe(self):
        cc.e('not support linux.')

    # def build_rdp(self):
    #     cc.e('not support linux.')

    def build_installer(self):
        cc.e('not support linux.')


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

    if 'exe' in argv:
        builder.build_exe()
    # elif 'rdp' in argv:
    #     builder.build_rdp()
    elif 'installer' in argv:
        builder.build_installer()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        cc.e(e.__str__())
    except:
        cc.f('got exception.')
