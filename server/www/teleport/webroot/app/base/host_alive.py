# -*- coding: utf-8 -*-

"""
通过PING等方式，判断远程主机的存活状态
  对系统中所有主机执行PING，默认每一分钟执行一次，默认PING为5秒超时；
  对每台主机：
    记录最后一次PING成功的时间，并与当前时间比较
      1分钟以内，正常（界面上绿色图标）
      大于1分钟，小于2分钟，故障（界面上黄色图标）
      大于2分钟，离线（界面上红色图标）
"""

import time
import threading
import socket
import select
import struct

from app.base.configs import tp_cfg
from app.base.cron import tp_cron
from app.base.logger import log

from app.model import host
# import app.model.host


def calc_icmp_checksum(data):
    n = len(data)
    m = n % 2
    checksum = 0
    for i in range(0, n - m, 2):
        # 每两个字节视作一个小端字节序的uint16，把它们加到一起
        checksum += (data[i]) + ((data[i + 1]) << 8)
    if m:
        checksum += (data[-1])
    # 将高16位与低16位相加
    checksum = (checksum >> 16) + (checksum & 0xffff)
    # 如果还有高于16位，将继续与低16位相加
    checksum += (checksum >> 16)
    # 结果是一个 uint16
    ret = ~checksum & 0xffff
    # 主机字节序转网络字节序列（小端序转大端序）
    ret = ret >> 8 | (ret << 8 & 0xff00)
    return ret


class HostAlive(object):

    PING_INTERVAL = 60    # 每分钟执行一次
    PING_TIMEOUT = 5      # 5秒

    METHOD_PING = 0
    METHOD_HTTP_GET = 1

    ICMP_ECHO_REQUEST = 8

    STATE_UNKNOWN = 0   # 未知(尚未检测)
    STATE_ONLINE = 1    # 在线
    STATE_WARNING = 2   # 可能离线
    STATE_OFFLINE = 3   # 已经离线(距离上次在线状态超过两分钟)

    def __init__(self):
        super().__init__()

        import builtins
        if '__host_alive__' in builtins.__dict__:
            raise RuntimeError('HostAlive object exists, you can not create more than one instance.')

        # 主机状态表，主机ip为索引，每个项为一个字典，包括
        # {
        #   'last_online': TIMESTAMP,
        #   'last_check': TIMESTAMP,
        #   'method': 0=PING,1=HTTP-GET
        #   'param': {}
        # }
        self._states = dict()

        self._need_stop = False
        self._socket_ping = None
        self._base_ping_pkg_id = 0
        self._thread_recv_ping_result = None

        self._ping_pkg_id_list = dict()

        self._lock = threading.RLock()

    def init(self):
        icmp_protocol = socket.getprotobyname('icmp')
        try:
            self._socket_ping = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_protocol)
        except PermissionError:
            print('To use PING to check host state, must run as root.')
            log.e('To use PING to check host state, must run as root.\n')
            return False

        # 加载所有主机IP
        hosts = host.get_all_hosts_for_check_state()
        for h in hosts:
            if h['router_ip'] != '':
                self.add_host(h['router_ip'], HostAlive.METHOD_PING)
            else:
                self.add_host(h['ip'], HostAlive.METHOD_PING)

        self._thread_recv_ping_result = threading.Thread(target=self._thread_func_recv_ping_result)
        self._thread_recv_ping_result.start()

        tp_cron().add_job('host_check_alive', self._check_alive, first_interval_seconds=10, interval_seconds=HostAlive.PING_INTERVAL)

        # for test:
        # tp_cron().add_job('host_show_alive', self._show_alive, first_interval_seconds=20, interval_seconds=HostAlive.PING_INTERVAL)

        return True

    def stop(self):
        self._need_stop = True
        if self._thread_recv_ping_result is not None:
            self._thread_recv_ping_result.join()

    def add_host(self, host_ip, method=0, param=None, check_now=False):
        if param is None:
            param = {}

        # now we support PING only
        if method != HostAlive.METHOD_PING:
            log.e('Unknown method for check host state: {}\n'.format(method))
            return False

        with self._lock:
            if host_ip not in self._states:
                self._states[host_ip] = {'last_online': 0, 'last_check': 0, 'method': method, 'param': param}
            else:
                self._states[host_ip]['method'] = method
                self._states[host_ip]['param'] = param

            if check_now:
                if method == HostAlive.METHOD_PING:
                    self._ping(host_ip)
                else:
                    log.w('Warning: check alive method not implement.\n')

    def remove_host(self, host_ip):
        with self._lock:
            if host_ip not in self._states:
                return
            del self._states[host_ip]

    def get_states(self, host_ip_list):
        with self._lock:
            ret = dict()
            time_now = int(time.time())
            for k in host_ip_list:
                if k not in self._states:
                    ret[k] = {'state': HostAlive.STATE_UNKNOWN, 'last_online': 0, 'last_check': 0}
                    continue
                if self._states[k]['last_check'] == 0:
                    ret[k] = {'state': HostAlive.STATE_UNKNOWN, 'last_online': 0, 'last_check': time_now - self._states[k]['last_check']}
                    continue
                if self._states[k]['last_online'] == 0:
                    ret[k] = {'state': HostAlive.STATE_WARNING, 'last_online': 0, 'last_check': time_now - self._states[k]['last_check']}

                if time_now - self._states[k]['last_online'] > 2 * 60:
                    _state = HostAlive.STATE_OFFLINE
                elif time_now - self._states[k]['last_online'] > 60:
                    _state = HostAlive.STATE_WARNING
                else:
                    _state = HostAlive.STATE_ONLINE
                ret[k] = {'state': _state, 'last_online': self._states[k]['last_online'], 'last_check': time_now - self._states[k]['last_check']}

        return ret

    def _check_alive(self):
        with self._lock:
            self._ping_pkg_id_list.clear()
            for k in self._states.keys():
                if self._states[k]['method'] == HostAlive.METHOD_PING:
                    self._ping(k)

    # def _show_alive(self):
    #     with self._lock:
    #         log.v('-------------')
    #         time_now = time.time()
    #         for k in self._states.keys():
    #             if time_now - self._states[k]['last_online'] > 2 * 60:
    #                 state = 'OFF-LINE'
    #             elif time_now - self._states[k]['last_online'] > 60:
    #                 state = 'Maybe off-line'
    #             else:
    #                 state = 'ON-LINE'
    #
    #             print('{:>15s}  {}'.format(k, state))

    def _ping(self, host_ip):
        pkg_data, pkg_id = self._make_ping_packet()
        return self._send_icmp_request(host_ip, pkg_id, pkg_data)

    def _send_icmp_request(self, target_ip, pkg_id, icmp_pkg):
        with self._lock:
            if target_ip not in self._states:
                return False

            self._states[target_ip]['last_check'] = int(time.time())
            self._ping_pkg_id_list[pkg_id] = target_ip

        self._socket_ping.sendto(icmp_pkg, (target_ip, 1))

        return True

    def _make_ping_packet(self):
        self._base_ping_pkg_id += 1
        if self._base_ping_pkg_id > 65530:
            self._base_ping_pkg_id = 1
        pkg_id = self._base_ping_pkg_id

        pkg_type = HostAlive.ICMP_ECHO_REQUEST
        pkg_code = 0        # must be zero
        pkg_sequence = 1    # sequence number
        pkg_payload = b'12345678901234567890123456789012'  # 32B payload data
        icmp_checksum = 0

        # type(1B), code(1B), checksum(2B), id(2B), sequence(2B), payload
        icmp_packet = struct.pack('>BBHHH32s', pkg_type, pkg_code, icmp_checksum, pkg_id, pkg_sequence, pkg_payload)
        icmp_checksum = calc_icmp_checksum(icmp_packet)
        icmp_packet = struct.pack('>BBHHH32s', pkg_type, pkg_code, icmp_checksum, pkg_id, pkg_sequence, pkg_payload)
        return icmp_packet, pkg_id

    def _thread_func_recv_ping_result(self):
        while not self._need_stop:
            event = select.select([self._socket_ping], [], [], 1)
            if not event[0]:
                continue
            data, _ = self._socket_ping.recvfrom(128)    # data-length=60
            if len(data) < 28:
                continue
            _type, _code, _checksum, _pkg_id, _sequence = struct.unpack(">BBHHH", data[20:28])
            if _type != 0 or _sequence != 1:
                continue

            time_now = int(time.time())
            with self._lock:
                if _pkg_id not in self._ping_pkg_id_list:
                    continue

                target_host = self._ping_pkg_id_list[_pkg_id]
                del self._ping_pkg_id_list[_pkg_id]

                time_used = time_now - self._states[target_host]['last_check']
                if time_used <= HostAlive.PING_TIMEOUT:
                    self._states[target_host]['last_online'] = time_now

        log.v('thread for receive PING result stopped.\n')


def tp_host_alive():
    """
    取得远程主机存活状态检查器的唯一实例

    :rtype : HostAlive
    """

    import builtins
    if '__host_alive__' not in builtins.__dict__:
        builtins.__dict__['__host_alive__'] = HostAlive()
    return builtins.__dict__['__host_alive__']
