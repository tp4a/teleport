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

    def build_assist(self):
        cc.e("this is a pure-virtual function.")

    def build_player(self):
        cc.e("this is a pure-virtual function.")

    def build_rdp(self):
        cc.e("this is a pure-virtual function.")

    def build_installer(self):
        cc.e("this is a pure-virtual function.")


class BuilderWin(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_assist(self):
        cc.i('build tp_assist...')
        sln_file = os.path.join(env.root_path, 'client', 'tp_assist_win', 'tp_assist.vs2022.sln')
        out_file = os.path.join(env.root_path, 'out', 'client', ctx.bits_path, ctx.target_path, 'tp_assist.exe')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.msvc_build(sln_file, 'tp_assist', ctx.target_path, ctx.bits_path, False)
        utils.ensure_file_exists(out_file)

    def build_player(self):
        cc.i('build tp-player...')
        prj_path = os.path.join(env.root_path, 'client', 'tp-player')
        out_file = os.path.join(env.root_path, 'out', 'client', ctx.bits_path, ctx.target_path, 'tp-player.exe')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.qt_build(prj_path, 'tp-player', ctx.bits_path, ctx.target_path)
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

        # assist configuration web page
        utils.copy_ex(os.path.join(env.root_path, 'client', 'tp_assist_win'), tmp_app_path, 'site')

        utils.makedirs(os.path.join(tmp_app_path, 'tools', 'putty'))
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'putty'), os.path.join(tmp_app_path, 'tools', 'putty'), 'putty.exe')

        utils.makedirs(os.path.join(tmp_app_path, 'tools', 'winscp'))
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'winscp'), os.path.join(tmp_app_path, 'tools', 'winscp'), 'WinSCP.exe')
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'winscp'), os.path.join(tmp_app_path, 'tools', 'winscp'), 'license.txt')

        utils.makedirs(os.path.join(tmp_app_path, 'tools', 'tprdp'))
        utils.copy_file(os.path.join(env.root_path, 'client', 'tools', 'tprdp'), os.path.join(tmp_app_path, 'tools', 'tprdp'), 'wfreerdp.exe')

        utils.copy_file(os.path.join(env.root_path, 'client', 'tools'), os.path.join(tmp_app_path, 'tools'), 'securecrt-telnet.vbs')

        # tp-player
        utils.copy_file(os.path.join(env.root_path, 'out', 'client', ctx.bits_path, ctx.target_path), tmp_app_path, 'tp-player.exe')

        # qt-redist
        qt_redist_path = os.path.join(env.root_path, 'client', 'tools', 'qt-redist')

        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-core-file-l1-2-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-core-file-l2-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-core-localization-l1-2-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-core-processthreads-l1-1-1.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-core-synch-l1-2-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-core-timezone-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-convert-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-environment-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-filesystem-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-heap-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-locale-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-math-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-multibyte-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-runtime-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-stdio-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-string-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-time-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'api-ms-win-crt-utility-l1-1-0.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'Qt5Core.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'Qt5Gui.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'Qt5Network.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'Qt5Widgets.dll')
        utils.copy_file(qt_redist_path, tmp_app_path, 'msvcp140_1.dll')
        utils.copy_ex(os.path.join(qt_redist_path, 'platforms'), os.path.join(tmp_app_path, 'platforms'))
        utils.copy_ex(os.path.join(qt_redist_path, 'styles'), os.path.join(tmp_app_path, 'styles'))
        utils.copy_ex(os.path.join(qt_redist_path, 'translations'), os.path.join(tmp_app_path, 'translations'))

        # zlib
        suffix = 'd' if ctx.target_path == 'debug' else ''
        utils.copy_file(os.path.join(env.root_path, 'external', 'zlib', 'build', ctx.target_path), tmp_app_path, 'zlib{}.dll'.format(suffix))

        # openssl
        utils.copy_file(os.path.join(env.root_path, 'external', 'openssl', 'bin'), tmp_app_path, 'libcrypto-1_1.dll')
        utils.copy_file(os.path.join(env.root_path, 'external', 'openssl', 'bin'), tmp_app_path, 'libssl-1_1.dll')

        # final build
        utils.nsis_build(os.path.join(env.root_path, 'dist', 'client', 'windows', 'assist', 'installer.nsi'))


class BuilderMacOS(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_assist(self):
        cc.i('build tp_assist...')

        configuration = ctx.target_path.capitalize()

        proj_file = os.path.join(env.root_path, 'client', 'tp_assist_macos', 'TP-Assist.xcodeproj')
        out_file = os.path.join(env.root_path, 'client', 'tp_assist_macos', 'build', configuration, 'TP-Assist.app')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.xcode_build(proj_file, 'TP-Assist', configuration, False)
        utils.ensure_file_exists(os.path.join(out_file, 'Contents', 'Info.plist'))

    def build_player(self):
        cc.i('build tp-player...')
        prj_path = os.path.join(env.root_path, 'client', 'tp-player')
        out_file = os.path.join(env.root_path, 'out', 'client', ctx.bits_path, ctx.target_path, 'tp-player.app')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.qt_build(prj_path, 'tp-player', ctx.bits_path, ctx.target_path)
        utils.ensure_file_exists(os.path.join(out_file, 'Contents', 'Info.plist'))

        # for deployment
        utils.qt_deploy(out_file)

    def build_installer(self):
        cc.i('make tp_assist dmg file...')

        # copy all files of tp-player.
        configuration = ctx.target_path.capitalize()
        player_path = os.path.join(env.root_path, 'out', 'client', ctx.bits_path, ctx.target_path)
        assist_path = os.path.join(env.root_path, 'client', 'tp_assist_macos', 'build', configuration, 'TP-Assist.app', 'Contents', 'Resources')
        utils.copy_ex(player_path, assist_path, 'tp-player.app')

        json_file = os.path.join(env.root_path, 'dist', 'client', 'macos', 'dmg.json')
        dmg_file = os.path.join(env.root_path, 'out', 'installer', 'teleport-assist-macos-{}.dmg'.format(VER_TP_ASSIST))
        if os.path.exists(dmg_file):
            utils.remove(dmg_file)

        utils.make_dmg(json_file, dmg_file)
        utils.ensure_file_exists(dmg_file)


class BuilderLinux(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_assist(self):
        # cc.e('not support linux.')
        cc.n('build tp_assist...')

        out_path = os.path.join(env.root_path, 'out', 'client', 'linux', 'bin')
        out_files = list()
        out_files.append(os.path.join(out_path, 'tp_assist'))

        for f in out_files:
            if os.path.exists(f):
                utils.remove(f)

        utils.makedirs(out_path)

        projects = ['tp_assist']
        utils.cmake(os.path.join(env.root_path, 'cmake-build-linux'), ctx.target_path, False, projects=projects)

        for f in out_files:
            if os.path.exists(f):
                utils.ensure_file_exists(f)

    def build_player(self):
        cc.e("this is no player for Linux platform yet.")

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
        builder.build_player()
        builder.build_assist()
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
