# -*- coding: utf-8 -*-

import os
import sys
import time
from core.env import env
import core.colorconsole as cc
import core.utils as utils

WIN_CORE_SERVICE_NAME = 'EOM Teleport Core Service'
WIN_WEB_SERVICE_NAME = 'EOM Teleport Web Service'


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

        ver_file = os.path.join(env.root_path, 'data', 'www', 'teleport', 'app', 'eom_ver.py')
        try:
            with open(ver_file, 'r') as f:
                x = f.readlines()
                for i in x:
                    s = i.split('=', 1)
                    if 'TS_VER' == s[0].strip():
                        self._current_ver = s[1].strip()[1:-1]
                        break
        except FileNotFoundError:
            raise RuntimeError('Cannot detect installer version.')

    def init(self):
        _width = 79
        cc.v('')
        cc.v('[]{}[]'.format('=' * (_width - 4)))
        _str = 'Teleport Server Installation'
        cc.o((cc.CR_VERBOSE, ' | '), (cc.CR_INFO, _str), (cc.CR_VERBOSE, '{}|'.format(' ' * (_width - 5 - len(_str)))))
        cc.v(' |{}|'.format('=' * (_width - 4)))
        cc.o((cc.CR_VERBOSE, ' |    ver: '), (cc.CR_NORMAL, self._current_ver), (cc.CR_VERBOSE, '{}|'.format(' ' * (_width - 13 - len(self._current_ver)))))
        _str = 'author: apexliu@eomsoft.net'
        cc.v(' | {}{}|'.format(_str, ' ' * (_width - 5 - len(_str))))
        cc.v('[]{}[]'.format('=' * (_width - 4)))
        cc.v('')
        cc.v('Welcome to install Teleport Server!')
        cc.v('')
        # cc.v('  NOTICE: if you want to use the default settings, just press `Enter`...')
        cc.o((cc.CR_VERBOSE, 'NOTICE: There are a few steps need you enter information or make choice,\n        if you want to use the '), (cc.CR_WARN, 'default settings'), (cc.CR_VERBOSE, ', just press `Enter` key.'))
        cc.o((cc.CR_VERBOSE, '        Otherwise you need enter the '), (cc.CR_NORMAL, 'highlight character'), (cc.CR_VERBOSE, ' to make choice.'))
        cc.v('')
        cc.v('')

        cc.v('Prepare installation...')
        self._check_installation()
        self._check_installation_ver()
        cc.v('')

    def run(self):
        if not self._is_installed:
            self.install()
        else:
            cc.v('')
            cc.v('Found teleport server have installed at `{}` already.'.format(self._install_path))
            while True:
                x = self._prompt_choice('What are you wanna to do?', [('upgrade', 2, True), ('uninstall', 0, False), ('quit', 0, False)])
                x = x.lower()
                if 'q' == x:
                    return
                elif 'u' == x:
                    self.uninstall()
                    return
                elif 'g' == x:
                    self._upgrade()
                    return

    def install(self):
        while True:
            cc.v('')
            self._install_path = self._prompt_input('Set installation path', self._def_install_path)
            _use_always = False
            if os.path.exists(self._install_path):
                while True:
                    cc.v('')
                    x = self._prompt_choice('The target path `{}` has already exists,\ndo you want to use it anyway?'.format(self._install_path), [('Yes', 0, True), ('No', 0, False)])
                    x = x.lower()
                    if 'y' == x:
                        _use_always = True
                        break
                    elif 'n' == x:
                        break

                if _use_always:
                    break
            else:
                break

        self._config_path = os.path.join(self._install_path, 'etc')
        self._data_path = os.path.join(self._install_path, 'data')
        self._log_path = os.path.join(self._install_path, 'log')

        utils.makedirs(self._install_path)
        self._copy_files()
        self._install_service()
        self._start_service()
        time.sleep(2)
        self._check_service()

        cc.v('\nall done..')

    def uninstall(self):
        if not self._is_installed:
            return

        _del_settings = False
        while True:
            cc.v('')
            x = self._prompt_choice('Do you want to keep your database and settings?', [('Yes', 0, True), ('No', 0, False)])
            x = x.lower()
            if 'y' == x:
                break
            elif 'n' == x:
                _del_settings = True
                break

        if _del_settings:
            while True:
                cc.v('')
                x = self._prompt_choice('Seriously!! Are you sure to remove all data and settings?', [('Yes', 0, False), ('No', 0, True)])
                x = x.lower()
                if 'y' == x:
                    break
                elif 'n' == x:
                    _del_settings = False
                    break

        self._stop_service()
        time.sleep(2)
        self._uninstall_service()
        self._delete_files(_del_settings)

        cc.v('\nall done..')
        pass

    def _upgrade(self):
        x = self._ver_compare(self._current_ver, self._installed_ver_str)
        if x == 0:
            while True:
                cc.v('')
                x = self._prompt_choice('The same version `{}` installed, are you sure to overwrite?'.format(self._current_ver), [('Yes', 0, False), ('No', 0, True)])
                x = x.lower()
                if 'y' == x:
                    break
                elif 'n' == x:
                    return
        elif x < 0:
            while True:
                cc.v('')
                x = self._prompt_choice('A new version `{}` installed, rollback to old version `{}` may cause Teleport Server not functionally.\nAre you sure to rollback to old version?'.format(self._installed_ver_str, self._current_ver), [('Yes', 0, False), ('No', 0, True)])
                x = x.lower()
                if 'y' == x:
                    break
                elif 'n' == x:
                    return
        else:
            while True:
                cc.v('')
                x = self._prompt_choice('Now upgrade from version `{}` to `{}`, \nAre you sure to upgrade to new version?'.format(self._installed_ver_str, self._current_ver), [('Yes', 0, False), ('No', 0, True)])
                x = x.lower()
                if 'y' == x:
                    break
                elif 'n' == x:
                    return

        while True:
            cc.v('')
            x = self._prompt_choice('Make sure you have backup your database and settings.\nAre you sure to continue?', [('Yes', 0, False), ('No', 0, True)])
            x = x.lower()
            if 'y' == x:
                break
            elif 'n' == x:
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

        cc.v('All done.')

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
                def_choice = msg[idx].lower()
                cc.w(msg[:idx], end='')
                cc.n(msg[idx], end='')
                cc.w(msg[idx + 1:], end='')
            else:
                msg = msg.lower()
                cc.v(msg[:idx], end='')
                cc.n(msg[idx], end='')
                cc.v(msg[idx + 1:], end='')

        cc.v(']: ', end='')
        try:
            x = input().strip()
            if len(x) == 0:
                x = def_choice
        except EOFError:
            x = def_choice

        return x

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
            if int(l[i] < r[i]):
                return -1
            elif int(l[i] > r[i]):
                return 1

        return 0

    def _check_installation(self):
        pass

    def _check_installation_ver(self):
        if not self._is_installed:
            return

        # try to get the installed version from www/teleport/app/eom_ver.py
        cc.v(' - check installed version ... ', end='')
        ver_file = os.path.join(self._install_path, 'www', 'teleport', 'app', 'eom_ver.py')
        try:
            with open(ver_file) as f:
                x = f.readlines()
                for i in x:
                    s = i.split('=', 1)
                    if 'TS_VER' == s[0].strip():
                        self._installed_ver_str = s[1].strip()[1:-1]
                        cc.i('[{}]'.format(self._installed_ver_str))
                        # self._installed_ver = self._ver_str_to_ver(self._installed_ver_str)
                        break
        except FileNotFoundError:
            cc.e('[failed]')
            cc.e('   the installation maybe broken')

    def _copy_files(self):
        pass

    def _delete_files(self, del_settings):
        pass

    def _install_service(self):
        pass

    def _start_service(self):
        pass

    def _stop_service(self):
        pass

    def _uninstall_service(self):
        pass

    def _check_service(self):
        pass


class InstallerWin(InstallerBase):
    def __init__(self):
        super().__init__()
        self._def_install_path = r'{}\teleport-server'.format(os.environ['SystemDrive'])

    def _check_installation(self):
        cc.o(' - check local installation ... ', end='')
        _err, _ = utils.sys_exec(r'sc query "{}"'.format(WIN_CORE_SERVICE_NAME))
        if 1060 == _err:
            # core service not install
            pass
        else:
            self._is_installed = True
            _err, _o = utils.sys_exec(r'sc qc "{}"'.format(WIN_CORE_SERVICE_NAME))
            if _err != 0:
                raise RuntimeError('Can not get core service installation information.')
            for i in _o:
                _x = i.split(':', 1)
                if 'BINARY_PATH_NAME' == _x[0].strip():
                    _path = _x[1].strip()
                    self._install_path = os.path.abspath(os.path.join(os.path.dirname(_path), '..'))
                    break

        _err, _ = utils.sys_exec(r'sc query "{}"'.format(WIN_WEB_SERVICE_NAME))
        if 1060 == _err:
            # web service not install.
            pass
        else:
            self._is_installed = True
            _err, _o = utils.sys_exec(r'sc qc "{}"'.format(WIN_WEB_SERVICE_NAME))
            if _err != 0:
                raise RuntimeError('Can not get web service installation information.')
            for i in _o:
                _x = i.split(':', 1)
                if 'BINARY_PATH_NAME' == _x[0].strip():
                    _path = _x[1].strip()
                    self._install_path = os.path.abspath(os.path.join(os.path.dirname(_path), '..'))
                    break

        if self._is_installed:
            cc.i('[exists]')
            self._config_path = os.path.join(self._install_path, 'etc')
            self._data_path = os.path.join(self._install_path, 'data')
            self._log_path = os.path.join(self._install_path, 'log')
        else:
            cc.i('[not exists]')
            return

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
            utils.remove(self._config_path)
            utils.remove(self._log_path)

            # only remove the installation path when it empty.
            os.rmdir(self._install_path)

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
        _err, _o = utils.sys_exec(r'sc start "{}"'.format(WIN_CORE_SERVICE_NAME))
        # print('start core', _err, _o)
        if _err == 0:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Can not start core service.')

        cc.o(' - start teleport web service ...', end='')
        _err, _o = utils.sys_exec(r'sc start "{}"'.format(WIN_WEB_SERVICE_NAME))
        # print('start web', _err, _o)
        if _err == 0:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Can not start web service.')

    def _stop_service(self):
        cc.o(' - stop teleport core service ... ', end='')
        _err, _o = utils.sys_exec(r'sc stop "{}"'.format(WIN_CORE_SERVICE_NAME))
        # print('stop core', _err, _o)
        if _err == 1060 or _err == 1062 or _err == 0:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Can not stop core service.')

        cc.o(' - stop teleport web service ... ', end='')
        _err, _o = utils.sys_exec(r'sc stop "{}"'.format(WIN_WEB_SERVICE_NAME))
        # print('stop web', _err, _o)
        if _err == 1060 or _err == 1062 or _err == 0:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Can not stop web service.')

    def _uninstall_service(self):
        cc.o(' - delete teleport core service ... ', end='')
        _err, _o = utils.sys_exec(r'sc delete "{}"'.format(WIN_CORE_SERVICE_NAME))
        # print('del core', _err, _o)
        if _err == 1060 or _err == 0:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Can not uninstall core service.')

        cc.o(' - delete teleport web service ... ', end='')
        _err, _o = utils.sys_exec(r'sc delete "{}"'.format(WIN_WEB_SERVICE_NAME))
        # print('del web', _err, _o)
        if _err == 1060 or _err == 0:
            cc.i('[done]')
        else:
            cc.e('[failed]')
            raise RuntimeError('Can not uninstall web service.')

    def _check_service(self):
        cc.o(' - check teleport core service status ... ', end='')
        _err, _o = utils.sys_exec(r'sc query "{}"'.format(WIN_CORE_SERVICE_NAME))
        # print('chk core', _err, _o)
        if _err == 1060 or _err == 0:
            cc.i('[running]')
        else:
            cc.e('[not running]')

        cc.o(' - check teleport web service status ... ', end='')
        _err, _o = utils.sys_exec(r'sc delete "{}"'.format(WIN_WEB_SERVICE_NAME))
        # print('chk web', _err, _o)
        if _err == 1060 or _err == 0:
            cc.i('[running]')
        else:
            cc.e('[not running]')


class InstallerLinux(InstallerBase):
    def __init__(self):
        super().__init__()
        self._is_installed = False
        self._install_path = ''

        if env.is_win:
            self._def_install_path = r'{}\teleport-server'.format(os.environ['SystemDrive'])
            self._check_installation = self._check_installation_win
            self._copy_files = self._copy_files_win
            self._install_service = self._install_service_win
            self._stop_service = self._stop_service_win
            self._delete_service = self._delete_service_win
        else:
            self._def_install_path = r'/usr/local/eom/teleport'
            self._check_installation = self._check_installation_linux
            self._copy_files = self._copy_files_linux
            self._install_service = self._install_service_linux
            self._stop_service = self._stop_service_linux
            self._delete_service = self._delete_service_linux

        self._check_installation()

    def init(self):
        pass
        # check if teleport server installed or not.

    def run(self):
        cc.v('')
        cc.v('Welcome to install Teleport Server for Windows!')
        if not self._is_installed:
            self.install()
        else:
            cc.v('')
            cc.v('Found teleport server already installed, now what are you want to do?')
            while True:
                x = self._prompt_choice('Please choice', [('Upgrade', 2, True), ('Uninstall', 0, False), ('Quit', 0, False)])
                x = x.lower()
                if 'q' == x:
                    return
                elif 'u' == x:
                    self.uninstall()
                    return
                elif 'g' == x:
                    self._upgrade()
                    return

    def install(self):
        cc.n('Notice: if you want to use the default settings, just press `Enter`...')
        cc.v('')
        self._install_path = self._prompt_input('Set installation path', self._def_install_path)

        utils.makedirs(self._install_path)
        # self._copy_files()
        self._install_service()

        pass
        # if self._check_installation():
        #     self._install()

    def uninstall(self):
        if not self._is_installed:
            return

        self._stop_service()
        self._delete_service()

        cc.e('uninstall not implemented.')
        pass

    def _upgrade(self):
        cc.e('upgrade not implemented.')
        pass

    @staticmethod
    def _prompt_choice(message, choices):
        cc.v('{} ['.format(message), end='')

        def_choice = ''

        # cc.v('(', end='')
        for i in range(len(choices)):
            if i > 0:
                cc.v('/', end='')
            msg = choices[i][0]
            idx = choices[i][1]
            if choices[i][2]:
                def_choice = msg[idx]
                cc.w(msg[:idx], end='')
                cc.n(msg[idx], end='')
                cc.w(msg[idx + 1:], end='')
            else:
                cc.v(msg[:idx], end='')
                cc.n(msg[idx], end='')
                cc.v(msg[idx + 1:], end='')

        # cc.v(') ', end='')

        # cc.v('[', end='')

        # cc.w(def_choice, end='')
        cc.v(']: ', end='')
        try:
            x = input().strip()
            if len(x) == 0:
                x = def_choice
        except EOFError:
            x = def_choice

        return x

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

    def _check_installation_win(self):
        _err, _ = utils.sys_exec(r'sc query "{}"'.format(WIN_CORE_SERVICE_NAME))
        if 1060 == _err:
            # core service not install
            pass
        else:
            self._is_installed = True
            _err, _o = utils.sys_exec(r'sc qc "{}"'.format(WIN_CORE_SERVICE_NAME))
            if _err != 0:
                raise RuntimeError('Can not get core service installation information.')
            for i in _o:
                _x = i.split(':', 1)
                if 'BINARY_PATH_NAME' == _x[0].strip():
                    _path = _x[1].strip()
                    self._install_path = os.path.abspath(os.path.join(os.path.dirname(_path), '..'))
                    return

        _err, _ = utils.sys_exec(r'sc query "{}"'.format(WIN_WEB_SERVICE_NAME))
        if 1060 == _err:
            # web service not install.
            pass
        else:
            self._is_installed = True
            _err, _o = utils.sys_exec(r'sc qc "{}"'.format(WIN_WEB_SERVICE_NAME))
            if _err != 0:
                raise RuntimeError('Can not get web service installation information.')
            for i in _o:
                _x = i.split(':', 1)
                if 'BINARY_PATH_NAME' == _x[0].strip():
                    _path = _x[1].strip()
                    self._install_path = os.path.abspath(os.path.join(os.path.dirname(_path), '..'))
                    return

    def _copy_files_win(self):
        utils.copy_ex(os.path.join(env.src_path, 'bin'), os.path.join(self._install_path, 'bin'))
        utils.copy_ex(os.path.join(env.src_path, 'www'), os.path.join(self._install_path, 'www'))

        _tmp = os.path.join(self._install_path, 'etc')
        if not os.path.exists(_tmp):
            utils.copy_ex(os.path.join(env.src_path, 'etc'), _tmp)

    def _install_service_win(self):
        _core = os.path.join(self._install_path, 'bin', 'tp_core.exe')
        _err, _o = utils.sys_exec(r'"{}" -i'.format(_core))
        if _err == 0:
            return True
        elif _err == 1:
            cc.v('Core service has been installed already.')
        else:
            cc.e('Install core service failed. error code: ', _err)
            return False

    def _stop_service_win(self):
        _err, _o = utils.sys_exec(r'sc stop "{}"'.format(WIN_CORE_SERVICE_NAME))
        if _err == 1060 or _err == 1062 or _err == 0:
            # 1060 = 服务尚未安装
            # 1062 = 服务尚未启动
            # 0 = 操作成功
            pass
        else:
            raise RuntimeError('Can not stop core service.')

        _err, _o = utils.sys_exec(r'sc stop "{}"'.format(WIN_WEB_SERVICE_NAME))
        if _err == 1060 or _err == 1062 or _err == 0:
            pass
        else:
            raise RuntimeError('Can not stop web service.')


def _main():
    cc.set_default(sep='', end='\n')
    env.init()

    if env.is_win:
        _installer = InstallerWin()
    elif env.is_linux:
        _installer = InstallerLinux()
    else:
        raise RuntimeError('Sorry, teleport server does not support this platform yet.')

    _installer.init()

    if len(sys.argv) > 0:
        _cmd = sys.argv[0].lower()
        if 'uninstall' == _cmd:
            _installer.uninstall()
            return

    _installer.run()


def main():
    try:
        _main()
    except KeyboardInterrupt:
        pass
    except RuntimeError as err:
        cc.v('')
        cc.v('')
        cc.e(err.__str__())
        cc.v('')
    except:
        cc.f('got exception.')

    return 0


if __name__ == '__main__':
    main()
