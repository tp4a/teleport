# -*- coding: utf-8 -*-

# import pickle
import time
import datetime
import threading

# from pymemcache.client.base import Client as mem_client
from .configs import app_cfg
from eom_common.eomcore.logger import log

cfg = app_cfg()

SESSION_EXPIRE = 3600  # 60*60  默认超时时间为1小时


class WebSession(threading.Thread):
    """
    :type _mem_client: pymemcache.client.base.Client
    """

    def __init__(self):
        super().__init__(name='session-manager-thread')

        import builtins
        if '__web_session__' in builtins.__dict__:
            raise RuntimeError('WebSession object exists, you can not create more than one instance.')

        # session表，session_id为索引，每个项为一个字典，包括 v(Value), t(Timestamp when add or modify), e(Expire seconds)
        self._session_dict = dict()

        self._lock = threading.RLock()
        self._stop_flag = False

    def init(self):
        return True

    def stop(self):
        self._stop_flag = True
        self.join()
        log.v('{} stopped.'.format(self.name))

    def run(self):
        while True:
            _now = int(datetime.datetime.utcnow().timestamp())
            with self._lock:
                _keys = [k for k in self._session_dict]
                for k in _keys:
                    if self._session_dict[k]['e'] == 0:
                        continue
                    if _now - self._session_dict[k]['t'] > self._session_dict[k]['e']:
                        del self._session_dict[k]

            # 每隔一分钟检查一次超时的会话
            for i in range(60):
                if not self._stop_flag:
                    time.sleep(1)

    def set(self, s_id, value, expire=SESSION_EXPIRE):
        """
        设置一个会话数据，如果expire为负数，则立即删除已经存在的名为s_id的会话，如果expire为0，则此会话数据永不过期。expire的单位为秒。
        @param s_id: string
        @param value: string
        @param expire: integer
        @return: None
        """
        if expire < 0:
            with self._lock:
                if s_id in self._session_dict:
                    del self._session_dict[s_id]
        else:
            self._session_dict[s_id] = {'v': value, 't': int(datetime.datetime.utcnow().timestamp()), 'e': expire}

    def get(self, s_id, _default=None):
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


def web_session():
    """
    取得 SwxSession 的唯一实例

    :rtype : WebSession
    """

    import builtins
    if '__web_session__' not in builtins.__dict__:
        builtins.__dict__['__web_session__'] = WebSession()
    return builtins.__dict__['__web_session__']
