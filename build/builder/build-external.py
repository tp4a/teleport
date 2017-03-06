#!/bin/env python3
# -*- coding: utf-8 -*-

import codecs
import shutil
import time
from core import colorconsole as cc
from core import utils
from core.context import *

ctx = BuildContext()

ROOT_PATH = utils.cfg.ROOT_PATH
PATH_EXTERNAL = os.path.join(ROOT_PATH, 'external')
PATH_DOWNLOAD = os.path.join(PATH_EXTERNAL, '_download_')

OPENSSL_VER = utils.cfg.ver.openssl
LIBUV_VER = utils.cfg.ver.libuv
MBEDTLS_VER = utils.cfg.ver.mbedtls
SQLITE_VER = utils.cfg.ver.sqlite


class BuilderBase:
    def __init__(self):
        self.out_dir = ''
        if not os.path.exists(PATH_DOWNLOAD):
            utils.makedirs(PATH_DOWNLOAD)

        self._init_path()

    def _init_path(self):
        cc.e("this is a pure-virtual function.")

    def build_openssl(self):
        file_name = 'openssl-{}.tar.gz'.format(OPENSSL_VER)
        if not self._download_file('openssl source tarball', 'https://www.openssl.org/source/{}'.format(file_name), file_name):
            return
        self._build_openssl(file_name)

    def _build_openssl(self, file_name):
        cc.e("this is a pure-virtual function.")

    def build_libuv(self):
        file_name = 'libuv-{}.zip'.format(LIBUV_VER)
        if not self._download_file('libuv source tarball', 'https://github.com/libuv/libuv/archive/v{}.zip'.format(LIBUV_VER), file_name):
            return
        self._build_libuv(file_name)

    def _build_libuv(self, file_name):
        cc.e("this is a pure-virtual function.")

    def build_mbedtls(self):
        file_name = 'mbedtls-mbedtls-{}.zip'.format(MBEDTLS_VER)
        if not self._download_file('mbedtls source tarball', 'https://github.com/ARMmbed/mbedtls/archive/mbedtls-{}.zip'.format(MBEDTLS_VER), file_name):
            return
        self._build_mbedtls(file_name)

    def _build_mbedtls(self, file_name):
        cc.e("this is a pure-virtual function.")

    def build_libssh(self):
        file_name = 'libssh-master.zip'
        if not self._download_file('mbedtls source tarball', 'https://git.libssh.org/projects/libssh.git/snapshot/master.zip', file_name):
            return
        self._build_libssh(file_name)

    def _build_libssh(self, file_name):
        cc.e("this is a pure-virtual function.")

    def build_sqlite(self):
        file_name = 'sqlite-autoconf-{}.tar.gz'.format(SQLITE_VER)
        if not self._download_file('mbedtls source tarball', 'http://sqlite.org/2016/{}'.format(file_name), file_name):
            return
        self._build_sqlite(file_name)

    def _build_sqlite(self, file_name):
        cc.e("this is a pure-virtual function.")

    def _download_file(self, desc, url, file_name):
        cc.n('downloading {} ...'.format(desc))
        if os.path.exists(os.path.join(PATH_DOWNLOAD, file_name)):
            cc.w('already exists, skip.')
            return True

        os.system('wget --no-check-certificate {} -O "{}/{}"'.format(url, PATH_DOWNLOAD, file_name))

        if not os.path.exists(os.path.join(PATH_DOWNLOAD, file_name)):
            cc.e('downloading {} from {} failed.'.format(desc, url))
            return True

        return True

    def fix_output(self):
        pass

class BuilderWin(BuilderBase):
    def __init__(self):
        super().__init__()

    def _init_path(self):
        cc.e("build external not works for Windows yet.")

    def _build_openssl(self, file_name):
        cc.e('build openssl-static for Windows...not supported yet.')

    def fix_output(self):
        pass


class BuilderLinux(BuilderBase):
    def __init__(self):
        super().__init__()

    def _init_path(self):
        self.PATH_TMP = os.path.join(PATH_EXTERNAL, 'linux', 'tmp')
        self.PATH_RELEASE = os.path.join(PATH_EXTERNAL, 'linux', 'release')
        self.OPENSSL_PATH_SRC = os.path.join(self.PATH_TMP, 'openssl-{}'.format(OPENSSL_VER))
        self.LIBUV_PATH_SRC = os.path.join(self.PATH_TMP, 'libuv-{}'.format(LIBUV_VER))
        self.MBEDTLS_PATH_SRC = os.path.join(self.PATH_TMP, 'mbedtls-mbedtls-{}'.format(MBEDTLS_VER))
        self.LIBSSH_PATH_SRC = os.path.join(self.PATH_TMP, 'libssh-master')
        self.SQLITE_PATH_SRC = os.path.join(self.PATH_TMP, 'sqlite-autoconf-{}'.format(SQLITE_VER))

        if not os.path.exists(self.PATH_TMP):
            utils.makedirs(self.PATH_TMP)

    def _build_openssl(self, file_name):
        if not os.path.exists(self.OPENSSL_PATH_SRC):
            os.system('tar -zxvf "{}/{}" -C "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build openssl static...')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libssl.a')):
            cc.w('already exists, skip.')
            return

        old_p = os.getcwd()
        os.chdir(self.OPENSSL_PATH_SRC)
        #os.system('./config --prefix={} --openssldir={}/openssl no-zlib no-shared'.format(self.PATH_RELEASE, self.PATH_RELEASE))
        os.system('./config --prefix={} --openssldir={}/openssl -fPIC no-zlib no-shared'.format(self.PATH_RELEASE, self.PATH_RELEASE))
        os.system('make')
        os.system('make install')
        os.chdir(old_p)

    def _build_libuv(self, file_name):
        if not os.path.exists(self.LIBUV_PATH_SRC):
            # os.system('tar -zxvf "{}/{}" -C "{}"'.format(PATH_DOWNLOAD, file_name, PATH_TMP))
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build libuv...')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libuv.a')):
            cc.w('already exists, skip.')
            return

        # we need following...
        # apt-get install autoconf aptitude libtool gcc-c++

        old_p = os.getcwd()
        os.chdir(self.LIBUV_PATH_SRC)
        os.system('sh autogen.sh')
        os.system('./configure --prefix={}'.format(self.PATH_RELEASE))
        os.system('make')
        os.system('make install')
        os.chdir(old_p)

    def _build_mbedtls(self, file_name):
        if not os.path.exists(self.MBEDTLS_PATH_SRC):
            # os.system('tar -zxvf "{}/{}" -C "{}"'.format(PATH_DOWNLOAD, file_name, PATH_TMP))
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build mbedtls...')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libmbedtls.a')):
            cc.w('already exists, skip.')
            return

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

        # fix config.h
        mkfile = os.path.join(self.MBEDTLS_PATH_SRC, 'include', 'mbedtls', 'config.h')
        f = open(mkfile)
        fl = f.readlines()
        f.close()

        for i in range(len(fl)):
            if fl[i].find('#define MBEDTLS_KEY_EXCHANGE_ECDHE_PSK_ENABLED') >= 0:
                fl[i] = '//#define MBEDTLS_KEY_EXCHANGE_ECDHE_PSK_ENABLED\n'
            elif fl[i].find('#define MBEDTLS_KEY_EXCHANGE_ECDHE_RSA_ENABLED') >= 0:
                fl[i] = '//#define MBEDTLS_KEY_EXCHANGE_ECDHE_RSA_ENABLED\n'
            elif fl[i].find('#define MBEDTLS_KEY_EXCHANGE_ECDHE_ECDSA_ENABLED') >= 0:
                fl[i] = '//#define MBEDTLS_KEY_EXCHANGE_ECDHE_ECDSA_ENABLED\n'
            elif fl[i].find('#define MBEDTLS_KEY_EXCHANGE_ECDH_ECDSA_ENABLED') >= 0:
                fl[i] = '//#define MBEDTLS_KEY_EXCHANGE_ECDH_ECDSA_ENABLED\n'
            elif fl[i].find('#define MBEDTLS_KEY_EXCHANGE_ECDH_RSA_ENABLED') >= 0:
                fl[i] = '//#define MBEDTLS_KEY_EXCHANGE_ECDH_RSA_ENABLED\n'
            elif fl[i].find('#define MBEDTLS_SELF_TEST') >= 0:
                fl[i] = '//#define MBEDTLS_SELF_TEST\n'
            elif fl[i].find('#define MBEDTLS_SSL_RENEGOTIATION') >= 0:
                fl[i] = '//#define MBEDTLS_SSL_RENEGOTIATION\n'
            elif fl[i].find('#define MBEDTLS_ECDH_C') >= 0:
                fl[i] = '//#define MBEDTLS_ECDH_C\n'
            elif fl[i].find('#define MBEDTLS_ECDSA_C') >= 0:
                fl[i] = '//#define MBEDTLS_ECDSA_C\n'
            elif fl[i].find('#define MBEDTLS_ECP_C') >= 0:
                fl[i] = '//#define MBEDTLS_ECP_C\n'
            elif fl[i].find('#define MBEDTLS_NET_C') >= 0:
                fl[i] = '//#define MBEDTLS_NET_C\n'

            elif fl[i].find('#define MBEDTLS_RSA_NO_CRT') >= 0:
                fl[i] = '#define MBEDTLS_RSA_NO_CRT\n'
            elif fl[i].find('#define MBEDTLS_SSL_PROTO_SSL3') >= 0:
                fl[i] = '#define MBEDTLS_SSL_PROTO_SSL3\n'

        f = open(mkfile, 'w')
        f.writelines(fl)
        f.close()

        # fix source file
        utils.ensure_file_exists(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'library', 'rsa.c'))
        utils.copy_file(os.path.join(PATH_EXTERNAL, 'fix-external', 'mbedtls', 'library'), os.path.join(self.MBEDTLS_PATH_SRC, 'library'), 'rsa.c')

        old_p = os.getcwd()
        os.chdir(self.MBEDTLS_PATH_SRC)
        os.system('make lib')
        os.system('make install')
        os.chdir(old_p)

    def _build_libssh(self, file_name):
        if not os.path.exists(self.LIBSSH_PATH_SRC):
            # os.system('tar -zxvf "{}/{}" -C "{}"'.format(PATH_DOWNLOAD, file_name, PATH_TMP))
            os.system('unzip "{}/{}" -d "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))
            os.rename(os.path.join(self.PATH_TMP, 'master'), os.path.join(self.PATH_TMP, 'libssh-master'))

        cc.n('build libssh...')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libssh.a')):
            cc.w('already exists, skip.')
            return

        build_path = os.path.join(self.LIBSSH_PATH_SRC, 'build')
        # utils.makedirs(build_path)

        # here is a bug in cmake v2.8.11 (default on ubuntu14), in FindOpenSSL.cmake,
        # it parse opensslv.h, use regex like this:
        #   REGEX "^#define[\t ]+OPENSSL_VERSION_NUMBER[\t ]+0x([0-9a-fA-F])+.*")
        # but in openssl-1.0.2h, the version define line is:
        #   # define OPENSSL_VERSION_NUMBER  0x1000208fL
        # notice there is a space char between # and define, so find openssl always fail.

        # old_p = os.getcwd()
        # os.chdir(build_path)
        # cmd = 'cmake' \
        #       ' -DCMAKE_INSTALL_PREFIX={}' \
        #       ' -D_OPENSSL_VERSION={}' \
        #       ' -DOPENSSL_INCLUDE_DIR={}/include' \
        #       ' -DOPENSSL_LIBRARIES={}/lib' \
        #       ' -DCMAKE_BUILD_TYPE=Release' \
        #       ' -DWITH_GSSAPI=OFF' \
        #       ' -DWITH_ZLIB=OFF' \
        #       ' -DWITH_STATIC_LIB=ON' \
        #       ' -DWITH_PCAP=OFF' \
        #       ' -DWITH_EXAMPLES=OFF' \
        #       ' -DWITH_NACL=OFF' \
        #       ' ..'.format(self.PATH_RELEASE, OPENSSL_VER, self.PATH_RELEASE, self.PATH_RELEASE)
        # cc.n(cmd)
        # os.system(cmd)
        # # os.system('make ssh_static ssh_threads_static')
        # os.system('make ssh_static')
        # # os.system('make install')
        # os.chdir(old_p)

        # TODO: need modify the `config.h.cmake` and comment out HAVE_OPENSSL_CRYPTO_CTR128_ENCRYPT.

        cmake_define = ' -DCMAKE_INSTALL_PREFIX={}' \
              ' -D_OPENSSL_VERSION={}' \
              ' -DOPENSSL_INCLUDE_DIR={}/include' \
              ' -DOPENSSL_LIBRARIES={}/lib' \
              ' -DWITH_GSSAPI=OFF' \
              ' -DWITH_ZLIB=OFF' \
              ' -DWITH_STATIC_LIB=ON' \
              ' -DWITH_PCAP=OFF' \
              ' -DWITH_TESTING=OFF' \
              ' -DWITH_CLIENT_TESTING=OFF' \
              ' -DWITH_EXAMPLES=OFF' \
              ' -DWITH_BENCHMARKS=OFF' \
              ' -DWITH_NACL=OFF' \
              ' ..'.format(self.PATH_RELEASE, OPENSSL_VER, self.PATH_RELEASE, self.PATH_RELEASE)

        # libssh always try to build shared library we do not care, but it may fail.
        # so catch the except, we will check the final output file `libssh.a` ourselves.
        try:
            utils.cmake(build_path, 'Release', False, cmake_define)
        except:
            pass

        # because make install will fail because we can not disable ssh_shared target,
        # so we copy necessary files ourselves.
        utils.ensure_file_exists(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src', 'libssh.a'))
        utils.copy_file(os.path.join(self.LIBSSH_PATH_SRC, 'build', 'src'), os.path.join(self.PATH_RELEASE, 'lib'), 'libssh.a')
        utils.copy_ex(os.path.join(self.LIBSSH_PATH_SRC, 'include'), os.path.join(self.PATH_RELEASE, 'include'), 'libssh')

    def _build_sqlite(self, file_name):
        if not os.path.exists(self.SQLITE_PATH_SRC):
            os.system('tar -zxvf "{}/{}" -C "{}"'.format(PATH_DOWNLOAD, file_name, self.PATH_TMP))

        cc.n('build sqlite static...')
        if os.path.exists(os.path.join(self.PATH_RELEASE, 'lib', 'libsqlite3.a')):
            cc.w('already exists, skip.')
            return

        old_p = os.getcwd()
        os.chdir(self.SQLITE_PATH_SRC)
        os.system('./configure --prefix={}'.format(self.PATH_RELEASE))
        os.system('make')
        os.system('make install')
        os.chdir(old_p)

    def fix_output(self):
        # remove .so files, otherwise eom_ts will link to .so but not .a in default.
        rm = ['libsqlite3.la', 'libsqlite3.so.0', 'libuv.la', 'libuv.so.1', 'libsqlite3.so', 'libsqlite3.so.0.8.6', 'libuv.so', 'libuv.so.1.0.0']
        for i in rm:
            _path = os.path.join(self.PATH_RELEASE, 'lib', i)
            if os.path.exists(_path):
                utils.remove(_path)


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

    # builder.build_openssl()
    ####builder.build_libuv()
    builder.build_mbedtls()
    builder.build_libssh()
    builder.build_sqlite()

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
