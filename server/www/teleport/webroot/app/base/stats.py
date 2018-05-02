# -*- coding: utf-8 -*-

import psutil
from app.base.utils import tp_utc_timestamp_ms
from app.const import *
from app.base.wss import tp_wss
from app.base.cron import tp_cron
from app.model import stats


class TPStats(object):
    _INTERVAL = 5  # seconds

    def __init__(self):
        super().__init__()

        import builtins
        if '__tp_stats__' in builtins.__dict__:
            raise RuntimeError('TPStats object exists, you can not create more than one instance.')

        # 实时数据我们在内存中保留最近10分钟的数据，每5秒收集一次，共 10*60/5 = 120 条记录
        self._sys_stats = list()

        # 网络流量和磁盘IO是递增的数据，因此要记下上一次采集的数据，以便计算间隔时间内的增量
        self._net_recv = 0
        self._net_sent = 0
        self._disk_read = 0
        self._disk_write = 0

        self._counter_stats = {
            'user': 1,
            'host': 0,
            'acc': 0,
            'conn': 0
        }

    def init(self):
        t = tp_utc_timestamp_ms() - 10 * 60 * 1000
        cnt = int((10 * 60 + self._INTERVAL - 1) / self._INTERVAL)
        for i in range(cnt):
            val = {
                't': t,
                'cpu': {'u': 0, 's': 0},
                'mem': {'u': 0, 't': 100},
                'disk': {'r': 0, 'w': 0},
                'net': {'r': 0, 's': 0}
            }
            self._sys_stats.append(val)
            t += self._INTERVAL * 1000

        psutil.cpu_times_percent()
        net = psutil.net_io_counters(pernic=False)
        self._net_recv = net.bytes_recv
        self._net_sent = net.bytes_sent
        disk = psutil.disk_io_counters(perdisk=False)
        self._disk_read = disk.read_bytes
        self._disk_write = disk.write_bytes

        err, c = stats.get_basic_stats()
        if TPE_OK == err:
            self._counter_stats = c

        # 每 5秒 采集一次系统状态统计数据
        tp_cron().add_job('sys_status', self._check_sys_stats, first_interval_seconds=self._INTERVAL, interval_seconds=self._INTERVAL)
        # 每 1小时 重新查询一次数据库，得到用户数/主机数/账号数/连接数，避免统计数量出现偏差
        tp_cron().add_job('query_counter', self._query_counter, first_interval_seconds=60 * 60, interval_seconds=60 * 60)
        # 每 1分钟 检查一下临时锁定用户是否可以自动解锁了
        tp_cron().add_job('check_temp_locked_user', self._check_temp_locked_user, interval_seconds=60)

        tp_wss().register_get_sys_status_callback(self.get_sys_stats)
        tp_wss().register_get_stat_counter_callback(self.get_counter_stats)

        return True

    def _check_sys_stats(self):
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

        self._sys_stats.pop(0)
        self._sys_stats.append(val)

        tp_wss().send_message('sys_status', val)

    def _query_counter(self):
        # 直接从数据库中查询数据，避免长时间运行后计数不准确
        err, c = stats.get_basic_stats()
        if TPE_OK == err:
            self._counter_stats = c
            tp_wss().send_message('stat_counter', self._counter_stats)

    def _check_temp_locked_user(self):
        stats.update_temp_locked_user_state()

    def get_sys_stats(self):
        return self._sys_stats

    def get_counter_stats(self):
        return self._counter_stats

    def user_counter_change(self, count):
        self._counter_stats['user'] = count
        # self._counter_stats['user'] += alt_count
        # if self._counter_stats['user'] < 0:
        #     self._counter_stats['user'] = 0
        tp_wss().send_message('stat_counter', self._counter_stats)

    def host_counter_change(self, alt_count):
        self._counter_stats['host'] += alt_count
        if self._counter_stats['host'] < 0:
            self._counter_stats['host'] = 0
        tp_wss().send_message('stat_counter', self._counter_stats)

    def acc_counter_change(self, alt_count):
        self._counter_stats['acc'] += alt_count
        if self._counter_stats['acc'] < 0:
            self._counter_stats['acc'] = 0
        tp_wss().send_message('stat_counter', self._counter_stats)

    def conn_counter_change(self, alt_count):
        self._counter_stats['conn'] += alt_count
        if self._counter_stats['conn'] < 0:
            self._counter_stats['conn'] = 0
        tp_wss().send_message('stat_counter', self._counter_stats)


def tp_stats():
    """
    取得 TPSysStatus 的唯一实例

    :rtype : TPStats
    """

    import builtins
    if '__tp_stats__' not in builtins.__dict__:
        builtins.__dict__['__tp_stats__'] = TPStats()
    return builtins.__dict__['__tp_stats__']
