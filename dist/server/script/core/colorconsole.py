# -*- coding: utf-8 -*-

import os
import sys
import platform
import traceback

__all__ = ['o', 'v', 'i', 'w', 'e', 'f']

# ======================================
# 颜色
# ======================================
CR_RESTORE = 0  # 恢复正常 - 浅灰色
# BOLD					= "[1m"	# 高亮显示
# UNDERSCORE	  			= "[4m"	# 下划线
# REVERSE				= "[7m"		# 反白显示
CR_BLACK = 1  # 黑色
CR_LIGHT_GRAY = 2  # 浅灰色 - 普通文字
CR_GRAY = 3  # 深灰色 - 捕获别的命令的输出
CR_WHITE = 4  # 白色
CR_RED = 5  # 红色
CR_GREEN = 6  # 绿色
CR_YELLOW = 7  # 黄色 - Windows平台称之为棕色(Brown)
CR_BLUE = 8  # 蓝色
CR_MAGENTA = 9  # 紫红
CR_CYAN = 10  # 青色
CR_LIGHT_RED = 11  # 亮红色 - 失败
CR_LIGHT_GREEN = 12  # 亮绿色 - 成功
CR_LIGHT_YELLOW = 13  # 亮黄色 - 重要
CR_LIGHT_BLUE = 14  # 亮蓝色 - 其实在黑色背景上还是比较深
CR_LIGHT_MAGENTA = 15  # 亮紫色 - 警告
CR_LIGHT_CYAN = 16  # 亮青色

# CR_VERBOSE = CR_LIGHT_GRAY
# CR_NORMAL = CR_WHITE
# CR_INFO = CR_GREEN
# CR_WARN = CR_LIGHT_YELLOW
# CR_ERROR = CR_LIGHT_RED

CR_VERBOSE = CR_RESTORE
CR_NORMAL = CR_GRAY
CR_INFO = CR_GREEN
CR_WARN = CR_YELLOW
CR_ERROR = CR_LIGHT_RED

COLORS = {
    # 常量定义			  	Linux色彩		WinConsole色彩
    CR_RESTORE: ('[0m', 7),  # 7 = 浅灰色 - 普通文字
    CR_BLACK: ('[0;30m', 0),  # 0 = 黑色
    CR_RED: ("[0;31m", 4),  # 红色
    CR_GREEN: ("[0;32m", 2),  # 绿色
    CR_YELLOW: ("[0;33m", 6),  # 黄色 - Windows平台称之为棕色(Brown)
    CR_BLUE: ("[0;34m", 1),  # 蓝色
    CR_MAGENTA: ("[0;35m", 5),  # 紫红
    CR_CYAN: ("[0;36m", 3),  # 青色
    CR_LIGHT_GRAY: ('[0;37m', 7),  # 浅灰色 - 普通文字
    CR_GRAY: ("[1;30m", 8),  # 深灰色 - 捕获别的命令的输出
    CR_LIGHT_RED: ("[1;31m", 12),  # 亮红色 - 失败
    CR_LIGHT_GREEN: ("[1;32m", 10),  # 亮绿色 - 成功
    CR_LIGHT_YELLOW: ("[1;33m", 14),  # 亮黄色 - 重要
    CR_LIGHT_BLUE: ("[1;34m", 9),  # 亮蓝色 - 其实在黑色背景上还是比较深
    CR_LIGHT_MAGENTA: ("[1;35m", 13),  # 亮紫色 - 警告
    CR_LIGHT_CYAN: ("[1;36m", 11),  # 亮青色
    CR_WHITE: ("[1;37m", 15)  # 白色
}


class ColorConsole:
    """
    :type _win_color : Win32ColorConsole
    """

    def __init__(self):

        # self._log_console = self._console_default  # 输出到控制台的方式，为None时表示不输出到控制台
        # self._console_set_color = self._console_set_color_default

        self._sep = ' '
        self._end = '\n'

        self._win_color = None

        self.o = self._func_output
        self.v = self._func_verbose
        self.n = self._func_normal
        self.i = self._func_info
        self.w = self._func_warn
        self.e = self._func_error
        self.f = self._func_fail

        if sys.stdout is None:
            self.o = self._func_pass
            self.v = self._func_pass
            self.n = self._func_pass
            self.i = self._func_pass
            self.w = self._func_pass
            self.e = self._func_pass
            self.f = self._func_pass
            # self._log_console = self._func_pass
            # self._console_set_color = self._console_set_color_default

        else:
            # python2.7 on Ubuntu, sys.platform is 'linux2', so we use platform.system() instead.

            _platform = platform.system().lower()

            if _platform == 'linux' or _platform == 'darwin':
                self._console_set_color = self._console_set_color_linux
                self._console_restore_color = self._console_restore_color_linux
            elif _platform == 'windows':
                if 'TERM' in os.environ and os.environ['TERM'] in ['xterm']:
                    self._console_set_color = self._console_set_color_linux
                    self._console_restore_color = self._console_restore_color_linux

                else:
                    self._win_color = Win32ColorConsole()
                    if self._win_color.available():
                        self._console_set_color = self._console_set_color_win
                        self._console_restore_color = self._console_restore_color_win

                    else:
                        self._console_set_color = self._func_pass
                        self._console_restore_color = self._func_pass

    def set_default(self, *args, **kwargs):
        if 'sep' in kwargs:
            self._sep = kwargs['sep']
        if 'end' in kwargs:
            self._end = kwargs['end']

    def _func_pass(self, *args, **kwargs):
        # do nothing.
        pass

    def _func_output(self, *args, **kwargs):
        sep = kwargs['sep'] if 'sep' in kwargs else self._sep
        end = kwargs['end'] if 'end' in kwargs else self._end

        first = True
        for x in args:
            if not first:
                sys.stdout.writelines(sep)

            if isinstance(x, tuple):
                cl = x[0]
                z = x[1:]
                self._console_set_color(cl)
                self._console_output(*z, sep='', end='')
                sys.stdout.flush()

            elif isinstance(x, str):
                self._console_output(x, sep='', end='')
                sys.stdout.flush()

            else:
                raise RuntimeError('Invalid param.')

        sys.stdout.writelines(end)
        self._console_restore_color()
        sys.stdout.flush()

    def _func_verbose(self, *args, **kwargs):
        self._console_set_color(CR_VERBOSE)
        self._console_output(*args, **kwargs)
        self._console_restore_color()
        sys.stdout.flush()

    # 普通的日志数据
    def _func_normal(self, *args, **kwargs):
        self._console_set_color(CR_NORMAL)
        self._console_output(*args, **kwargs)
        self._console_restore_color()
        sys.stdout.flush()

    # 重要信息
    def _func_info(self, *args, **kwargs):
        self._console_set_color(CR_INFO)
        self._console_output(*args, **kwargs)
        self._console_restore_color()
        sys.stdout.flush()

    # 警告
    def _func_warn(self, *args, **kwargs):
        self._console_set_color(CR_WARN)
        self._console_output(*args, **kwargs)
        self._console_restore_color()
        sys.stdout.flush()

    def _func_error(self, *args, **kwargs):
        self._console_set_color(CR_ERROR)
        self._console_output(*args, **kwargs)
        self._console_restore_color()
        sys.stdout.flush()

    def _func_fail(self, *args, **kwargs):
        self._console_set_color(CR_ERROR)
        self._console_output('[FAIL] ', end='')
        self._console_output(*args, **kwargs)

        _type, _value, _tb = sys.exc_info()
        if _type is not None:
            x = traceback.format_exception_only(_type, _value)
            self._console_output('[EXCEPTION] ', end='')
            self._console_output(x[0], end='')

            x = traceback.extract_tb(_tb)
            c = len(x)
            self._console_set_color(CR_RED)
            for i in range(0, c):
                self._console_output(os.path.abspath(x[i][0]), '(', x[i][1], '): ', x[i][3], sep='')
        else:
            s = traceback.extract_stack()
            c = len(s)
            self._console_set_color(CR_RED)
            for i in range(2, c):
                self._console_output('  ', os.path.abspath(s[c - i - 1][0]), '(', s[c - i - 1][1], '): ', s[c - i - 1][3], sep='')

        self._console_restore_color()
        sys.stdout.flush()

    def _console_set_color_win(self, cr=None):
        if cr is None:
            return
        self._win_color.set_color(COLORS[cr][1])
        sys.stdout.flush()

    def _console_set_color_linux(self, cr=None):
        if cr is None:
            return
        sys.stdout.writelines('\x1B')
        sys.stdout.writelines(COLORS[cr][0])
        sys.stdout.flush()

    def _console_restore_color_win(self):
        self._win_color.set_color(COLORS[CR_RESTORE][1])
        sys.stdout.flush()

    def _console_restore_color_linux(self):
        sys.stdout.writelines('\x1B[0m')
        sys.stdout.flush()

    def _console_output(self, *args, **kwargs):
        sep = kwargs['sep'] if 'sep' in kwargs else self._sep
        end = kwargs['end'] if 'end' in kwargs else self._end
        first = True
        for x in args:
            if not first:
                sys.stdout.writelines(sep)

            first = False
            if isinstance(x, str):
                sys.stdout.writelines(x)
                continue

            else:
                sys.stdout.writelines(x.__str__())

        sys.stdout.writelines(end)
        sys.stdout.flush()

    def test(self):
        self.o('o()......')
        self.v('v()......')
        self.n('n()......')
        self.i('i()......')
        self.w('w()......')
        self.e('e()......')
        self.f('f()......')

        self.v('test auto\nsplit lines.\nYou should see\nmulti-lines.\n')


class Win32ColorConsole:
    def __init__(self):
        from ctypes import WINFUNCTYPE, windll
        from ctypes.wintypes import BOOL, HANDLE, DWORD, WORD

        self.__original_stderr = sys.stderr
        self.__stdout = None
        self.__SetConsoleTextAttribute = None

        # Work around <http://bugs.python.org/issue6058>.
        # codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

        # Make Unicode console output work independently of the current code page.
        # This also fixes <http://bugs.python.org/issue1602>.
        # Credit to Michael Kaplan <http://blogs.msdn.com/b/michkap/archive/2010/04/07/9989346.aspx>
        # and TZOmegaTZIOY
        # <http://stackoverflow.com/questions/878972/windows-cmd-encoding-change-causes-python-crash/1432462#1432462>.
        try:
            # <http://msdn.microsoft.com/en-us/library/ms683231(VS.85).aspx>
            # HANDLE WINAPI GetStdHandle(DWORD nStdHandle);
            # returns INVALID_HANDLE_VALUE, NULL, or a valid handle
            #
            # <http://msdn.microsoft.com/en-us/library/aa364960(VS.85).aspx>
            # DWORD WINAPI GetFileType(DWORD hFile);
            #
            # <http://msdn.microsoft.com/en-us/library/ms683167(VS.85).aspx>
            # BOOL WINAPI GetConsoleMode(HANDLE hConsole, LPDWORD lpMode);

            STD_OUTPUT_HANDLE = DWORD(-11)
            INVALID_HANDLE_VALUE = DWORD(-1).value

            GetStdHandle = WINFUNCTYPE(HANDLE, DWORD)(("GetStdHandle", windll.kernel32))

            self.__SetConsoleTextAttribute = WINFUNCTYPE(BOOL, HANDLE, WORD)(("SetConsoleTextAttribute", windll.kernel32))

            self.__stdout = GetStdHandle(STD_OUTPUT_HANDLE)
            if self.__stdout == INVALID_HANDLE_VALUE:
                self.__stdout = None

        except Exception as e:
            self.__stdout = None
            self._complain("exception %r while fixing up sys.stdout and sys.stderr\n" % (str(e),))

    # If any exception occurs in this code, we'll probably try to print it on stderr,
    # which makes for frustrating debugging if stderr is directed to our wrapper.
    # So be paranoid about catching errors and reporting them to original_stderr,
    # so that we can at least see them.
    @staticmethod
    def _complain(message):
        # print >> self.__original_stderr, message if isinstance(message, str) else repr(message)
        sys.stderr.writelines(message)

    def available(self):
        if self.__stdout is None or self.__SetConsoleTextAttribute is None:
            return False
        else:
            return True

    def set_color(self, color):
        # if not self.available():
        #     return
        self.__SetConsoleTextAttribute(self.__stdout, color)


_cc = ColorConsole()
del ColorConsole

# _cc.test()


def set_default(*args, **kwargs):
    _cc.set_default(*args, **kwargs)


def o(*args, **kwargs):
    _cc.o(*args, **kwargs)


def v(*args, **kwargs):
    _cc.v(*args, **kwargs)


def n(*args, **kwargs):
    _cc.n(*args, **kwargs)


def i(*args, **kwargs):
    _cc.i(*args, **kwargs)


def w(*args, **kwargs):
    _cc.w(*args, **kwargs)


def e(*args, **kwargs):
    _cc.e(*args, **kwargs)


def f(*args, **kwargs):
    _cc.f(*args, **kwargs)
