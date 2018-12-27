# -*- coding: utf-8 -*-

from core import colorconsole as cc
from core import utils
from core.ver import *
from core.context import *
from core.env import env

ctx = BuildContext()


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
        cc.i('build tp_assist...')
        sln_file = os.path.join(env.root_path, 'client', 'tp_assist_win', 'tp_assist.vs2017.sln')
        out_file = os.path.join(env.root_path, 'out', 'client', ctx.bits_path, ctx.target_path, 'tp_assist.exe')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.msvc_build(sln_file, 'tp_assist', ctx.target_path, ctx.bits_path, False)
        utils.ensure_file_exists(out_file)

    # def build_rdp(self):
    #     cc.n('build tp_rdp...')
    #     sln_file = os.path.join(ROOT_PATH, 'client', 'tp_rdp', 'tp_rdp.2015.sln')
    #     out_file = os.path.join(ROOT_PATH, 'out', 'client', ctx.bits_path, ctx.target_path, 'tp_rdp.exe')
    #     if os.path.exists(out_file):
    #         utils.remove(out_file)
    #     utils.msvc_build(sln_file, 'tp_rdp', ctx.target_path, ctx.bits_path, False)
    #     utils.ensure_file_exists(out_file)

    def build_installer(self):
        cc.i('build assist installer...')

        name = 'teleport-assist-{}-{}'.format(ctx.dist, VER_TP_ASSIST)

        out_path = os.path.join(env.root_path, 'out', 'installer')
        utils.makedirs(out_path)

        out_file = os.path.join(out_path, '{}.exe'.format(name))
        utils.remove(out_file)

        self._build_installer()

        utils.ensure_file_exists(out_file)


    @staticmethod
    def _build_installer():
        tmp_path = os.path.join(env.root_path, 'dist', 'client', 'windows', 'assist')
        tmp_app_path = os.path.join(tmp_path, 'apps')
        tmp_cfg_path = os.path.join(tmp_app_path, 'cfg')

        if os.path.exists(tmp_app_path):
            utils.remove(tmp_app_path)

        utils.makedirs(tmp_app_path)
        utils.makedirs(tmp_cfg_path)

        utils.copy_file(os.path.join(env.root_path, 'out', 'client', ctx.bits_path, ctx.target_path), tmp_app_path, 'tp_assist.exe')
        utils.copy_file(os.path.join(env.root_path, 'client', 'cfg'), tmp_cfg_path, ('tp-assist.windows.json', 'tp-assist.json'))

        utils.copy_file(os.path.join(env.root_path, 'client', 'cfg'), tmp_cfg_path, 'cacert.cer')
        utils.copy_file(os.path.join(env.root_path, 'client', 'cfg'), tmp_cfg_path, 'localhost.key')
        utils.copy_file(os.path.join(env.root_path, 'client', 'cfg'), tmp_cfg_path, 'localhost.pem')

        utils.copy_ex(os.path.join(env.root_path, 'client', 'tp_assist_win'), tmp_app_path, 'site')

        utils.makedirs(os.path.join(tmp_app_path, 'tools', 'putty'))
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'putty'), os.path.join(tmp_app_path, 'tools', 'putty'), 'putty.exe')

        utils.makedirs(os.path.join(tmp_app_path, 'tools', 'winscp'))
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'winscp'), os.path.join(tmp_app_path, 'tools', 'winscp'), 'WinSCP.exe')
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'winscp'), os.path.join(tmp_app_path, 'tools', 'winscp'), 'license.txt')

        utils.makedirs(os.path.join(tmp_app_path, 'tools', 'tprdp'))
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'tprdp-client.exe')
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'tprdp-replay.exe')
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'libeay32.dll')
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'ssleay32.dll')
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'msvcr120.dll')

        utils.copy_file(os.path.join(env.root_path, 'client', 'tools'), os.path.join(tmp_app_path, 'tools'), 'securecrt-telnet.vbs')

        utils.nsis_build(os.path.join(env.root_path, 'dist', 'client', 'windows', 'assist', 'installer.nsi'))


class BuilderMacOS(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_exe(self):
        cc.i('build tp_assist...')

        configuration = ctx.target_path.capitalize()

        proj_file = os.path.join(env.root_path, 'client', 'tp_assist_macos', 'TP-Assist.xcodeproj')
        out_file = os.path.join(env.root_path, 'client', 'tp_assist_macos', 'build', configuration, 'TP-Assist.app')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.xcode_build(proj_file, 'TP-Assist', configuration, False)
        utils.ensure_file_exists(os.path.join(out_file, 'Contents', 'Info.plist'))

    def build_installer(self):
        cc.i('make tp_assist dmg file...')

        json_file = os.path.join(env.root_path, 'dist', 'client', 'macos', 'dmg.json')
        dmg_file = os.path.join(env.root_path, 'out', 'client', 'macos', 'teleport-assist-macos-{}.dmg'.format(VER_TP_ASSIST))
        if os.path.exists(dmg_file):
            utils.remove(dmg_file)

        utils.make_dmg(json_file, dmg_file)
        utils.ensure_file_exists(dmg_file)

    @staticmethod
    def _build_installer():
        return
        # tmp_path = os.path.join(env.root_path, 'dist', 'client', 'windows', 'assist')
        # tmp_app_path = os.path.join(tmp_path, 'apps')
        # tmp_cfg_path = os.path.join(tmp_app_path, 'cfg')
        #
        # if os.path.exists(tmp_app_path):
        #     utils.remove(tmp_app_path)
        #
        # utils.makedirs(tmp_app_path)
        # utils.makedirs(tmp_cfg_path)
        #
        # utils.copy_file(os.path.join(env.root_path, 'out', 'client', ctx.bits_path, ctx.target_path), tmp_app_path, 'tp_assist.exe')
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tp_assist_win', 'cfg'), tmp_cfg_path, ('tp-assist.default.json', 'tp-assist.json'))
        #
        # utils.copy_ex(os.path.join(env.root_path, 'client', 'tp_assist_win'), tmp_app_path, 'site')
        #
        # utils.makedirs(os.path.join(tmp_app_path, 'tools', 'putty'))
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'putty'), os.path.join(tmp_app_path, 'tools', 'putty'), 'putty.exe')
        #
        # utils.makedirs(os.path.join(tmp_app_path, 'tools', 'winscp'))
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'winscp'), os.path.join(tmp_app_path, 'tools', 'winscp'), 'WinSCP.exe')
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'winscp'), os.path.join(tmp_app_path, 'tools', 'winscp'), 'license.txt')
        #
        # utils.makedirs(os.path.join(tmp_app_path, 'tools', 'tprdp'))
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'tprdp-client.exe')
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'tprdp-replay.exe')
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'libeay32.dll')
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'ssleay32.dll')
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'msvcr120.dll')
        #
        # utils.copy_file(os.path.join(env.root_path, 'client', 'tools'), os.path.join(tmp_app_path, 'tools'), 'securecrt-telnet.vbs')
        #
        # utils.nsis_build(os.path.join(env.root_path, 'dist', 'client', 'windows', 'assist', 'installer.nsi'))


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
    elif dist == 'macos':
        builder = BuilderMacOS()
    elif dist == 'linux':
        builder = BuilderLinux()
    else:
        raise RuntimeError('unsupported platform.')

    ctx.set_dist(dist)
    return builder


def main():
    if not env.init():
        return

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
