# -*- coding: utf-8 -*-

import pickle

from pymemcache.client.base import Client as mem_client
from .configs import app_cfg

cfg = app_cfg()

SESSION_EXPIRE = 3600  # 60*60


# SESSION_EXPIRE = 1800 # 30*60
# SESSION_EXPIRE = 30

class SwxSession:
    """
    :type _mem_client: pymemcache.client.base.Client
    """

    def __init__(self):
        import builtins
        if '__swx_session__' in builtins.__dict__:
            raise RuntimeError('SwxSession object exists, you can not create more than one instance.')
        self._session_dict = dict()

    def init(self):
        return True

    def add(self, s_id, value):
        self._session_dict[s_id] = value

    def set(self, s_id, value):
        self._session_dict[s_id] = value

    def get(self, s_id, _default=None):
        if s_id in self._session_dict:
            v = self._session_dict[s_id]
        else:
            v = _default
        return v


def swx_session():
    """
    取得 SwxSession 的唯一实例

    :rtype : SwxSession
    """

    import builtins
    if '__swx_session__' not in builtins.__dict__:
        builtins.__dict__['__swx_session__'] = SwxSession()
    return builtins.__dict__['__swx_session__']
