# -*- coding: utf-8 -*-

import datetime
import threading

from app.base.configs import tp_cfg
from app.base.cron import tp_cron


class SessionManager(object):

    _expire = 3600

    def __init__(self):
        super().__init__()

        import builtins
        if '__session_manager__' in builtins.__dict__:
            raise RuntimeError('SessionManager object exists, you can not create more than one instance.')

        # session表，session_id为索引，每个项为一个字典，包括 v(value), t(last access), e(expire seconds)
        self._session_dict = dict()

        self._expire = 0
        self._lock = threading.RLock()
        self._stop_flag = False
        self._timer_cond = threading.Condition()

    def init(self):
        self.update_default_expire()
        tp_cron().add_job('session_expire', self._check_expire, first_interval_seconds=None, interval_seconds=60)
        return True

    def update_default_expire(self):
        self._expire = tp_cfg().sys.login.session_timeout * 60

    def _check_expire(self):
        _now = int(datetime.datetime.utcnow().timestamp())
        with self._lock:
            _keys = [k for k in self._session_dict]
            for k in _keys:
                if self._session_dict[k]['e'] == 0:
                    continue
                if _now - self._session_dict[k]['t'] > self._session_dict[k]['e']:
                    del self._session_dict[k]

    def set(self, s_id, value, expire=None):
        """
        设置一个会话数据，如果expire为负数，则立即删除已经存在的名为s_id的会话，如果expire为0，则此会话数据永不过期。expire的单位为秒。
        @param s_id: string
        @param value: string
        @param expire: integer
        @return: None
        """

        if expire is None:
            expire = tp_cfg().sys.login.session_timeout * 60

        if expire < 0:
            with self._lock:
                if s_id in self._session_dict:
                    del self._session_dict[s_id]
        else:
            self._session_dict[s_id] = {'v': value, 't': int(datetime.datetime.utcnow().timestamp()), 'e': expire}

    def get(self, s_id, _default=None):
        # 从session中获取一个数据（读取并更新最后访问时间）
        with self._lock:
            if s_id in self._session_dict:
                if self._session_dict[s_id]['e'] == 0:
                    return self._session_dict[s_id]['v']
                else:
                    if int(datetime.datetime.utcnow().timestamp()) - self._session_dict[s_id]['t'] > self._session_dict[s_id]['e']:
                        del self._session_dict[s_id]
                        return _default
                    else:
                        self._session_dict[s_id]['t'] = int(datetime.datetime.utcnow().timestamp())
                        return self._session_dict[s_id]['v']

            else:
                return _default

    def get_start_with(self, key_start):
        with self._lock:
            ret = {}
            for k in self._session_dict:
                if k.startswith(key_start):
                    ret[k] = self._session_dict[k]

            return ret

    def taken(self, s_id, _default=None):
        # 从session中取走一个数据（读取并删除）
        with self._lock:
            if s_id in self._session_dict:
                ret = self._session_dict[s_id]['v']
                del self._session_dict[s_id]
                return ret
            else:
                return _default


def tp_session():
    """
    取得Session管理器的唯一实例

    :rtype : SessionManager
    """

    import builtins
    if '__session_manager__' not in builtins.__dict__:
        builtins.__dict__['__session_manager__'] = SessionManager()
    return builtins.__dict__['__session_manager__']
