#!/bin/env python3
# -*- coding: utf-8 -*-

import shutil

from core import colorconsole as cc
from core import makepyo
from core import utils
from core.context import *
from core.ver import *

ctx = BuildContext()

ROOT_PATH = utils.cfg.ROOT_PATH


# COMMON_MODULES = ['paste', 'pyasn1', 'pymemcache', 'pymysql', 'rsa', 'tornado', 'six.py']


class BuilderBase:
    def __init__(self):
        self.out_dir = ''

    def build_installer(self):
        pass

    def _build_web_backend(self, base_path, dist, target_path):
        cc.n('make Teleport Backend package...')
        src_path = os.path.join(ROOT_PATH, 'web', 'site', 'backend')
        pkg_path = os.path.join(ROOT_PATH, 'web', 'packages')
        tmp_path = os.path.join(base_path, '_tmp_backend_')
        tmp_app_path = os.path.join(tmp_path, 'app')

        if os.path.exists(tmp_path):
            utils.remove(tmp_path)

        cc.n(' - make pyo and pack to zip...')

        shutil.copytree(os.path.join(src_path, 'app'), tmp_app_path)

        comm_path = os.path.join(pkg_path, 'common')
        comm_dir = os.listdir(comm_path)

        for d in comm_dir:
            s = os.path.join(comm_path, d)
            t = os.path.join(tmp_app_path, d)
            if os.path.isdir(s):
                shutil.copytree(s, t)
            else:
                shutil.copy(s, t)

        makepyo.make(tmp_app_path)
        shutil.make_archive(os.path.join(tmp_path, 'app'), 'zip', tmp_app_path)
        utils.remove(tmp_app_path)

        cc.n(' - copy packages...')
        pkgs = ['packages-common', 'packages-{}'.format(dist)]
        for d in pkgs:
            s = os.path.join(pkg_path, d)
            t = os.path.join(tmp_path, 'packages', d)
            if os.path.isdir(s):
                shutil.copytree(s, t)
            else:
                shutil.copy(s, t)

        makepyo.remove_cache(tmp_path)

        cc.n(' - copy static and view...')
        miscs = ['static', 'view', 'res', 'tools']
        for d in miscs:
            s = os.path.join(src_path, d)
            t = os.path.join(tmp_path, d)
            if os.path.isdir(s):
                shutil.copytree(s, t)
            else:
                shutil.copy(s, t)

        # self._create_start_file(os.path.join(tmp_path, 'eom_bootstrap.py'), 'ts-backend')

        shutil.copytree(tmp_path, os.path.join(target_path, 'www', 'backend'))
        utils.remove(tmp_path)

    # def _create_start_file(self, fname, name):
    #     f = open(fname, 'w')
    #     f.write('# -*- coding: utf-8 -*-\n')
    #     f.write('import os\n')
    #     f.write('import sys\n')
    #     f.write('p = os.path.abspath(os.path.dirname(__file__))\n')
    #     f.write('_p = os.path.join(p, "app.zip")\n')
    #     f.write('sys.path.insert(0, _p)\n')
    #     # f.write('_p = os.path.join(p, "{}", "app", "common.zip")\n'.format(name))
    #     # f.write('sys.path.insert(0, _p)\n')
    #     f.write('def main():\n')
    #     f.write('    try:\n')
    #     f.write('        import eom_main\n')
    #     f.write('        return eom_main.main()\n')
    #     f.write('    except:\n')
    #     f.write('        print("can not start {}.")\n'.format(name))
    #     f.write('        raise\n')
    #     f.write('if __name__ == "__main__":\n')
    #     f.write('    sys.exit(main())\n')
    #
    #     f.close()

    # def _build_web_frontend(self, base_path, dist, target_path):
    #     cc.n('make Teleport Frontend package...')
    #     src_path = os.path.join(ROOT_PATH, 'web', 'site', 'frontend')
    #     pkg_path = os.path.join(ROOT_PATH, 'web', 'packages')
    #     tmp_path = os.path.join(base_path, '_tmp_frontend_')
    #
    #     if os.path.exists(tmp_path):
    #         utils.remove(tmp_path)
    #
    #     shutil.copytree(os.path.join(src_path, 'app'), os.path.join(tmp_path, 'app'))
    #
    #     pkg_common = os.path.join(pkg_path, 'common')
    #     _s_path = os.listdir(pkg_common)
    #     for d in _s_path:
    #         s = os.path.join(pkg_common, d)
    #         t = os.path.join(tmp_path, 'app', d)
    #         if os.path.isdir(s):
    #             shutil.copytree(s, t)
    #         else:
    #             shutil.copy(s, t)
    #
    #     cc.n(' - copy packages...')
    #     pkgs = ['packages-common', 'packages-{}'.format(dist)]
    #     for d in pkgs:
    #         s = os.path.join(pkg_path, d)
    #         t = os.path.join(tmp_path, 'packages', d)
    #         if os.path.isdir(s):
    #             shutil.copytree(s, t)
    #         else:
    #             shutil.copy(s, t)
    #
    #     makepyo.remove_cache(tmp_path)
    #
    #     cc.n(' - copy static and view...')
    #     miscs = ['static', 'view', 'res']
    #     for d in miscs:
    #         s = os.path.join(src_path, d)
    #         t = os.path.join(tmp_path, d)
    #         if os.path.isdir(s):
    #             shutil.copytree(s, t)
    #         else:
    #             shutil.copy(s, t)
    #
    #     # if not os.path.exists(os.path.join(tmp_path, 'static', 'download')):
    #     #     utils.makedirs(os.path.join(tmp_path, 'static', 'download'))
    #     # utils.copy_file(os.path.join(ROOT_PATH, 'dist'), os.path.join(tmp_path, 'static', 'download'), 'teleport-assist-win.zip')
    #
    #     shutil.copytree(tmp_path, os.path.join(target_path, 'www', 'frontend'))
    #     utils.remove(tmp_path)


    def _build_web(self, base_path, dist, target_path):
        cc.n('make Teleport Web package...')
        src_path = os.path.join(ROOT_PATH, 'web', 'site', 'teleport')
        pkg_path = os.path.join(ROOT_PATH, 'web', 'packages')
        tmp_path = os.path.join(base_path, '_tmp_web_')

        if os.path.exists(tmp_path):
            utils.remove(tmp_path)

        shutil.copytree(os.path.join(src_path, 'app'), os.path.join(tmp_path, 'app'))

        pkg_common = os.path.join(pkg_path, 'common')
        _s_path = os.listdir(pkg_common)
        for d in _s_path:
            s = os.path.join(pkg_common, d)
            t = os.path.join(tmp_path, 'app', d)
            if os.path.isdir(s):
                shutil.copytree(s, t)
            else:
                shutil.copy(s, t)

        cc.n(' - copy packages...')
        pkgs = ['packages-common', 'packages-{}'.format(dist)]
        for d in pkgs:
            s = os.path.join(pkg_path, d)
            t = os.path.join(tmp_path, 'packages', d)
            if os.path.isdir(s):
                shutil.copytree(s, t)
            else:
                shutil.copy(s, t)

        makepyo.remove_cache(tmp_path)

        cc.n(' - copy static and view...')
        miscs = ['static', 'view', 'res', 'tools']
        for d in miscs:
            s = os.path.join(src_path, d)
            t = os.path.join(tmp_path, d)
            if os.path.isdir(s):
                shutil.copytree(s, t)
            else:
                shutil.copy(s, t)

        # if not os.path.exists(os.path.join(tmp_path, 'static', 'download')):
        #     utils.makedirs(os.path.join(tmp_path, 'static', 'download'))
        # utils.copy_file(os.path.join(ROOT_PATH, 'dist'), os.path.join(tmp_path, 'static', 'download'), 'teleport-assist-win.zip')

        shutil.copytree(tmp_path, os.path.join(target_path, 'www', 'teleport'))
        utils.remove(tmp_path)


class BuilderWin(BuilderBase):
    def __init__(self):
        super().__init__()

        # now = time.localtime(time.time())
        # _ver = '1.0.{:2d}.{:d}{:02d}'.format(now.tm_year - 2000, now.tm_mon, now.tm_mday)
        # self.name = 'teleport-server-windows-{}-{}'.format(ctx.bits_path, _ver)
        self.name = 'teleport-server-windows-{}-{}'.format(ctx.bits_path, VER_TELEPORT_SERVER)

        self.base_path = os.path.join(ROOT_PATH, 'dist', 'installer', ctx.dist, 'server')
        self.base_tmp = os.path.join(self.base_path, '_tmp_')
        self.tmp_path = os.path.join(self.base_tmp, self.name, 'data', 'teleport')

    def build_installer(self):
        cc.n('make teleport installer package...')

        if os.path.exists(self.base_tmp):
            utils.remove(self.base_tmp)

        # self._build_web_backend(self.base_path, 'windows', self.tmp_path)
        # utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'web-backend.conf')
        #
        # self._build_web_frontend(self.base_path, 'windows', self.tmp_path)
        # utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'web-frontend.conf')

        self._build_web(self.base_path, 'windows', self.tmp_path)
        utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'web.conf')

        # out_path = os.path.join(ROOT_PATH, 'out', 'eom_ts', ctx.target_path, ctx.dist_path)
        # bin_path = os.path.join(self.tmp_path, 'bin')
        # utils.copy_file(out_path, bin_path, 'eom_ts')
        # utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'etc'), 'eom_ts.ini')
        # utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'etc'), 'ts_ssh_server.key')

        out_path = os.path.join(ROOT_PATH, 'out', 'eom_ts', ctx.bits_path, ctx.target_path)
        bin_path = os.path.join(self.tmp_path, 'bin')
        utils.copy_ex(out_path, bin_path, 'eom_ts.exe')
        utils.copy_ex(out_path, bin_path, 'pysrt')

        utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'eom_ts.ini')
        # utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'license.key')
        utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'ts_ssh_server.key')
        # utils.copy_ex(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'ssl')

        # utils.copy_ex(os.path.join(ROOT_PATH, 'share', 'data'), os.path.join(self.tmp_path, 'tmp', 'data'), ('ts_db_release.db', 'ts_db.db'))
        utils.copy_ex(os.path.join(ROOT_PATH, 'share', 'data'), os.path.join(self.tmp_path, 'tmp', 'data'), 'main.sql')

        # utils.copy_ex(os.path.join(ROOT_PATH, 'share', 'data'), os.path.join(self.tmp_path, 'data'), ('ts_db_release.db', 'ts_db.db'))

        # utils.make_zip(os.path.join(self.tmp_path, '..'), os.path.join(self.tmp_path, '..', '..', 'teleport.zip'))
        # utils.copy_file(os.path.join(self.tmp_path, '..', '..'), os.path.join(self.tmp_path, '..'), 'teleport.zip')
        # utils.remove(os.path.join(self.tmp_path, '..', '..', 'teleport.zip'))
        # utils.remove(self.tmp_path)

        # make final installer.
        cc.n('pack final server installer...')
        out_file = os.path.join(ROOT_PATH, 'dist', '{}.zip'.format(self.name))

        if os.path.exists(out_file):
            utils.remove(out_file)

        # # copy installer scripts.
        # for i in ['daemon', 'install.sh', 'start.sh', 'stop.sh', 'status.sh']:
        #     shutil.copy(os.path.join(self.base_path, 'script', i), os.path.join(self.base_tmp, self.name, i))

        for i in ['install.bat', 'uninst.bat']:
            shutil.copy(os.path.join(self.base_path, 'script', i), os.path.abspath(os.path.join(self.tmp_path, '..', '..', i)))

        # for i in ['7z.exe']:
        #     shutil.copy(os.path.join(self.base_path, 'script', i), os.path.abspath(os.path.join(self.tmp_path, '..', '..', 'data', i)))

        utils.make_zip(os.path.join(self.base_tmp, self.name, '..'), out_file)


class BuilderLinux(BuilderBase):
    def __init__(self):
        super().__init__()

        # now = time.localtime(time.time())
        # _ver = '1.0.{:2d}.{:d}{:02d}'.format(now.tm_year - 2000, now.tm_mon, now.tm_mday)
        # self.name = 'teleport-server-linux-{}-{}'.format(ctx.bits_path, _ver)
        self.name = 'teleport-server-linux-{}-{}'.format(ctx.bits_path, VER_TELEPORT_SERVER)

        self.base_path = os.path.join(ROOT_PATH, 'dist', 'installer', ctx.dist, 'server')
        self.base_tmp = os.path.join(self.base_path, '_tmp_')
        self.tmp_path = os.path.join(self.base_tmp, self.name, 'data', 'teleport')

        # self.server_path = os.path.join(ROOT_PATH, 'dist', 'installer', ctx.dist, 'server')
        # self.script_path = self.tmp_path = os.path.join(self.server_path, 'script')
        # self.src_path = os.path.join(ROOT_PATH, 'source')
        # self.out_tmp_path = os.path.join(self.tmp_path, self.name, 'server')

    def build_installer(self):
        cc.n('make teleport installer package...')

        if os.path.exists(self.base_tmp):
            utils.remove(self.base_tmp)

        # self._build_web_backend(self.base_path, 'linux', self.tmp_path)
        # utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'web-backend.conf')
        #
        # self._build_web_frontend(self.base_path, 'linux', self.tmp_path)
        # utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'web-frontend.conf')

        self._build_web(self.base_path, 'linux', self.tmp_path)
        utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'web.conf')

        # out_path = os.path.join(ROOT_PATH, 'out', 'eom_ts', ctx.target_path, ctx.dist_path)
        # out_path = os.path.join(ROOT_PATH, 'out', 'eom_ts', ctx.bits_path, 'bin')
        # bin_path = os.path.join(self.tmp_path, 'bin')
        # utils.copy_file(out_path, bin_path, 'eom_ts')

        out_path = os.path.join(ROOT_PATH, 'out', 'eom_ts', ctx.bits_path, 'bin')
        bin_path = os.path.join(self.tmp_path, 'bin')
        utils.copy_ex(out_path, bin_path, 'eom_ts')

        # utils.copy_ex(out_path, bin_path, 'pysrt')
        utils.copy_ex(os.path.join(ROOT_PATH, 'dist', 'pysrt'), bin_path, (ctx.dist_path, 'pysrt'))

        utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'eom_ts.ini')
        # utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'license.key')
        utils.copy_file(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'ts_ssh_server.key')
        utils.copy_ex(os.path.join(ROOT_PATH, 'share', 'etc'), os.path.join(self.tmp_path, 'tmp', 'etc'), 'ssl')

        # utils.copy_ex(os.path.join(ROOT_PATH, 'share', 'data'), os.path.join(self.tmp_path, 'tmp', 'data'), ('ts_db_release.db', 'ts_db.db'))
        utils.copy_ex(os.path.join(ROOT_PATH, 'share', 'data'), os.path.join(self.tmp_path, 'tmp', 'data'), 'main.sql')

        # utils.make_zip(self.tmp_path, os.path.join(self.tmp_path, '..', 'eom_ts.zip'))
        utils.make_targz(os.path.join(self.tmp_path, '..'), 'teleport', 'teleport.tar.gz')
        utils.remove(self.tmp_path)

        # make final installer.
        cc.n('pack final server installer...')
        # out_file = os.path.join(ROOT_PATH, 'dist', '{}.zip'.format(self.name))
        out_file = os.path.join(ROOT_PATH, 'dist', '{}.tar.gz'.format(self.name))

        if os.path.exists(out_file):
            utils.remove(out_file)

        # # copy installer scripts.
        for i in ['daemon', 'start.sh', 'stop.sh', 'status.sh']:
            shutil.copy(os.path.join(self.base_path, 'script', i), os.path.abspath(os.path.join(self.tmp_path, '..', i)))
        for i in ['install.sh']:
            shutil.copy(os.path.join(self.base_path, 'script', i), os.path.abspath(os.path.join(self.tmp_path, '..', '..', i)))

        # utils.make_zip(os.path.join(self.base_tmp, self.name), out_file)
        utils.make_targz(self.base_tmp, self.name, out_file)


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
