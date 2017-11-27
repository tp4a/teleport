# -*- coding: utf-8 -*-

import shutil

from core import colorconsole as cc
from core import makepyo
from core import utils
from core.env import env
from core.context import *
from core.ver import *

ctx = BuildContext()
with_rdp = os.path.exists(os.path.join(env.root_path, 'server', 'tp_core', 'protocol', 'rdp'))
with_telnet = os.path.exists(os.path.join(env.root_path, 'server', 'tp_core', 'protocol', 'telnet'))


# COMMON_MODULES = ['paste', 'pyasn1', 'pymemcache', 'pymysql', 'rsa', 'tornado', 'six.py']


class BuilderBase:
    def __init__(self):
        self.out_dir = ''

    def build_installer(self):
        pass

    def _build_web(self, base_path, dist, target_path):
        cc.n('make Teleport Web package...')
        src_path = os.path.join(env.root_path, 'server', 'www')
        pkg_path = os.path.join(src_path, 'packages')
        tmp_path = os.path.join(base_path, '_tmp_web_')

        if os.path.exists(tmp_path):
            utils.remove(tmp_path)

        shutil.copytree(os.path.join(src_path, 'teleport'), os.path.join(tmp_path, 'teleport'))
        utils.remove(os.path.join(tmp_path, 'teleport', '.idea'))

        cc.n(' - copy packages...')
        utils.copy_ex(pkg_path, os.path.join(tmp_path, 'packages'), 'packages-common')
        utils.copy_ex(os.path.join(pkg_path, 'packages-{}'.format(dist)), os.path.join(tmp_path, 'packages', 'packages-{}'.format(dist)), ctx.bits_path)

        makepyo.remove_cache(tmp_path)

        shutil.copytree(tmp_path, os.path.join(target_path, 'www'))
        utils.remove(tmp_path)


class BuilderWin(BuilderBase):
    def __init__(self):
        super().__init__()
        self.name = 'teleport-server-windows-{}-{}'.format(ctx.bits_path, VER_TP_SERVER)
        self._final_file = os.path.join(env.root_path, 'out', 'installer', '{}.zip'.format(self.name))

        self.dist_path = os.path.join(env.root_path, 'dist', 'server')
        self.base_path = os.path.join(env.root_path, 'out', 'installer')
        self.base_tmp = os.path.join(self.base_path, '_tmp_')

        self.path_tmp = os.path.join(self.base_tmp, self.name)
        self.path_tmp_data = os.path.join(self.path_tmp, 'data')

    def build_installer(self):
        cc.n('make teleport installer package...')

        if os.path.exists(self.base_tmp):
            utils.remove(self.base_tmp)

        self._build_web(self.base_path, 'windows', self.path_tmp_data)
        utils.copy_file(os.path.join(env.root_path, 'server', 'share', 'etc'), os.path.join(self.path_tmp_data, 'tmp', 'etc'), ('web.ini.in', 'web.ini'))
        utils.copy_file(os.path.join(env.root_path, 'server', 'share', 'etc'), os.path.join(self.path_tmp_data, 'tmp', 'etc'), ('core.ini.in', 'core.ini'))
        utils.copy_file(os.path.join(env.root_path, 'server', 'share', 'etc'), os.path.join(self.path_tmp_data, 'tmp', 'etc'), 'tp_ssh_server.key')

        out_path = os.path.join(env.root_path, 'out', 'server', ctx.bits_path, ctx.target_path)
        bin_path = os.path.join(self.path_tmp_data, 'bin')
        utils.copy_ex(out_path, bin_path, 'tp_web.exe')
        utils.copy_ex(out_path, bin_path, 'tp_core.exe')
        utils.copy_ex(out_path, bin_path, 'tpssh.dll')
        if with_rdp:
            utils.copy_ex(out_path, bin_path, 'tprdp.dll')

        utils.copy_ex(os.path.join(env.root_path, 'out', 'pysrt'), bin_path, (ctx.dist_path, 'pysrt'))

        # 复制安装所需的脚本
        utils.copy_ex(os.path.join(self.dist_path), self.path_tmp, 'setup.bat')
        utils.copy_ex(os.path.join(self.dist_path), self.path_tmp, 'script')

        if os.path.exists(self._final_file):
            utils.remove(self._final_file)

        utils.make_zip(self.path_tmp, self._final_file)

        # utils.remove(self.base_tmp)


class BuilderLinux(BuilderBase):
    def __init__(self):
        super().__init__()
        self.name = 'teleport-server-linux-{}-{}'.format(ctx.bits_path, VER_TP_SERVER)
        self._final_file = os.path.join(env.root_path, 'out', 'installer', '{}.tar.gz'.format(self.name))

        self.dist_path = os.path.join(env.root_path, 'dist', 'server')
        self.base_path = os.path.join(env.root_path, 'out', 'installer')
        self.base_tmp = os.path.join(self.base_path, '_tmp_')

        self.path_tmp = os.path.join(self.base_tmp, self.name)
        self.path_tmp_data = os.path.join(self.path_tmp, 'data')

        # self.server_path = os.path.join(env.root_path, 'dist', 'installer', ctx.dist, 'server')
        # self.script_path = self.tmp_path = os.path.join(self.server_path, 'script')
        # self.src_path = os.path.join(env.root_path, 'source')
        # self.out_tmp_path = os.path.join(self.tmp_path, self.name, 'server')

    def build_installer(self):
        cc.n('make teleport installer package...')

        if os.path.exists(self.base_tmp):
            utils.remove(self.base_tmp)

        self._build_web(self.base_path, 'linux', self.path_tmp_data)

        utils.copy_file(os.path.join(env.root_path, 'server', 'share', 'etc'), os.path.join(self.path_tmp_data, 'tmp', 'etc'), ('web.ini.in', 'web.ini'))
        utils.copy_file(os.path.join(env.root_path, 'server', 'share', 'etc'), os.path.join(self.path_tmp_data, 'tmp', 'etc'), ('core.ini.in', 'core.ini'))
        utils.copy_file(os.path.join(env.root_path, 'server', 'share', 'etc'), os.path.join(self.path_tmp_data, 'tmp', 'etc'), 'tp_ssh_server.key')

        # fix new line flag
        utils.fix_new_line_flag(os.path.join(self.path_tmp_data, 'tmp', 'etc', 'web.ini'))
        utils.fix_new_line_flag(os.path.join(self.path_tmp_data, 'tmp', 'etc', 'core.ini'))

        # out_path = os.path.join(env.root_path, 'out', 'eom_ts', ctx.target_path, ctx.dist_path)
        # out_path = os.path.join(env.root_path, 'out', 'eom_ts', ctx.bits_path, 'bin')
        # bin_path = os.path.join(self.tmp_path, 'bin')
        # utils.copy_file(out_path, bin_path, 'eom_ts')

        out_path = os.path.join(env.root_path, 'out', 'server', ctx.bits_path, 'bin')
        bin_path = os.path.join(self.path_tmp_data, 'bin')
        utils.copy_ex(out_path, bin_path, 'tp_web')
        utils.copy_ex(out_path, bin_path, 'tp_core')
        utils.copy_ex(out_path, bin_path, 'libtpssh.so')
        if with_rdp:
            utils.copy_ex(out_path, bin_path, 'libtprdp.so')

        utils.copy_ex(os.path.join(env.root_path, 'out', 'pysrt'), bin_path, (ctx.dist_path, 'pysrt'))

        # utils.copy_file(os.path.join(env.root_path, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'eom_ts.ini')
        # utils.copy_file(os.path.join(env.root_path, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'license.key')
        # utils.copy_ex(os.path.join(env.root_path, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'ssl')

        # utils.copy_ex(os.path.join(env.root_path, 'share', 'data'), os.path.join(self.tmp_path, 'tmp', 'data'), ('ts_db_release.db', 'ts_db.db'))
        # utils.copy_ex(os.path.join(env.root_path, 'server', 'share', 'data'), os.path.join(self.tmp_path, 'tmp', 'data'), 'main.sql')

        # utils.make_zip(self.tmp_path, os.path.join(self.tmp_path, '..', 'eom_ts.zip'))
        # utils.make_targz(os.path.join(self.tmp_path, '..'), 'teleport', 'teleport.tar.gz')
        # utils.remove(self.tmp_path)

        # make final installer.
        # cc.n('pack final server installer...')
        # out_file = os.path.join(env.root_path, 'dist', '{}.zip'.format(self.name))
        # out_file = os.path.join(env.root_path, 'out', 'installer', '{}.tar.gz'.format(self.name))

        # if os.path.exists(out_file):
        #     utils.remove(out_file)

        # # copy installer scripts.
        # for i in ['daemon', 'start.sh', 'stop.sh', 'status.sh']:
        # # for i in ['daemon_web', 'daemon_core', 'teleport.sh']:
        #     shutil.copy(os.path.join(self.dist_path, 'script', i), os.path.abspath(os.path.join(self.tmp_path, '..', i)))
        # for i in ['install.sh', 'uninst.sh']:
        #     shutil.copy(os.path.join(self.dist_path, 'script', i), os.path.abspath(os.path.join(self.tmp_path, '..', '..', i)))

        # 复制安装所需的脚本
        # utils.copy_ex(os.path.join(self.dist_path, 'script'), self.path_tmp, 'install.sh')
        # utils.copy_ex(os.path.join(self.dist_path, 'script'), self.path_tmp, 'uninst.sh')
        utils.copy_ex(os.path.join(self.dist_path), self.path_tmp, 'setup.sh')
        utils.copy_ex(os.path.join(self.dist_path), self.path_tmp, 'script')
        utils.copy_ex(os.path.join(self.dist_path), self.path_tmp, 'daemon')

        if os.path.exists(self._final_file):
            utils.remove(self._final_file)

        utils.make_targz(self.base_tmp, self.name, self._final_file)

        # utils.remove(self.base_tmp)


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

    if 'installer' in argv:
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
