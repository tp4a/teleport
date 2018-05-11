# -*- coding: utf-8 -*-

import os
import platform
import atexit
import sys
import threading
import time
import traceback

__all__ = ['log']

USE_TPWEB_LOG = False

try:
    import tpweb
    USE_TPWEB_LOG = True
except ImportError:
    pass

# ======================================
# 颜色
# ======================================
CR_NORMAL = 1
CR_DEBUG = 2
CR_VERBOSE = 3
CR_INFO = 4
CR_WARN = 5
CR_ERROR = 6

COLORS = {
    # 常量定义: (Linux色彩, WinConsole色彩)
    CR_NORMAL: ('[0m', 7),  # 默认颜色
    # CR_WHITE: ("[0;30m", 15),  # 最亮的白色
    CR_DEBUG: ('[0;37m', 7),  # 深灰色
    CR_VERBOSE: ('[0m', 0),  # 标准色
    CR_ERROR: ("[0;31m", 4),  # 红色
    CR_INFO: ("[0;32m", 2),  # 绿色
    CR_WARN: ("[0;35m", 5)  # 紫红
}


class Logger:
    """
    日志记录模块，支持输出到控制台及文件。

    :type _file_handle : file
    :type _win_color : Win32ColorConsole
    """
    LOG_DEBUG = 0
    LOG_VERBOSE = 1
    LOG_INFO = 2
    LOG_WARN = 3
    LOG_ERROR = 4

    TRACE_ERROR_NONE = 0
    TRACE_ERROR_FULL = 999999

    def __init__(self):
        atexit.register(self.finalize)

        if USE_TPWEB_LOG:
            self.LOG_DEBUG = tpweb.EX_LOG_LEVEL_DEBUG
            self.LOG_VERBOSE = tpweb.EX_LOG_LEVEL_VERBOSE
            self.LOG_INFO = tpweb.EX_LOG_LEVEL_INFO
            self.LOG_WARN = tpweb.EX_LOG_LEVEL_WARN
            self.LOG_ERROR = tpweb.EX_LOG_LEVEL_ERROR
            self._do_log = self._do_log_tpweb
        else:
            self._do_log = self._do_log_local

        self._locker = threading.RLock()

        # self._sep = ' '
        # self._end = '\n'

        self._min_level = self.LOG_INFO  # 大于等于此值的日志信息才会记录
        self._trace_error = self.TRACE_ERROR_NONE  # 记录错误信息时，是否追加记录调用栈
        self._log_datetime = True  # 是否记录日志时间
        self._file_handle = None  # 日志文件的句柄，为None时表示不记录到文件
        self._to_console = False

        self._win_color = None

        self._set_console(True)
        self._set_level(self._min_level)

    def initialize(self):
        if not USE_TPWEB_LOG:
            self._log_datetime = True

    def finalize(self):
        if self._file_handle is not None:
            self._file_handle.close()

    def set_attribute(self, min_level=None, console=None, log_datetime=None, trace_error=None, filename=None):
        """
        设置日志模块属性，参数为None的跳过，不调整。其中，filename设为''空字符串（不是None）表示关闭记录到文件的功能。
        :type filename: str
        :type trace_error: int
        :type log_datetime: bool
        :type min_level: int
        :type console: bool
        """
        if min_level is not None:
            self._set_level(min_level)

        if console is not None:
            self._set_console(console)

        if log_datetime is not None:
            self._log_datetime = log_datetime

        if trace_error is not None:
            self._trace_error = trace_error

        if filename is not None:
            if not self._set_filename(filename):
                return False

        return True

    def _set_level(self, level):
        self.d = self._log_debug
        self.v = self._log_verbose
        self.i = self._log_info
        self.w = self._log_warn
        self.e = self._log_error

        if self.LOG_DEBUG == level:
            pass
        elif self.LOG_VERBOSE == level:
            self.d = self._log_pass
        elif self.LOG_INFO == level:
            self.d = self._log_pass
            self.v = self._log_pass
        elif self.LOG_WARN == level:
            self.d = self._log_pass
            self.v = self._log_pass
            self.i = self._log_pass
        elif self.LOG_ERROR == level:
            self.d = self._log_pass
            self.v = self._log_pass
            self.i = self._log_pass
            self.w = self._log_pass
        else:
            pass

        self._min_level = level

    def _set_console(self, is_enabled):
        if not is_enabled:
            self._to_console = False
            # self._log_console = self._log_pass
            return

        # python2.7 on Ubuntu, sys.platform is 'linux2', so we use platform.system() instead.

        _platform = platform.system().lower()

        if _platform == 'linux' or _platform == 'darwin':
            self._console_set_color = self._console_set_color_linux
            self._console_restore_color = self._console_restore_color_linux
        elif _platform == 'windows':
            if 'TERM' in os.environ and os.environ['TERM'] in ['xterm', 'emacs', 'cygwin']:
                self._console_set_color = self._console_set_color_linux
                self._console_restore_color = self._console_restore_color_linux

            else:
                self._win_color = Win32ColorConsole()
                if self._win_color.available():
                    self._console_set_color = self._console_set_color_win
                    self._console_restore_color = self._console_restore_color_win

                else:
                    self._console_set_color = self._log_pass
                    self._console_restore_color = self._log_pass

    def _set_filename(self, base_filename):
        if USE_TPWEB_LOG:
            return True

        if len(base_filename) == 0:
            if self._file_handle is not None:
                self._file_handle.close()
                self._file_handle = None
            return True

        log_filename = base_filename.strip()
        if 0 == len(log_filename):
            self.e('invalid log file name.')
            return False

        try:
            self._file_handle = open(log_filename, 'a+', encoding='utf8')
        except IOError:
            self._file_handle = None
            self.e('Can not open log file for write [{}].\n'.format(log_filename))
            return False

        return True

    def _log_pass(self, *args, **kwargs):
        pass

    def _log_debug(self, *args, **kwargs):
        self._console_set_color(CR_DEBUG)
        self._do_log(self.LOG_DEBUG, *args, **kwargs)
        self._console_restore_color()

    def _log_verbose(self, *args, **kwargs):
        self._console_set_color(CR_VERBOSE)
        self._do_log(self.LOG_VERBOSE, *args, **kwargs)
        self._console_restore_color()

    def _log_info(self, *args, **kwargs):
        self._console_set_color(CR_INFO)
        self._do_log(self.LOG_INFO, *args, **kwargs)
        self._console_restore_color()

    def _log_warn(self, *args, **kwargs):
        self._console_set_color(CR_WARN)
        self._do_log(self.LOG_WARN, *args, **kwargs)
        self._console_restore_color()

    def _log_error(self, *args, **kwargs):
        self._console_set_color(CR_ERROR)
        self._do_log(self.LOG_ERROR, *args, **kwargs)

        if self._trace_error != self.TRACE_ERROR_NONE:
            s = traceback.extract_stack()
            c = len(s)
            for i in range(c - 1):
                if i >= self._trace_error:
                    break
                if s[c - 2 - i][0].startswith('<frozen '):
                    continue
                self._do_log(self.LOG_ERROR, '  %s(%d)\n' % (s[c - 2 - i][0], s[c - 2 - i][1]))

        _type, _value, _tb = sys.exc_info()
        if _type is not None:
            x = traceback.format_exception_only(_type, _value)
            self._do_log(self.LOG_ERROR, '[EXCEPTION] %s' % x[0])
            x = traceback.extract_tb(_tb)
            self._do_log(self.LOG_ERROR, '  %s(%d): %s\n' % (x[-1][0], x[-1][1], x[-1][3]))

        self._console_restore_color()

    def _do_log_tpweb(self, level, *args, **kwargs):
        # sep = kwargs['sep'] if 'sep' in kwargs else self._sep
        # end = kwargs['end'] if 'end' in kwargs else self._end

        # first = True
        for x in args:
            # if not first:
            #     tpweb.log_output(level, sep)

            # first = False
            if isinstance(x, str):
                tpweb.log_output(level, x)
                continue

            else:
                tpweb.log_output(level, x.__str__())

                # tpweb.log_output(level, end)

    def _do_log_local(self, level, *args, **kwargs):
        if level < self._min_level:
            return

        show_datetime = kwargs['show_datetime'] if 'show_datetime' in kwargs else self._log_datetime

        with self._locker:
            if show_datetime:
                now = time.localtime(time.time())
                # _log_time = '[{now.tm_year:02d}{now.tm_mon:02d}{now.tm_mday:02d}-{now.tm_hour:02d}{now.tm_min:02d}{now.tm_sec:02d}] '.format(now=now)
                _log_time = '[{now.tm_mon:02d}/{now.tm_mday:02d}-{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}] '.format(now=now)

                sys.stdout.writelines(_log_time)
                self._log_file(_log_time)

            for x in args:
                if isinstance(x, str):
                    sys.stdout.writelines(x)
                    self._log_file(x)
                    continue

                else:
                    sys.stdout.writelines(x.__str__())
                    self._log_file(x.__str__())

    def _console_set_color_win(self, cr=None):
        if cr is None or USE_TPWEB_LOG:
            return
        self._win_color.set_color(COLORS[cr][1])

    def _console_set_color_linux(self, cr=None):
        if cr is None or USE_TPWEB_LOG:
            return
        sys.stdout.writelines('\x1B')
        sys.stdout.writelines(COLORS[cr][0])
        sys.stdout.flush()

    def _console_restore_color_win(self):
        if USE_TPWEB_LOG:
            return
        self._win_color.set_color(COLORS[CR_NORMAL][1])
        sys.stdout.flush()

    def _console_restore_color_linux(self):
        if USE_TPWEB_LOG:
            return
        sys.stdout.writelines('\x1B[0m')
        sys.stdout.flush()

    def bin(self, msg, data):
        # 二进制日志格式（一行16字节数据）：
        # 00000000   2F 64 65 76 2F 73 64 61 - 31 03 0B 08 00 00 B0 0A   /dev/sda1.......
        # 00000010   01 00 00 00 02 00 00 00 - 03 00 00 00 CF A7 DF 55   ...............U
        # 00000080   1F 00 00 00 00                                      .....
        # 这样，每一行需要 8(偏移)+3(留白)+ 3*8(前8字节) +2(中间分隔号及留白) + 3*8(后8字节) + 3(留白) + 16(可显示字符) = 80字节
        # 根据要显示的数组长度，可以计算出需要多少行。

        # 仅仅在调试模式下输出二进制。
        if self._min_level > self.LOG_DEBUG:
            return
        # 仅仅输出到控制台，不输出到日志文件
        # if self._log_console is None:
        if not self._to_console:
            return

        m = msg.rstrip(' \r\n\t')
        if bytes != type(data) and bytearray != type(data):
            self.w('%s [NOT BINARY]\n' % m)
            return
        data_size = len(data)
        self.d('%s [%d/0x%X B]\n' % (m, data_size, data_size))
        if data_size == 0:
            return

        x = 0
        loop = int(data_size / 16)
        last_line = data_size % 16

        for x in range(loop):
            m = '%08X  ' % (x * 16)

            for y in range(16):
                if 8 == y:
                    m += ' -'
                m += ' %02X' % data[x * 16 + y]

            m += '   '

            for y in range(16):
                ch = data[x * 16 + y]
                if 32 <= ch <= 126:
                    m += '%c' % data[x * 16 + y]
                else:
                    m += '.'

            m += '\n'
            self.d(m)

        if loop > 0:
            x += 1

        if last_line > 0:
            padding_size = (16 - last_line) * 3
            if last_line <= 8:
                padding_size += 2

            m = '%08X  ' % (x * 16)

            for y in range(last_line):
                if 8 == y:
                    m += ' -'
                m += ' %02X' % data[x * 16 + y]

            m += ' ' * (padding_size + 3)

            for y in range(last_line):
                ch = data[x * 16 + y]
                if 32 <= ch <= 126:
                    m += '%c' % data[x * 16 + y]
                else:
                    m += '.'

            m += '\n'
            self.d(m)

    # def _do_log(self, msg, color=None, show_datetime=True):
    #     with self._locker:
    #         now = time.localtime(time.time())
    #         _log_time = '[{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}] '.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    #
    #         try:
    #             if show_datetime and self._log_datetime:
    #                 msg = '{}{}'.format(_log_time, msg)
    #                 self._log_console(msg, color)
    #             else:
    #                 self._log_console(msg, color)
    #                 msg = '{}{}'.format(_log_time, msg)
    #
    #             self._log_file(msg)
    #
    #         except IOError:
    #             pass

    # def _console_default(self, msg, color=None):
    #     """
    #     Log to console without color.
    #     """
    #     if not self._log_console:
    #         return
    #     if msg is None:
    #         return
    #
    #     sys.stdout.writelines(msg)
    #     sys.stdout.flush()

    # def _console_win(self, msg, color=None):
    #     if not self._log_console:
    #         return
    #     if msg is None:
    #         msg = ''
    #
    #     # 这里的问题很复杂，日常使用没有问题，但是当在工作机上使用时，部分内容是捕获另一个脚本执行的结果再输出
    #     # 如果结果中有中文，这里就会显示乱码。如果尝试编码转换，会抛出异常。目前暂时采用显示乱码的方式了。
    #
    #     # if CONSOLE_WIN_CMD == self.console_type:
    #     # 	try:
    #     # 		_msg = unicode(msg, 'utf-8')
    #     # 	except:
    #     # 		_msg = msg
    #     # else:
    #     # 	_msg = msg
    #     # _msg = None
    #     # if isinstance(msg, unicode):
    #     #     _msg = msg
    #     # else:
    #     #     # _msg = unicode(msg, 'utf-8')
    #     #     try:
    #     #         _msg = unicode(msg, 'utf-8')
    #     #     except:
    #     #         _msg = unicode(msg, 'gb2312')
    #     #         # _msg = msg
    #     #
    #     #         # if CONSOLE_WIN_CMD == self.console_type:
    #     #         # 	sys.stdout.writelines(msg.encode('gb2312'))
    #     #         # else:
    #     #         # 	sys.stdout.writelines(msg.encode('utf-8'))
    #     #
    #     #
    #     #         # try:
    #     #         #	_msg = unicode(msg, 'utf-8')
    #     #         # except:
    #     # _msg = msg
    #
    #     if color is None:
    #         sys.stdout.writelines(msg)
    #     else:
    #         self._win_color.set_color(COLORS[color][1])
    #         sys.stdout.writelines(msg)
    #         sys.stdout.flush()
    #         self._win_color.set_color(COLORS[CR_NORMAL][1])
    #
    #     sys.stdout.flush()
    #
    # def _console_linux(self, msg, cr=None):
    #     if not self._log_console:
    #         return
    #     if msg is None:
    #         return
    #
    #     if cr is None:
    #         sys.stdout.writelines(msg)
    #     else:
    #         sys.stdout.writelines('\x1B%s%s\x1B[0m' % (COLORS[cr][0], msg))
    #         # sys.stdout.writelines('\[%s%s\[[0m' % (COLORS[cr][0], msg))
    #
    #     sys.stdout.flush()

    def _log_file(self, msg):
        if self._file_handle is None:
            return

        # 保存到文件时，总是将字符串按 utf-8 格式保存
        # self._file_handle.write(msg.encode('utf-8'))
        self._file_handle.write(msg)
        self._file_handle.flush()

    def log_print(self, *args, **kwargs):
        sep = kwargs['sep'] if 'sep' in kwargs else ' '
        end = kwargs['end'] if 'end' in kwargs else '\n'

        show_datetime = self._log_datetime
        first = True
        for x in args:
            if not first:
                log._do_log(self.LOG_VERBOSE, sep, show_datetime=show_datetime)

            first = False
            if isinstance(x, str):
                log._do_log(self.LOG_VERBOSE, x, show_datetime=show_datetime)
            else:
                log._do_log(self.LOG_VERBOSE, x.__str__(), show_datetime=show_datetime)

            show_datetime = False

        log._do_log(self.LOG_VERBOSE, end, show_datetime=show_datetime)

        # s = traceback.extract_stack()
        # c = len(s)
        # for i in range(c - 1):
        #     if i >= self._trace_error:
        #         break
        #     if s[c - 2 - i][0].startswith('<frozen '):
        #         continue
        #     self._do_log('USING `print` IN SOURCE FILE:\n')
        #     self._do_log('  %s(%d)\n' % (s[c - 2 - i][0], s[c - 2 - i][1]), CR_RED)
        #     break

    def _test(self):
        self._set_level(self.LOG_DEBUG)
        self._trace_error = self.TRACE_ERROR_FULL

        self.d('This is DEBUG message.\n')
        self.v('This is VERBOSE message.\n')
        self.i('This is INFORMATION message.\n')
        self.w('This is WARNING message.\n')
        self.e('This is ERROR message.\n')

        self.v('test auto\nsplit lines.\nYou should see\nmulti-lines.\n')

        data = b'This is a test string and you can see binary format data here.'
        self.bin('Binary Data:\n', data)
        data = b''
        self.bin('Empty binary\n', data)
        self.bin('This is string\n\n', 'data')

        sys.stdout.writelines('[0m      \x1B[0m')
        sys.stdout.writelines('This is a string.\n')

        for x in [0, 1, 4, 7]:  # 0=正常，1=加粗，4=下划线，7=反白显示（前景背景对调）
            for y in range(2):  # 3=正常，4=背景色
                for z in range(9):  # 颜色
                    sys.stdout.writelines('\x1B[0m')
                    sys.stdout.writelines('[{};{}{}m   '.format(x, y + 3, z))

                    # [0;30m
                    sys.stdout.writelines('\x1B[{};{}{}m'.format(x, y + 3, z))
                    sys.stdout.writelines('This is a string.\n')
                    sys.stdout.flush()

                    # sys.stdout.flush()


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


log = Logger()
del Logger

# log._test()
# print('test built-in `print` function.')

import builtins

builtins.__dict__['print'] = log.log_print
