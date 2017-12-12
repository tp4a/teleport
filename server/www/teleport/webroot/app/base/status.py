# -*- coding: utf-8 -*-

import psutil
from app.base.utils import tp_timestamp_utc_now, tp_utc_timestamp_ms
from app.controller.ws import tp_wss
from app.base.cron import tp_corn


class TPSysStatus(object):
    _INTERVAL = 5  # seconds

    def __init__(self):
        super().__init__()

        import builtins
        if '__tp_sys_status__' in builtins.__dict__:
            raise RuntimeError('TPSysStatus object exists, you can not create more than one instance.')

        # 实时数据我们在内存中保留最近10分钟的数据，每5秒收集一次，共 10*60/5 = 120 条记录
        self._history = list()

        self._disk_read = 0
        self._disk_write = 0
        self._net_recv = 0
        self._net_sent = 0

    def init(self):
        t = tp_utc_timestamp_ms() - 10 * 60 * 1000
        cnt = int((10 * 60 + self._INTERVAL - 1) / self._INTERVAL)
        for i in range(cnt):
            val = {
                't': t,
                'cpu': {'u': 0, 's': 0},
                'mem': {'u': 1, 't': 100},
                'disk': {'r': 0, 'w': 0},
                'net': {'r': 0, 's': 0}
            }
            self._history.append(val)
            t += self._INTERVAL*1000

        psutil.cpu_times_percent()
        net = psutil.net_io_counters(pernic=False)
        self._net_recv = net.bytes_recv
        self._net_sent = net.bytes_sent
        disk = psutil.disk_io_counters(perdisk=False)
        self._disk_read = disk.read_bytes
        self._disk_write = disk.write_bytes

        tp_corn().add_job('sys_status', self._check_status, first_interval_seconds=self._INTERVAL, interval_seconds=self._INTERVAL)
        tp_wss().register_get_sys_status_callback(self.get_status)
        return True

    def _check_status(self):
        val = {'t': tp_utc_timestamp_ms()}

        cpu = psutil.cpu_times_percent()
        val['cpu'] = {'u': cpu.user, 's': cpu.system}

        mem = psutil.virtual_memory()
        val['mem'] = {'u': mem.used, 't': mem.total}

        disk = psutil.disk_io_counters(perdisk=False)
        _read = disk.read_bytes - self._disk_read
        _write = disk.write_bytes - self._disk_write
        self._disk_read = disk.read_bytes
        self._disk_write = disk.write_bytes

        if _read < 0:
            _read = 0
        if _write < 0:
            _write = 0
        val['disk'] = {'r': int(_read / self._INTERVAL), 'w': int(_write / self._INTERVAL)}

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
        val['net'] = {'r': int(_recv / self._INTERVAL), 's': int(_sent / self._INTERVAL)}

        self._history.pop(0)
        self._history.append(val)

        tp_wss().send_message('sys_status', val)

    def get_status(self):
        return self._history


def tp_sys_status():
    """
    取得TPSysStatus管理器的唯一实例

    :rtype : TPSysStatus
    """

    import builtins
    if '__tp_sys_status__' not in builtins.__dict__:
        builtins.__dict__['__tp_sys_status__'] = TPSysStatus()
    return builtins.__dict__['__tp_sys_status__']
