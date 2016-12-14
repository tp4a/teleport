# -*- coding: utf-8 -*-

"""
执行系统命令的模块
"""

import subprocess

from .logger import *


class SysExec:
    def __init__(self, cmd, line_processor=None):
        self.__cmd = cmd
        self.__process_ret = 0
        self.__console_output = bytes()
        self.__line_processor = line_processor

    def get_exec_ret(self):
        return self.__process_ret

    def get_console_output(self):
        return self.__console_output

    def run(self, direct_output=False, output_codec=None):
        # 注意：output_codec在windows默认为gb2312，其他平台默认utf8
        if output_codec is None:
            if env.is_windows():
                output_codec = 'gb2312'
            else:
                output_codec = 'utf8'

        p = None
        """type: subprocess.Popen"""

        if env.is_windows():
            try:
                p = subprocess.Popen(self.__cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            except WindowsError as e:
                self.__process_ret = e.errno
                msg = 'Unknown error.'
                if 2 == e.errno:
                    msg = 'The system cannot find the file specified.'
                elif 3 == e.errno:
                    msg = 'The system cannot find the path specified.'
                elif 5 == e.errno:
                    msg = 'Access is denied.'
                elif 13 == e.errno:
                    msg = 'The process cannot access the file because it is being used by another process.'

                self.__console_output = msg.encode(output_codec)
                return

            except:
                msg = 'Unknown error.'
                self.__process_ret = 999
                self.__console_output = msg.encode(output_codec)
                return

        else:
            try:
                # Test under Mac, shell must be True.
                p = subprocess.Popen(self.__cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            except:
                msg = 'Unknown error.'
                self.__process_ret = 999
                self.__console_output = msg.encode(output_codec)

        f = p.stdout
        while True:
            line = f.readline()
            if 0 == len(line):
                break

            # if '\n' == line[-1]:
            #	line = line[:-1]

            if line[-2:] == '\r\n':
                line = line[:-2]
                line += '\n'
            if line[-1:] == '\r':
                line = line[:-1]
                line += '\n'

            if self.__line_processor is not None:
                self.__line_processor(line)

            if direct_output:
                log.d(line.decode(output_codec))

            self.__console_output += line

        # # 捕获输出的字符串，在内部使用时先转换为unicode，再根据需要转为其他编码格式
        # # 例如存储时总是转换为utf-8，输出时在Win平台上转换为gb2312，其他平台上会是utf-8.
        # _line = None
        # if const.CONSOLE_WIN_CMD == self.console_type:
        # 	_line = unicode(line, output_codec)
        # else:
        # 	log.v('tab\n')
        # 	_line = utf8_coder.decode(line)[0]#unicode(line, 'utf-8')

        # if direct_output == True:
        # 	log.cap(_line)

        # strOutput += utf8_coder.encode(_line)[0]#_line.encode('utf-8')

        self.__process_ret = p.wait()

        # if bCompareRet:
        # 	if retWanted != ret:
        # 		self.error("\nExecute command returned %d, but we wanted %d.\n\n" % (ret, retWanted))

        # print(self.__console_output.decode(output_codec))
        return

    def start(self):
        # Start a command and return, not wait it end.

        if env.is_windows():
            try:
                subprocess.Popen(self.__cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            except OSError as e:
                self.__process_ret = e.errno
                # msg = 'Unknown error.'
                # if 2 == e.errno:
                #     msg = 'The system cannot find the file specified.'
                # elif 3 == e.errno:
                #     msg = 'The system cannot find the path specified.'
                # elif 5 == e.errno:
                #     msg = 'Access is denied.'
                # elif 13 == e.errno:
                #     msg = 'The process cannot access the file because it is being used by another process.'
                #
                # self.__console_output = msg.encode(output_codec)
                return False

            except:
                # msg = 'Unknown error.'
                self.__process_ret = 999
                # self.__console_output = msg.encode(output_codec)
                return False

        else:
            try:
                subprocess.Popen(self.__cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            except:
                # msg = 'Unknown error.'
                self.__process_ret = 999
                # self.__console_output = msg.encode(output_codec)
                return False

        return True
