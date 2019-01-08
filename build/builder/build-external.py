# -*- coding: utf-8 -*-

import time

from core import colorconsole as cc
from core import utils
from core.context import *

from core.env import env

ctx = BuildContext()

PATH_EXTERNAL = os.path.join(env.root_path, 'external')
PATH_DOWNLOAD = os.path.join(PATH_EXTERNAL, '_download_')


class BuilderBase:
    def __init__(self):
        self.out_dir = ''
        if not os.path.exists(PATH_DOWNLOAD):
            utils.makedirs(PATH_DOWNLOAD)

        self._init_path()

    def _init_path(self):
        cc.e("this is a pure-virtual function.")

    def build_jsoncpp(self):
        file_name = 'jsoncpp-{}.zip'.format(env.ver_jsoncpp)
        if not utils.download_file('jsoncpp source tarball', 'https://github.com/open-source-parsers/jsoncpp/archive/{}.zip'.format(env.ver_jsoncpp), PATH_DOWNLOAD, file_name):
            return
        self._build_jsoncpp(file_name)

    def _build_jsoncpp(self, file_name):
        cc.e("this is a pure-virtual function.")

    def build_mongoose(self):
        file_name = 'mongoose-{}.zip'.format(env.ver_mongoose)
        if not utils.download_file('mongoose source tarball', 'https://github.com/cesanta/mongoose/archive/{}.zip'.format(env.ver_mongoose), PATH_DOWNLOAD, file_name):
            return
        self._build_mongoose(file_name)

    def _build_mongoose(self, file_name):
        cc.e("this is a pure-virtual function.")

    def build_openssl(self):
        file_name = 'openssl-{}.zip'.format(env.ver_ossl)
        self._build_openssl(file_name)

    def _build_openssl(self, file_name):
        _alt_ver = '_'.join(env.ver_ossl.split('.'))
        if not utils.download_file('openssl source tarball', 'https://github.com/openssl/openssl/archive/OpenSSL_{}.zip'.format(_alt_ver), PATH_DOWNLOAD, file_name):
            cc.e("can not download openssl source tarball.")
            return False
        else:
            return True

    def build_libuv(self):
        file_name = 'libuv-{}.zip'.format(env.ver_libuv)
        if not utils.download_file('libuv source tarball', 'https://github.com/libuv/libuv/archive/v{}.zip'.format(env.ver_libuv), PATH_DOWNLOAD, file_name):
            return
        self._build_libuv(file_name)

    def _build_libuv(self, file_name):
        cc.e("this is a pure-virtual function.")

    def build_mbedtls(self):
        file_name = 'mbedtls-mbedtls-{}.zip'.format(env.ver_mbedtls)
        if not utils.download_file('mbedtls source tarball', 'https://github.com/ARMmbed/mbedtls/archive/mbedtls-{}.zip'.format(env.ver_mbedtls), PATH_DOWNLOAD, file_name):
            return
        self._build_mbedtls(file_name)

    def _build_mbedtls(self, file_name):
        cc.e("this is a pure-virtual function.")

    def build_libssh(self):
        file_name = 'libssh-{}.zip'.format(env.ver_libssh)
        if not utils.download_file('libssh source tarball', 'https://git.libssh.org/projects/libssh.git/snapshot/libssh-{}.zip'.format(env.ver_libssh), PATH_DOWNLOAD, file_name):
            return
        self._build_libssh(file_name)

    def _build_libssh(self, file_name):
        cc.e("this is a pure-virtual function.")

    def prepare_python(self):
        self._prepare_python()

    def _prepare_python(self):
        cc.e("this is a pure-virtual function.")

    def fix_output(self):
        pass


class BuilderWin(BuilderBase):
    def __init__(self):
        super().__init__()

    def _init_path(self):
        self.OPENSSL_PATH_SRC = os.path.join(PATH_EXTERNAL, 'openssl')
        self.JSONCPP_PATH_SRC = os.path.join(PATH_EXTERNAL, 'jsoncpp')
        self.MONGOOSE_PATH_SRC = os.path.join(PATH_EXTERNAL, 'mongoose')
        self.MBEDTLS_PATH_SRC = os.path.join(PATH_EXTERNAL, 'mbedtls')
        self.LIBUV_PATH_SRC = os.path.join(PATH_EXTERNAL, 'libuv')
        self.LIBSSH_PATH_SRC = os.path.join(PATH_EXTERNAL, 'libssh')

    def _prepare_python(self):
        cc.n('prepare python header files ...', end='')

        if os.path.exists(os.path.join(PATH_EXTERNAL, 'python', 'include', 'Python.h')):
            cc.w('already exists, skip.')
            return
        cc.v('')

        _header_path = None
        for p in sys.path:
            if os.path.exists(os.path.join(p, 'include', 'Python.h')):
                _header_path = os.path.join(p, 'include')
        if _header_path is None:
            cc.e('\ncan not locate python development include path in:')
            for p in sys.path:
                cc.e('  ', p)
            raise RuntimeError()

        utils.copy_ex(_header_path, os.path.join(PATH_EXTERNAL, 'python', 'include'))

    def _build_openssl(self, file_name):
        cc.n('build openssl static library from source code... ')

        if not super()._build_openssl(file_name):
            return

        _chk_output = [
            os.path.join(self.OPENSSL_PATH_SRC, 'out32', 'libeay32.lib'),
            os.path.join(self.OPENSSL_PATH_SRC, 'out32', 'ssleay32.lib'),
            os.path.join(self.OPENSSL_PATH_SRC, 'inc32', 'openssl', 'opensslconf.h'),
            ]

        need_build = False
        for f in _chk_output:
            if not os.path.exists(f):
                need_build = True
                break

        if not need_build:
            cc.n('build openssl static library from source code... ', end='')
            cc.w('already exists, skip.')
            return
        cc.v('')

        cc.n('prepare openssl source code...')
        _alt_ver = '_'.join(env.ver_ossl.split('.'))
        if not os.path.exists(self.OPENSSL_PATH_SRC):
            utils.unzip(os.path.join(PATH_DOWNLOAD, file_name), PATH_EXTERNAL)
            os.rename(os.path.join(PATH_EXTERNAL, 'openssl-OpenSSL_{}'.format(_alt_ver)), self.OPENSSL_PATH_SRC)
            if not os.path.exists(self.OPENSSL_PATH_SRC):
                raise RuntimeError('can not prepare openssl source code.')
        else:
            cc.w('already exists, skip.')

        os.chdir(self.OPENSSL_PATH_SRC)
        os.system('""{}" Configure VC-WIN32"'.format(env.perl))
        os.system(r'ms\do_nasm')
        # for vs2015
        # utils.sys_exec(r'"{}\VC\bin\vcvars32.bat" && nmake -f ms\nt.mak'.format(env.visual_studio_path), direct_output=True)
        # for vs2017 community
        utils.sys_exec(r'"{}VC\Auxiliary\Build\vcvars32.bat" && nmake -f ms\nt.mak'.format(env.visual_studio_path), direct_output=True)

        for f in _chk_output:
            if not os.path.exists(f):
                raise RuntimeError('build openssl static library from source code failed.')

    def _build_libssh(self, file_name):
        cc.n('build libssh static library from source code... ', end='')

        if not os.path.exists(self.LIBSSH_PATH_SRC):
            cc.v('')
            utils.unzip(os.path.join(PATH_DOWNLOAD, file_name), PATH_EXTERNAL)
            os.rename(os.path.join(PATH_EXTERNAL, 'libssh-{}'.format(env.ver_libssh)), self.LIBSSH_PATH_SRC)

            # cc.n('fix libssh source code... ', end='')
            # utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', 'src', 'sftp.c'))
            # utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', 'src'), os.path.join(self.LIBSSH_PATH_SRC, 'src'), 'sftp.c')
            cc.n('fix libssh source code... ', end='')
            s_name = 'libssh-{}'.format(env.ver_libssh)
            utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src', 'session.c'))
            utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src', 'libcrypto.c'))
            utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src', 'libcrypto-compat.c'))
            utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src'), os.path.join(self.LIBSSH_PATH_SRC, 'src'), 'session.c')
            utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src'), os.path.join(self.LIBSSH_PATH_SRC, 'src'), 'libcrypto.c')
            utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src'), os.path.join(self.LIBSSH_PATH_SRC, 'src'), 'libcrypto-compat.c')

        out_file_lib = os.path.join(self.LIBSSH_PATH_SRC, 'lib', ctx.target_path, 'ssh.lib')
        out_file_dll = os.path.join(self.LIBSSH_PATH_SRC, 'lib', ctx.target_path, 'ssh.dll')

        if os.path.exists(out_file_lib) and os.path.exists(out_file_dll):
            cc.w('already exists, skip.')
            return
        cc.v('')

        cc.w('On Windows, when build libssh, need you use cmake-gui.exe to generate solution file')
        cc.w('for Visual Studio 2017. Visit https://docs.tp4a.com for more details.')
        cc.w('\nOnce the libssh.sln generated, press Enter to continue or Q to quit...', end='')
        try:
            x = env.input()
        except EOFError:
            x = 'q'
        if x == 'q':
            return

        cc.i('build libssh...')
        sln_file = os.path.join(self.LIBSSH_PATH_SRC, 'build', 'libssh.sln')
        utils.msvc_build(sln_file, 'ssh_shared', ctx.target_path, 'win32', False)
        utils.ensure_file_exists(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src', ctx.target_path, 'ssh.lib'))
        utils.ensure_file_exists(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src', ctx.target_path, 'ssh.dll'))
        utils.copy_file(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src', ctx.target_path), os.path.join(self.LIBSSH_PATH_SRC, 'lib', ctx.target_path), 'ssh.lib')
        utils.copy_file(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src', ctx.target_path), os.path.join(self.LIBSSH_PATH_SRC, 'lib', ctx.target_path), 'ssh.dll')
        utils.ensure_file_exists(out_file_lib)
        utils.ensure_file_exists(out_file_dll)

    def _build_jsoncpp(self, file_name):
        cc.n('prepare jsoncpp source code... ', end='')
        if not os.path.exists(self.JSONCPP_PATH_SRC):
            cc.v('')
            utils.unzip(os.path.join(PATH_DOWNLOAD, file_name), PATH_EXTERNAL)
            os.rename(os.path.join(PATH_EXTERNAL, 'jsoncpp-{}'.format(env.ver_jsoncpp)), self.JSONCPP_PATH_SRC)
        else:
            cc.w('already exists, skip.')

    def _build_mongoose(self, file_name):
        cc.n('prepare mongoose source code... ', end='')
        if not os.path.exists(self.MONGOOSE_PATH_SRC):
            cc.v('')
            utils.unzip(os.path.join(PATH_DOWNLOAD, file_name), PATH_EXTERNAL)
            os.rename(os.path.join(PATH_EXTERNAL, 'mongoose-{}'.format(env.ver_mongoose)), self.MONGOOSE_PATH_SRC)
        else:
            cc.w('already exists, skip.')

    def _build_mbedtls(self, file_name):
        cc.n('prepare mbedtls source code... ', end='')
        if not os.path.exists(self.MBEDTLS_PATH_SRC):
            cc.v('')
            utils.unzip(os.path.join(PATH_DOWNLOAD, file_name), PATH_EXTERNAL)
            os.rename(os.path.join(PATH_EXTERNAL, 'mbedtls-mbedtls-{}'.format(env.ver_mbedtls)), self.MBEDTLS_PATH_SRC)
        else:
            cc.w('already exists, skip.')
            return
        cc.v('')

        # fix source file
        utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'include', 'mbedtls', 'config.h'))
        utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'include', 'mbedtls'), os.path.join(self.MBEDTLS_PATH_SRC, 'include', 'mbedtls'), 'config.h')
        # utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'library', 'rsa.c'))
        # utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'library'), os.path.join(self.MBEDTLS_PATH_SRC, 'library'), 'rsa.c')

    def _build_libuv(self, file_name):
        cc.n('prepare libuv source code... ', end='')
        if not os.path.exists(self.LIBUV_PATH_SRC):
            cc.v('')
            utils.unzip(os.path.join(PATH_DOWNLOAD, file_name), PATH_EXTERNAL)
            time.sleep(1)   # wait for a while, otherwise rename may fail.
            os.rename(os.path.join(PATH_EXTERNAL, 'libuv-{}'.format(env.ver_libuv)), self.LIBUV_PATH_SRC)
        else:
            cc.w('already exists, skip.')

    def fix_output(self):
        pass


class BuilderLinux(BuilderBase):
    def __init__(self):
        super().__init__()

    def _init_path(self):
        self.PATH_TMP = os.path.join(PATH_EXTERNAL, 'linux', 'tmp')
        self.PATH_RELEASE = os.path.join(PATH_EXTERNAL, 'linux', 'release')
        self.LIBUV_PATH_SRC = os.path.join(self.PATH_TMP, 'libuv-{}'.format(env.ver_libuv))
        self.MBEDTLS_PATH_SRC = os.path.join(self.PATH_TMP, 'mbedtls-mbedtls-{}'.format(env.ver_mbedtls))
        self.LIBSSH_PATH_SRC = os.path.join(self.PATH_TMP, 'libssh-{}'.format(env.ver_libssh))

        self.JSONCPP_PATH_SRC = os.path.join(PATH_EXTERNAL, 'jsoncpp')
        self.MONGOOSE_PATH_SRC = os.path.join(PATH_EXTERNAL, 'mongoose')

        if not os.path.exists(self.PATH_TMP):
            utils.makedirs(self.PATH_TMP)

    def _prepare_python(self):
        cc.n('prepare python header and lib files ...')

        if os.path.exists(os.path.join(self.PATH_RELEASE, 'include', 'python', 'Python.h')):
            cc.w(' - header file already exists, skip.')
        else:
            utils.ensure_file_exists(os.path.join(self.PATH_RELEASE, 'include', 'python{}m'.format(ctx.py_dot_ver), 'Python.h'))
            utils.sys_exec('ln -s "{}" "{}"'.format(
                os.path.join(self.PATH_RELEASE, 'include', 'python{}m'.format(ctx.py_dot_ver)),
                os.path.join(self.PATH_RELEASE, 'include', 'python')
            ))

        lib_file = 'libpython{}m.a'.format(env.py_ver_dot)
        utils.ensure_file_exists(os.path.join(self.PATH_RELEASE, 'lib', lib_file))

    def _build_jsoncpp(self, file_name):
        cc.n('prepare jsoncpp source code...', end='')
        if not os.path.exists(self.JSONCPP_PATH_SRC):
            cc.v('')
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, PATH_EXTERNAL))
            os.rename(os.path.join(PATH_EXTERNAL, 'jsoncpp-{}'.format(env.ver_jsoncpp)), self.JSONCPP_PATH_SRC)
        else:
            cc.w('already exists, skip.')

    def _build_mongoose(self, file_name):
        cc.n('prepare mongoose source code...', end='')
        if not os.path.exists(self.MONGOOSE_PATH_SRC):
            cc.v('')
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, PATH_EXTERNAL))
            os.rename(os.path.join(PATH_EXTERNAL, 'mongoose-{}'.format(env.ver_mongoose)), self.MONGOOSE_PATH_SRC)
        else:
            cc.w('already exists, skip.')

    def _build_openssl(self, file_name):
        pass  # we do not need build openssl anymore, because first time run build.sh we built Python, it include openssl.

    def _build_libuv(self, file_name):
        if not os.path.exists(self.LIBUV_PATH_SRC):
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build libuv...', end='')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libuv.a')):
            cc.w('already exists, skip.')
            return
        cc.v('')

        # we need following...
        # apt-get install autoconf aptitude libtool gcc-c++

        old_p = os.getcwd()
        os.chdir(self.LIBUV_PATH_SRC)
        os.system('sh autogen.sh')
        os.system('./configure --prefix={} --with-pic'.format(self.PATH_RELEASE))
        os.system('make')
        os.system('make install')
        os.chdir(old_p)

        files = os.listdir(os.path.join(self.PATH_RELEASE, 'lib'))
        for i in files:
            if i.startswith('libuv.so') or i.startswith('libuv.la'):
                # use os.unlink() because some file should be a link.
                os.unlink(os.path.join(self.PATH_RELEASE, 'lib', i))

    def _build_mbedtls(self, file_name):
        if not os.path.exists(self.MBEDTLS_PATH_SRC):
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build mbedtls...', end='')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libmbedtls.a')):
            cc.w('already exists, skip.')
            return
        cc.v('')

        # fix the Makefile
        mkfile = os.path.join(self.MBEDTLS_PATH_SRC, 'Makefile')
        f = open(mkfile)
        fl = f.readlines()
        f.close()

        fixed = False
        for i in range(len(fl)):
            x = fl[i].split('=')
            if x[0] == 'DESTDIR':
                fl[i] = 'DESTDIR={}\n'.format(self.PATH_RELEASE)
                fixed = True
                break

        if not fixed:
            cc.e('can not fix Makefile of mbedtls.')
            return

        f = open(mkfile, 'w')
        f.writelines(fl)
        f.close()

        # fix source file
        utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'include', 'mbedtls', 'config.h'))
        utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'include', 'mbedtls'), os.path.join(self.MBEDTLS_PATH_SRC, 'include', 'mbedtls'), 'config.h')
        # utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'library', 'rsa.c'))
        # utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'library'), os.path.join(self.MBEDTLS_PATH_SRC, 'library'), 'rsa.c')

        old_p = os.getcwd()
        os.chdir(self.MBEDTLS_PATH_SRC)
        os.system('make CFLAGS="-fPIC" lib')
        os.system('make install')
        os.chdir(old_p)

    def _build_libssh(self, file_name):
        if not os.path.exists(self.LIBSSH_PATH_SRC):
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build libssh...', end='')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libssh.a')):
            cc.w('already exists, skip.')
            return
        cc.v('')

        cc.n('fix libssh source code... ', end='')
        s_name = 'libssh-{}'.format(env.ver_libssh)
        utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src', 'session.c'))
        utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src', 'libcrypto.c'))
        utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src', 'libcrypto-compat.c'))
        utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src'), os.path.join(self.LIBSSH_PATH_SRC, 'src'), 'session.c')
        utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src'), os.path.join(self.LIBSSH_PATH_SRC, 'src'), 'libcrypto.c')
        utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'libssh', s_name, 'src'), os.path.join(self.LIBSSH_PATH_SRC, 'src'), 'libcrypto-compat.c')

        build_path = os.path.join(self.LIBSSH_PATH_SRC, 'build')

        cmake_define = ' -DCMAKE_INSTALL_PREFIX={path_release}' \
                       ' -DOPENSSL_INCLUDE_DIR={path_release}/include' \
                       ' -DOPENSSL_LIBRARIES={path_release}/lib' \
                       ' -DWITH_SFTP=ON' \
                       ' -DWITH_SERVER=ON' \
                       ' -DWITH_STATIC_LIB=ON' \
                       ' -DWITH_GSSAPI=OFF' \
                       ' -DWITH_ZLIB=OFF' \
                       ' -DWITH_PCAP=OFF' \
                       ' -DUNIT_TESTING=OFF' \
                       ' -DWITH_EXAMPLES=OFF' \
                       ' -DWITH_BENCHMARKS=OFF' \
                       ' -DWITH_NACL=OFF' \
                       ' ..'.format(path_release=self.PATH_RELEASE)

        old_p = os.getcwd()
        try:
            utils.cmake(build_path, 'Release', False, cmake_define=cmake_define, cmake_pre_define='CFLAGS="-fPIC"')
            os.chdir(build_path)
            utils.sys_exec('make install')
        except:
            pass
        os.chdir(old_p)

        utils.ensure_file_exists(os.path.join(self.PATH_RELEASE, 'lib', 'libssh.a'))
        files = os.listdir(os.path.join(self.PATH_RELEASE, 'lib'))
        for i in files:
            if i.startswith('libssh.so'):
                # use os.unlink() because some file should be a link.
                os.unlink(os.path.join(self.PATH_RELEASE, 'lib', i))

    def fix_output(self):
        pass


class BuilderMacOS(BuilderBase):
    def __init__(self):
        super().__init__()

    def _init_path(self):
        self.PATH_TMP = os.path.join(PATH_EXTERNAL, 'macos', 'tmp')
        self.PATH_RELEASE = os.path.join(PATH_EXTERNAL, 'macos', 'release')
        self.OPENSSL_PATH_SRC = os.path.join(self.PATH_TMP, 'openssl-OpenSSL_{}'.format(env.ver_ossl.replace('.', '_')))
        self.LIBUV_PATH_SRC = os.path.join(self.PATH_TMP, 'libuv-{}'.format(env.ver_libuv))
        self.MBEDTLS_PATH_SRC = os.path.join(self.PATH_TMP, 'mbedtls-mbedtls-{}'.format(env.ver_mbedtls))
        self.LIBSSH_PATH_SRC = os.path.join(self.PATH_TMP, 'libssh-{}'.format(env.ver_libssh))

        self.JSONCPP_PATH_SRC = os.path.join(PATH_EXTERNAL, 'jsoncpp')
        self.MONGOOSE_PATH_SRC = os.path.join(PATH_EXTERNAL, 'mongoose')

        if not os.path.exists(self.PATH_TMP):
            utils.makedirs(self.PATH_TMP)

    def _build_jsoncpp(self, file_name):
        cc.n('prepare jsoncpp source code...', end='')
        if not os.path.exists(self.JSONCPP_PATH_SRC):
            cc.v('')
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, PATH_EXTERNAL))
            os.rename(os.path.join(PATH_EXTERNAL, 'jsoncpp-{}'.format(env.ver_jsoncpp)), self.JSONCPP_PATH_SRC)
        else:
            cc.w('already exists, skip.')

    def _build_mongoose(self, file_name):
        cc.n('prepare mongoose source code...', end='')
        if not os.path.exists(self.MONGOOSE_PATH_SRC):
            cc.v('')
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, PATH_EXTERNAL))
            os.rename(os.path.join(PATH_EXTERNAL, 'mongoose-{}'.format(env.ver_mongoose)), self.MONGOOSE_PATH_SRC)
        else:
            cc.w('already exists, skip.')

    def _build_openssl(self, file_name):
        if not super()._build_openssl(file_name):
            return

        cc.n('prepare openssl source code...', end='')
        if not os.path.exists(self.OPENSSL_PATH_SRC):
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))
            if not os.path.exists(self.OPENSSL_PATH_SRC):
                raise RuntimeError('can not prepare openssl source code.')
        else:
            cc.w('already exists, skip.')

        cc.n('build openssl static...', end='')
        out_file_lib = os.path.join(self.PATH_RELEASE, 'lib', 'libssl.a')
        if os.path.exists(out_file_lib):
            cc.w('already exists, skip.')
            return
        cc.v('')

        old_p = os.getcwd()
        os.chdir(self.OPENSSL_PATH_SRC)
        # os.system('./config --prefix={} --openssldir={}/openssl no-zlib no-shared'.format(self.PATH_RELEASE, self.PATH_RELEASE))
        # os.system('./Configure darwin64-x86_64-cc')
        os.system('./Configure darwin64-x86_64-cc --prefix={} --openssldir={}/openssl -fPIC no-zlib no-shared'.format(self.PATH_RELEASE, self.PATH_RELEASE))
        os.system('make')
        os.system('make install')
        os.chdir(old_p)

    def _build_libuv(self, file_name):
        cc.n('prepare libuv source code...', end='')
        if not os.path.exists(self.LIBUV_PATH_SRC):
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build libuv...', end='')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libuv.a')):
            cc.w('already exists, skip.')
            return
        cc.v('')

        # we need following...
        # brew install automake libtool

        old_p = os.getcwd()
        os.chdir(self.LIBUV_PATH_SRC)
        os.system('sh autogen.sh')
        os.system('./configure --prefix={} --with-pic'.format(self.PATH_RELEASE))
        os.system('make')
        os.system('make install')
        os.chdir(old_p)

    def _build_mbedtls(self, file_name):
        if not os.path.exists(self.MBEDTLS_PATH_SRC):
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build mbedtls...', end='')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libmbedtls.a')):
            cc.w('already exists, skip.')
            return
        cc.v('')

        # fix the Makefile
        mkfile = os.path.join(self.MBEDTLS_PATH_SRC, 'Makefile')
        f = open(mkfile)
        fl = f.readlines()
        f.close()

        fixed = False
        for i in range(len(fl)):
            x = fl[i].split('=')
            if x[0] == 'DESTDIR':
                fl[i] = 'DESTDIR={}\n'.format(self.PATH_RELEASE)
                fixed = True
                break

        if not fixed:
            cc.e('can not fix Makefile of mbedtls.')
            return

        f = open(mkfile, 'w')
        f.writelines(fl)
        f.close()

        # fix source file
        utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'include', 'mbedtls', 'config.h'))
        utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'include', 'mbedtls'), os.path.join(self.MBEDTLS_PATH_SRC, 'include', 'mbedtls'), 'config.h')
        # utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'library', 'rsa.c'))
        # utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'library'), os.path.join(self.MBEDTLS_PATH_SRC, 'library'), 'rsa.c')

        old_p = os.getcwd()
        os.chdir(self.MBEDTLS_PATH_SRC)
        os.system('make CFLAGS="-fPIC" lib')
        os.system('make install')
        os.chdir(old_p)

    def _build_libssh(self, file_name):
        if not os.path.exists(self.LIBSSH_PATH_SRC):
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build libssh...', end='')
        # if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libssh.a')) and os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libssh_threads.a')):
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libssh.a')):
            cc.w('already exists, skip.')
            return
        cc.v('')

        build_path = os.path.join(self.LIBSSH_PATH_SRC, 'build')

        cmake_define = ' -DCMAKE_INSTALL_PREFIX={path_release}' \
                       ' -DOPENSSL_INCLUDE_DIR={path_release}/include' \
                       ' -DOPENSSL_LIBRARIES={path_release}/lib' \
                       ' -DWITH_SFTP=ON' \
                       ' -DWITH_SERVER=ON' \
                       ' -DWITH_STATIC_LIB=ON' \
                       ' -DWITH_GSSAPI=OFF' \
                       ' -DWITH_ZLIB=OFF' \
                       ' -DWITH_PCAP=OFF' \
                       ' -DUNIT_TESTING=OFF' \
                       ' -DWITH_EXAMPLES=OFF' \
                       ' -DWITH_BENCHMARKS=OFF' \
                       ' -DWITH_NACL=OFF' \
                       ''.format(path_release=self.PATH_RELEASE)

        try:
            utils.cmake(build_path, 'Release', False, cmake_define)
        except:
            pass

        # because make install will fail because we can not disable ssh_shared target,
        # so we copy necessary files ourselves.
        utils.ensure_file_exists(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src', 'libssh.a'))
        # utils.ensure_file_exists(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src', 'threads', 'libssh_threads.a'))
        utils.copy_file(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src'), os.path.join(self.PATH_RELEASE, 'lib'), 'libssh.a')
        # utils.copy_file(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src', 'threads'), os.path.join(self.PATH_RELEASE, 'lib'), 'libssh_threads.a')
        utils.copy_ex(os.path.join(self.LIBSSH_PATH_SRC, 'include'), os.path.join(self.PATH_RELEASE, 'include'), 'libssh')

    def _prepare_python(self):
        pass

    def fix_output(self):
        # remove .so files, otherwise will link to .so but not .a in default.
        # rm = ['libsqlite3.la', 'libsqlite3.so.0', 'libsqlite3.so', 'libsqlite3.so.0.8.6', 'libuv.la', 'libuv.so.1', 'libuv.so', 'libuv.so.1.0.0']
        rm = ['libuv.la', 'libuv.dylib', 'libuv.so.1', 'libuv.so', 'libuv.so.1.0.0']
        for i in rm:
            _path = os.path.join(self.PATH_RELEASE, 'lib', i)
            if os.path.exists(_path):
                utils.remove(_path)


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

    builder.prepare_python()

    builder.build_jsoncpp()
    builder.build_mongoose()
    builder.build_openssl()
    builder.build_libuv()
    builder.build_mbedtls()
    builder.build_libssh()

    builder.fix_output()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        cc.e(e.__str__())
    except:
        cc.f('got exception.')
