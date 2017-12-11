# -*- coding: utf-8 -*-

import time
import datetime
import threading
import psutil
import json

from app.base.logger import log
from app.base.utils import tp_timestamp_utc_now
from app.base.configs import tp_cfg
from app.controller.ws import tp_wss


class TPSysStatus(threading.Thread):
    def __init__(self):
        super().__init__(name='sys-status-thread')

        import builtins
        if '__tp_sys_status__' in builtins.__dict__:
            raise RuntimeError('TPSysStatus object exists, you can not create more than one instance.')

        # session表，session_id为索引，每个项为一个字典，包括 v(value), t(last access), e(expire seconds)
        self._session_dict = dict()

        self._stop_flag = False
        self._time_cnt = 0
        self._interval = 2

        self._disk_read = 0
        self._disk_write = 0
        self._net_recv = 0
        self._net_sent = 0

    def init(self):
        psutil.cpu_times_percent()
        net = psutil.net_io_counters(pernic=False)
        self._net_recv = net.bytes_recv
        self._net_sent = net.bytes_sent
        disk = psutil.disk_io_counters(perdisk=False)
        self._disk_read = disk.read_bytes
        self._disk_write = disk.write_bytes

        return True

    def stop(self):
        self._stop_flag = True
        self.join()
        log.v('{} stopped.\n'.format(self.name))

    def run(self):
        while not self._stop_flag:
            # time.sleep(1)
            # if self._stop_flag:
            #     break
            # self._time_cnt += 1
            # if self._time_cnt < 5:
            #     continue
            #
            # self._time_cnt = 0

            time.sleep(self._interval)
            val = {'t': tp_timestamp_utc_now()}

            cpu = psutil.cpu_times_percent()
            # print(int(cpu.user * 100), int(cpu.system * 100))
            val['c'] = {'u': cpu.user, 's': cpu.system}
            #
            mem = psutil.virtual_memory()
            val['m'] = {'u': mem.used, 't': mem.total}
            # print(mem.total, mem.used, int(mem.used * 100 / mem.total))

            disk = psutil.disk_io_counters(perdisk=False)
            # val['d'] = {'r': disk.read_byes, 'w': disk.write_bytes}
            # print(disk.read_bytes, disk.write_bytes)
            _read = disk.read_bytes - self._disk_read
            _write = disk.write_bytes - self._disk_write
            self._disk_read = disk.read_bytes
            self._disk_write = disk.write_bytes

            if _read < 0:
                _read = 0
            if _write < 0:
                _write = 0
            val['d'] = {'r': _read, 'w': _write}
            # print(int(_read / self._interval), int(_write / self._interval))

            net = psutil.net_io_counters(pernic=False)
            _recv = net.bytes_recv - self._net_recv
            _sent = net.bytes_sent - self._net_sent
            self._net_recv = net.bytes_recv
            self._net_sent = net.bytes_sent

            # On some systems such as Linux, on a very busy or long-lived system, the numbers
            # returned by the kernel may overflow and wrap (restart from zero)
            if _recv < 0:
                _recv = 0
            if _sent < 0:
                _sent = 0
            val['n'] = {'r': _recv, 's': _sent}
            # print(int(_recv / self._interval), int(_sent / self._interval))

            # s = json.dumps(val, separators=(',', ':'))

            tp_wss().send_message('sys_real_status', val)

            # print(s)


def tp_sys_status():
    """
    取得TPSysStatus管理器的唯一实例

    :rtype : TPSysStatus
    """

    import builtins
    if '__tp_sys_status__' not in builtins.__dict__:
        builtins.__dict__['__tp_sys_status__'] = TPSysStatus()
    return builtins.__dict__['__tp_sys_status__']
