# -*- coding: utf-8 -*-

from core import colorconsole as cc
from core import utils
from core.context import *
from core.env import env

ctx = BuildContext()
with_rdp = os.path.exists(os.path.join(env.root_path, 'server', 'tp_core', 'protocol', 'rdp'))


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
        # notice: now we can not build debug version of tp_web.exe
        if ctx.target_path == 'debug':
            cc.w('cannot build debug version of tp_web, skip.')
        else:
            sln_file = os.path.join(env.root_path, 'server', 'tp_web', 'src', 'tp_web.vs2017.sln')
            out_file = os.path.join(env.root_path, 'out', 'server', ctx.bits_path, ctx.target_path, 'tp_web.exe')
            if os.path.exists(out_file):
                utils.remove(out_file)
            utils.msvc_build(sln_file, 'tp_web', ctx.target_path, ctx.bits_path, False)
            utils.ensure_file_exists(out_file)

        cc.n('build core server ...')
        sln_file = os.path.join(env.root_path, 'server', 'tp_core', 'core', 'tp_core.vs2017.sln')
        out_file = os.path.join(env.root_path, 'out', 'server', ctx.bits_path, ctx.target_path, 'tp_core.exe')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.msvc_build(sln_file, 'tp_core', ctx.target_path, ctx.bits_path, False)
        utils.ensure_file_exists(out_file)

        cc.n('build SSH protocol ...')
        sln_file = os.path.join(env.root_path, 'server', 'tp_core', 'protocol', 'ssh', 'tpssh.vs2017.sln')
        out_file = os.path.join(env.root_path, 'out', 'server', ctx.bits_path, ctx.target_path, 'tpssh.dll')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.msvc_build(sln_file, 'tpssh', ctx.target_path, ctx.bits_path, False)
        utils.ensure_file_exists(out_file)
        utils.copy_file(os.path.join(env.root_path, 'external', 'libssh', 'lib', ctx.target_path), os.path.join(env.root_path, 'out', 'server', ctx.bits_path, ctx.target_path), 'ssh.dll')

        cc.n('build TELNET protocol ...')
        sln_file = os.path.join(env.root_path, 'server', 'tp_core', 'protocol', 'telnet', 'tptelnet.vs2017.sln')
        out_file = os.path.join(env.root_path, 'out', 'server', ctx.bits_path, ctx.target_path, 'tptelnet.dll')
        if os.path.exists(out_file):
            utils.remove(out_file)
        utils.msvc_build(sln_file, 'tptelnet', ctx.target_path, ctx.bits_path, False)
        utils.ensure_file_exists(out_file)

        if with_rdp:
            cc.n('build RDP protocol ...')
            sln_file = os.path.join(env.root_path, 'server', 'tp_core', 'protocol', 'rdp', 'tprdp.vs2017.sln')
            out_file = os.path.join(env.root_path, 'out', 'server', ctx.bits_path, ctx.target_path, 'tprdp.dll')
            if os.path.exists(out_file):
                utils.remove(out_file)
            utils.msvc_build(sln_file, 'tprdp', ctx.target_path, ctx.bits_path, False)
            utils.ensure_file_exists(out_file)


class BuilderLinux(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_server(self):
        cc.n('build server app (tp_core/libtpssh/libtelnet/librdp/tp_web)...')

        out_path = os.path.join(env.root_path, 'out', 'server', ctx.bits_path, 'bin')
        out_files = list()
        out_files.append(os.path.join(out_path, 'tp_core'))
        out_files.append(os.path.join(out_path, 'tp_web'))
        out_files.append(os.path.join(out_path, 'libtpssh.so'))
        out_files.append(os.path.join(out_path, 'libtptelnet.so'))
        if with_rdp:
            out_files.append(os.path.join(out_path, 'libtprdp.so'))

        for f in out_files:
            if os.path.exists(f):
                utils.remove(f)

        utils.makedirs(out_path)

        utils.cmake(os.path.join(env.root_path, 'cmake-build'), ctx.target_path, False)
        # utils.strip(out_file)

        for f in out_files:
            if os.path.exists(f):
                utils.ensure_file_exists(f)


class BuilderMacOS(BuilderBase):
    def __init__(self):
        super().__init__()

    def build_server(self):
        cc.n('build server app (tp_core/libtpssh/libtelnet/librdp/tp_web)...')

        out_path = os.path.join(env.root_path, 'out', 'server', ctx.bits_path, 'bin')
        out_files = list()
        out_files.append(os.path.join(out_path, 'tp_core'))
        out_files.append(os.path.join(out_path, 'tp_web'))
        out_files.append(os.path.join(out_path, 'libtpssh.so'))
        out_files.append(os.path.join(out_path, 'libtptelnet.so'))
        if with_rdp:
            out_files.append(os.path.join(out_path, 'libtprdp.so'))

        for f in out_files:
            if os.path.exists(f):
                utils.remove(f)

        utils.makedirs(out_path)

        utils.cmake(os.path.join(env.root_path, 'cmake-build'), ctx.target_path, False)
        # utils.strip(out_file)

        for f in out_files:
            if os.path.exists(f):
                utils.ensure_file_exists(f)


def gen_builder(dist):
    if dist == 'windows':
        builder = BuilderWin()
    elif dist == 'linux':
        builder = BuilderLinux()
    elif dist == 'macos':
        builder = BuilderMacOS()
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

    if 'server' in argv:
        builder.build_server()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        cc.e(e.__str__())
    except:
        cc.f('got exception.')
