# -*- coding: utf-8 -*-

import os
import sys
import time
import stat
from core.env import env
import core.colorconsole as cc
import core.utils as utils


class InstallerBase:
    def __init__(self):
        self._all_ok = True
        self._err_msg = list()

        self._is_installed = False
        self._install_path = ''
        self._config_path = ''
        self._data_path = ''
        self._log_path = ''

        self._installed_ver_str = 'UNKNOWN'
        self._current_ver = 'UNKNOWN'

        self._def_install_path = ''

        ver_file = os.path.join(env.root_path, 'data', 'www', 'teleport', 'webroot', 'app', 'app_ver.py')
        try:
            with open(ver_file, 'r') as f:
                x = f.readlines()
                for i in x:
                    s = i.split('=', 1)
                    if 'TP_SERVER_VER' == s[0].strip():
                        self._current_ver = s[1].strip()[1:-1]
                        break
        except FileNotFoundError:
            raise RuntimeError('Cannot detect installer version.')

    def _init(self):
        _width = 79
        cc.v('')
        cc.v('[]{}[]'.format('=' * (_width - 4)))
        _str = 'Teleport Server Installation'
        cc.o((cc.CR_VERBOSE, ' | '), (cc.CR_VERBOSE, _str), (cc.CR_VERBOSE, '{}|'.format(' ' * (_width - 5 - len(_str)))))
        cc.v(' |{}|'.format('=' * (_width - 4)))
        cc.o((cc.CR_VERBOSE, ' |    ver: '), (cc.CR_ERROR, self._current_ver),
             (cc.CR_VERBOSE, '{}|'.format(' ' * (_width - 13 - len(self._current_ver)))))
        _str = 'author: apex.liu@qq.com'
        cc.v(' | {}{}|'.format(_str, ' ' * (_width - 5 - len(_str))))
        cc.v('[]{}[]'.format('=' * (_width - 4)))
        cc.v('')
        cc.v('Welcome to install Teleport Server!')
        cc.v('')
        cc.o((cc.CR_VERBOSE,
              'NOTICE: There are a few steps need you enter information or make choice,\n'
              '        if you want to use the DEFAULT choice, just press `Enter` key.'))
        cc.o((cc.CR_VERBOSE, '        Otherwise you need enter the '), (cc.CR_ERROR, 'highlight character'),
             (cc.CR_VERBOSE, ' to make choice.'))
        cc.v('')
        cc.v('')

        cc.v('Prepare installation...')
        self._check_installation()
        self._check_installation_ver()
        cc.v('')

    def run(self):
        self._init()

        if not self._is_installed:
            self._do_install()
        else:
            cc.v('')
            cc.v('Found teleport server have installed at `{}` already.'.format(self._install_path))
            while True:
                x = self._prompt_choice('What are you wanna to do?',
                                        [('upgrade', 2, True), ('uninstall', 0, False), ('quit', 0, False)])
                if x in ['q', 'quit']:
                    break
                elif x in ['u', 'uninstall']:
                    self._do_uninstall()
                    break
                elif x in ['g', 'upgrade']:
                    self._do_upgrade()
                    break

    def _do_install(self):
        while True:
            cc.v('')
            self._install_path = self._prompt_input('Set installation path', self._def_install_path)
            _use_anyway = False
            if os.path.exists(self._install_path):
                while True:
                    cc.v('')
                    x = self._prompt_choice(
                        'The target path `{}` has already exists,\ndo you want to use it anyway?'.format(
                            self._install_path), [('Yes', 0, True), ('No', 0, False)])
                    if x in ['y', 'yes']:
                        _use_anyway = True
                        break
                    elif x in ['n', 'no']:
                        break

                if _use_anyway:
                    break
            else:
                break

        self._fix_path()

        utils.make_dirs(self._install_path)
        self._copy_files()
        self._install_service()
        self._start_service()
        time.sleep(2)
        self._check_service()

    def _do_uninstall(self):
        if not self._is_installed:
            return

        _del_settings = False
        while True:
            cc.v('')
            x = self._prompt_choice('Do you want to keep your database and settings?',
                                    [('Yes', 0, True), ('No', 0, False)])
            if x in ['y', 'yes']:
                break
            elif x in ['n', 'no']:
                _del_settings = True
                break

        if _del_settings:
            while True:
                cc.v('')
                x = self._prompt_choice('Seriously!! Are you sure to remove all data and settings?',
                                        [('Yes', 0, False), ('No', 0, True)])
                if x in ['y', 'yes']:
                    break
                elif x in ['n', 'no']:
                    _del_settings = False
                    break

        self._stop_service()
        time.sleep(2)
        self._uninstall_service()
        self._delete_files(_del_settings)

    def _do_upgrade(self):
        x = self._ver_compare(self._current_ver, self._installed_ver_str)
        if x == 0:
            while True:
                cc.v('')
                x = self._prompt_choice(
                    'The same version `{}` installed, are you sure to overwrite?'.format(self._current_ver),
                    [('Yes', 0, False), ('No', 0, True)])
                if x in ['y', 'yes']:
                    break
                elif x in ['n', 'no']:
                    return
        elif x < 0:
            while True:
                cc.v('')
                x = self._prompt_choice(
                    'A new version `{}` installed, rollback to old version `{}` may cause Teleport Server not functionally.\nAre you sure to rollback to old version?'.format(
                        self._installed_ver_str, self._current_ver), [('Yes', 0, False), ('No', 0, True)])
                if x in ['y', 'yes']:
                    break
                elif x in ['n', 'no']:
                    return
        else:
            while True:
                cc.v('')
                x = self._prompt_choice(
                    'Now upgrade from version `{}` to `{}`, \nAre you sure to upgrade to new version?'.format(
                        self._installed_ver_str, self._current_ver), [('Yes', 0, False), ('No', 0, True)])
                if x in ['y', 'yes']:
                    break
                elif x in ['n', 'no']:
                    return

        while True:
            cc.v('')
            x = self._prompt_choice('Make sure you have backup your database and settings.\nAre you sure to continue?',
                                    [('Yes', 0, False), ('No', 0, True)])
            x = x.lower()
            if x in ['y', 'yes']:
                break
            elif x in ['n', 'yes']:
                return

        self._stop_service()
        time.sleep(2)
        self._uninstall_service()
        self._delete_files(False)
        time.sleep(1)
        self._copy_files()
        self._install_service()
        self._start_service()
        time.sleep(2)
        self._check_service()

    @staticmethod
    def _prompt_choice(message, choices):
        cc.v('{} ['.format(message), end='')

        def_choice = ''

        for i in range(len(choices)):
            if i > 0:
                cc.v('/', end='')
            msg = choices[i][0]
            idx = choices[i][1]
            if choices[i][2]:
                msg = msg.upper()
                def_choice = msg[idx]
                cc.v(msg[:idx], end='')
                cc.e(msg[idx], end='')
                cc.v(msg[idx + 1:], end='')
            else:
                msg = msg.lower()
                cc.v(msg[:idx], end='')
                cc.e(msg[idx], end='')
                cc.v(msg[idx + 1:], end='')

        cc.v(']: ', end='')
        try:
            x = input().strip()
            if len(x) == 0:
                x = def_choice
        except EOFError:
            x = def_choice

        return x.lower()

    @staticmethod
    def _prompt_input(message, def_value):
        cc.v('{} ['.format(message), end='')

        cc.w(def_value, end='')
        cc.v(']: ', end='')
        try:
            x = input().strip()
            if len(x) == 0:
                x = def_value
        except EOFError:
            x = def_value

        return x

    @staticmethod
    def _ver_compare(left, right):
        l = left.split('.')
        r = right.split('.')

        len_l = len(l)
        len_r = len(r)

        if len_l < len_r:
            for i in range(len_r - len_l):
                l.append('0')
        elif len_l > len_r:
            for i in range(len_l - len_r):
                r.append('0')

        cnt = len(l)
        for i in range(cnt):
            if int(l[i]) < int(r[i]):
                return -1
            elif int(l[i]) > int(r[i]):
                return 1

        return 0

    def _check_installation(self):
        raise RuntimeError('`check_installation` not implement.')

    def _check_installation_ver(self):
        if not self._is_installed:
            return

        # try to get the installed version from www/teleport/app/eom_ver.py
        cc.o(' - check installed version ... ', end='')
        ver_file = os.path.join(self._install_path, 'www', 'teleport', 'webroot', 'app', 'app_ver.py')
        try:
            with open(ver_file) as f:
                x = f.readlines()
                for i in x:
                    s = i.split('=', 1)
                    if 'TP_SERVER_VER' == s[0].strip():
                        self._installed_ver_str = s[1].strip()[1:-1]
                        cc.i('[{}]'.format(self._installed_ver_str))
                        # self._installed_ver = self._ver_str_to_ver(self._installed_ver_str)
                        break
        except FileNotFoundError:
            cc.e('[failed]')
            cc.e('   the installation maybe broken')

    def _fix_path(self):
        raise RuntimeError('`_fix_path` not implement.')

    def _copy_files(self):
        raise RuntimeError('`copy_files` not implement.')

    def _delete_files(self, del_settings):
        raise RuntimeError('`delete_files` not implement.')

    def _install_service(self):
        raise RuntimeError('`install_service` not implement.')

    def _start_service(self):
        raise RuntimeError('`start_service` not implement.')

    def _stop_service(self):
        raise RuntimeError('`stop_service` not implement.')

    def _uninstall_service(self):
        raise RuntimeError('`uninstall_service` not implement.')

    def _check_service(self):
        raise RuntimeError('`check_service` not implement.')


class InstallerWin(InstallerBase):
    def __init__(self):
        super().__init__()
        self._core_service_name = 'Teleport Core Service'
        self._web_service_name = 'Teleport Web Service'
        self._old_core_service_name = 'EOM Teleport Core Service'
        self._old_web_service_name = 'EOM Teleport Web Service'

        self._def_install_path = r'{}\teleport-server'.format(os.environ['SystemDrive'])

    def _get_service_exec(self, service_name):
        _err, _ = utils.sys_exec(r'sc query "{}"'.format(service_name))
        if 1060 == _err:
            return None
        else:
            _err, _o = utils.sys_exec(r'sc qc "{}"'.format(service_name))
            if _err != 0:
                raise RuntimeError('Can not get execute file path of service `{}`.'.format(service_name))
            for i in _o:
                _x = i.split(':', 1)
                if 'BINARY_PATH_NAME' == _x[0].strip():
                    _path = _x[1].strip()
                    return _path

        return None

    def _check_installation(self):
        cc.o(' - check local installation ... ', end='')

        _check_service_name = [self._old_core_service_name, self._old_web_service_name, self._core_service_name,
                               self._web_service_name]
        for _service_name in _check_service_name:
            _exec_file = self._get_service_exec(_service_name)
            if _exec_file is not None:
                self._is_installed = True
                self._install_path = os.path.abspath(os.path.join(os.path.dirname(_exec_file), '..'))
                break

        if self._is_installed:
            cc.i('[{}]'.format(self._install_path))
            self._fix_path()
        else:
            cc.i('[not exists]')
            return

    def _fix_path(self):
        self._data_path = os.path.join(self._install_path, 'data')
        self._config_path = os.path.join(self._data_path, 'etc')
        self._log_path = os.path.join(self._data_path, 'log')

    def _copy_files(self):
        utils.copy_ex(os.path.join(env.src_path, 'bin'), os.path.join(self._install_path, 'bin'))
        utils.copy_ex(os.path.join(env.src_path, 'www'), os.path.join(self._install_path, 'www'))

        if not os.path.exists(self._config_path):
            utils.copy_ex(os.path.join(env.src_path, 'tmp', 'etc'), self._config_path)

    def _delete_files(self, del_settings):
        utils.remove(os.path.join(self._install_path, 'bin'))
        utils.remove(os.path.join(self._install_path, 'www'))
        if del_settings:
            utils.remove(self._data_path)
            # utils.remove(self._config_path)
            # utils.remove(self._log_path)

            # only remove the installation path when it empty.
            try:
                os.rmdir(self._install_path)
            except OSError:
                pass

    def _install_service(self):
        cc.o(' - install teleport core service ... ', end='')
        _core = os.path.join(self._install_path, 'bin', 'tp_core.exe')
        _err, _ = utils.sys_exec(r'"{}" -i'.format(_core))
        if _err == 0 or _err == 1:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Install core service failed. error code: {}'.format(_err))

        cc.o(' - install teleport web service ... ', end='')
        _core = os.path.join(self._install_path, 'bin', 'tp_web.exe')
        _err, _ = utils.sys_exec(r'"{}" -i'.format(_core))
        if _err == 0 or _err == 1:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Install web service failed. error code: {}'.format(_err))

        return True

    def _start_service(self):
        cc.o(' - start teleport core service ... ', end='')
        _err, _o = utils.sys_exec(r'sc start "{}"'.format(self._core_service_name))
        # print('start core', _err, _o)
        if _err == 0:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Can not start core service.')

        cc.o(' - start teleport web service ...', end='')
        _err, _ = utils.sys_exec(r'sc start "{}"'.format(self._web_service_name))
        if _err == 0:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Can not start web service.')

    def _stop_service(self):
        _check_service_name = [self._old_core_service_name, self._old_web_service_name, self._core_service_name,
                               self._web_service_name]

        for _service_name in _check_service_name:
            cc.o(' - stop service [{}] ... '.format(_service_name), end='')
            _err, _ = utils.sys_exec(r'sc stop "{}"'.format(_service_name))
            if _err == 1060 or _err == 1062 or _err == 0:
                cc.i('[done]')
            elif _err == 1072:
                cc.e('[failed]')
                raise RuntimeError('can not stop service [{}]. please close Service Manager and try again.'.format(_service_name))
            else:
                cc.e('[failed]')
                raise RuntimeError('can not stop service [{}].'.format(_service_name))

    def _uninstall_service(self):
        _check_service_name = [self._old_core_service_name, self._old_web_service_name, self._core_service_name,
                               self._web_service_name]

        for _service_name in _check_service_name:
            cc.o(' - remove service [{}] ... '.format(_service_name), end='')
            _err, _ = utils.sys_exec(r'sc delete "{}"'.format(_service_name))
            if _err == 1060 or _err == 0:
                cc.i('[done]')
            elif _err == 1072:
                cc.e('[failed]')
                raise RuntimeError('can not remove service [{}]. please close Service Manager and try again.'.format(_service_name))
            else:
                cc.e('[failed]')
                raise RuntimeError('can not remove service [{}].'.format(_service_name))

    def _check_service(self):
        cc.o(' - check teleport core service status ... ', end='')
        _err, _o = utils.sys_exec(r'sc query "{}"'.format(self._core_service_name))
        if _err == 1060 or _err == 0:
            cc.i('[running]')
        else:
            cc.e('[not running]')

        cc.o(' - check teleport web service status ... ', end='')
        _err, _o = utils.sys_exec(r'sc query "{}"'.format(self._web_service_name))
        if _err == 1060 or _err == 0:
            cc.i('[running]')
        else:
            cc.e('[not running]')


class InstallerLinux(InstallerBase):
    def __init__(self):
        super().__init__()
        self._def_install_path = '/usr/local/teleport'

    def _check_installation(self):
        cc.o(' - check local installation ... ', end='')

        # old version, the daemon named `eom_ts`.
        # from 2.0.0.1, the daemon rename to `teleport`.
        # we must check both.
        if os.path.exists('/etc/init.d/eom_ts'):
            self._is_installed = True
            self._install_path = '/usr/local/eom/teleport'
            # self._fix_path()
        elif os.path.exists('/etc/init.d/teleport'):
            self._is_installed = True
            self._install_path = '/usr/local/teleport'
            # self._fix_path()

        if self._is_installed:
            cc.i('[{}]'.format(self._install_path))
            self._fix_path()
        else:
            cc.i('[not exists]')
            return

    def _fix_path(self):
        # self._config_path = '/etc/teleport'
        # self._data_path = os.path.join('/var/lib/teleport')
        # self._log_path = os.path.join('/var/log/teleport')
        self._data_path = os.path.join(self._install_path, 'data')
        self._config_path = os.path.join(self._data_path, 'etc')
        self._log_path = os.path.join(self._data_path, 'log')

    def _copy_files(self):
        utils.copy_ex(os.path.join(env.src_path, 'bin'), os.path.join(self._install_path, 'bin'))
        utils.copy_ex(os.path.join(env.src_path, 'www'), os.path.join(self._install_path, 'www'))

        if not os.path.exists(self._config_path):
            utils.copy_ex(os.path.join(env.src_path, 'tmp', 'etc'), self._config_path)

    def _delete_files(self, del_settings):
        utils.remove(os.path.join(self._install_path, 'bin'))
        utils.remove(os.path.join(self._install_path, 'www'))

        utils.remove(os.path.join(self._install_path, 'start.sh'))
        utils.remove(os.path.join(self._install_path, 'stop.sh'))
        utils.remove(os.path.join(self._install_path, 'status.sh'))

        # only remove the installation path when it empty.
        try:
            os.rmdir(self._install_path)
        except OSError:
            pass  # maybe the install path not empty.

        if del_settings:
            utils.remove(self._data_path)
            # utils.remove(self._config_path)
            # utils.remove(self._log_path)

    def _install_service(self):
        daemon_files = [
            ['daemon.in', '/etc/init.d/teleport'],
            ['start.sh.in', os.path.join(self._install_path, 'start.sh')],
            ['stop.sh.in', os.path.join(self._install_path, 'stop.sh')],
            ['status.sh.in', os.path.join(self._install_path, 'status.sh')],
        ]

        for _d in daemon_files:
            cc.v('process [{}] to [{}]'.format(_d[0], _d[1]))
            _orig_file = os.path.join(env.root_path, 'daemon', _d[0])
            with open(_orig_file, 'r') as f:
                _text = f.read()
                _text = _text.format(daemon_path=self._install_path)

            with open(_d[1], 'w') as f:
                f.write(_text)

            if not os.path.exists(_d[1]):
                raise RuntimeError('can not generate daemon file [{}].'.format(_d[1]))

            # owner: RWX, group: RX, others: RX
            os.chmod(_d[1], stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

        # create symbolic link
        os.symlink('/etc/init.d/teleport', '/etc/rc2.d/S50teleport')
        os.symlink('/etc/init.d/teleport', '/etc/rc3.d/S50teleport')
        os.symlink('/etc/init.d/teleport', '/etc/rc4.d/S50teleport')
        os.symlink('/etc/init.d/teleport', '/etc/rc5.d/S50teleport')

    def _start_service(self):
        cc.v('')
        cc.o('start services...')
        _ret, _ = utils.sys_exec('/etc/init.d/teleport start', direct_output=True)
        if _ret != 0:
            raise RuntimeError('not all services started.')

    def _stop_service(self):
        cc.o(' - stop teleport core service ... ', end='')

        # old version, the daemon named `eom_ts`.
        if os.path.exists('/etc/init.d/eom_ts'):
            utils.sys_exec('/etc/init.d/eom_ts stop')
        # from 2.0.0.1, the daemon rename to `teleport`.
        if os.path.exists('/etc/init.d/teleport'):
            utils.sys_exec('/etc/init.d/teleport stop')

        cc.i('[done]')

    def _uninstall_service(self):
        # old version, the daemon named `eom_ts`.
        utils.remove('/etc/init.d/eom_ts')
        utils.remove('/etc/rc2.d/S50eom_ts')
        utils.remove('/etc/rc3.d/S50eom_ts')
        utils.remove('/etc/rc4.d/S50eom_ts')
        utils.remove('/etc/rc5.d/S50eom_ts')
        # from 2.0.0.1, the daemon rename to `teleport`.
        utils.remove('/etc/init.d/teleport')
        utils.remove('/etc/rc2.d/S50teleport')
        utils.remove('/etc/rc3.d/S50teleport')
        utils.remove('/etc/rc4.d/S50teleport')
        utils.remove('/etc/rc5.d/S50teleport')

    def _check_service(self):
        cc.v('')
        cc.o('check services status...')
        utils.sys_exec('/etc/init.d/teleport status', direct_output=True)


def _main():
    cc.set_default(sep='', end='\n')
    env.init()

    if env.is_win:
        _installer = InstallerWin()
    elif env.is_linux:
        _installer = InstallerLinux()
    else:
        raise RuntimeError('Sorry, teleport server does not support this platform yet.')

    _installer.run()


def main():
    try:
        _main()
        cc.v('\n--==[ ALL DONE ]==--\n')
        return 0
    except KeyboardInterrupt:
        return 1
    except RuntimeError as err:
        cc.v('')
        cc.v('')
        cc.e(err.__str__())
        cc.v('')
        return 2
    except:
        cc.f('got exception.')
        return 3


if __name__ == '__main__':
    main()
