# -*- coding: utf-8 -*-

import datetime
import threading

from app.const import *
from app.base.configs import tp_cfg
from app.base.cron import tp_cron
import app.model.system as system_model


class IntegrationManager(object):
    """
    第三方系统集成密钥-内存缓存管理
    """

    def __init__(self):
        super().__init__()

        import builtins
        if '__integration_manager__' in builtins.__dict__:
            raise RuntimeError('IntegrationManager object exists, you can not create more than one instance.')

        # 密钥表，access-key为索引，每个项为一个字典，包括 n(name), s(access-secret), i(id), r(role_id), p(privilege)
        self._keys = dict()

        self._lock = threading.RLock()

    def init(self):
        # load from database.
        err, _, _, recorder = system_model.get_integration(with_acc_sec=True)
        if err != TPE_OK:
            return False
        # print(recorder)
        # [{'id': 8, 'acc_key': 'TPRTn6c7xMW7ci7f', 'name': 'test-audit', 'comment': '日常审计操作', 'acc_sec': 'y3NcQZPdy76kPQmNz7nTik72S8JrTmnp', 'role_id': 3, 'role_name': '审计员', 'privilege': 32769}, ...]
        for i in recorder:
            self._keys[i['acc_key']] = {
                'name': i['name'],
                'secret': i['acc_sec'],
                'id': i['id'],
                'role_id': i['role_id'],
                'privilege': i['privilege']
            }

        # tp_cron().add_job('session_expire', self._check_expire, first_interval_seconds=None, interval_seconds=60)
        return True

    def get_secret(self, acc_key):
        with self._lock:
            return None if acc_key not in self._keys else self._keys[acc_key]

    def update_by_id(self, _id, acc_key, acc_sec, name, role_id, privilege):
        with self._lock:
            if acc_key in self._keys:
                self._keys[acc_key]['id'] = _id
                self._keys[acc_key]['name'] = name
                self._keys[acc_key]['role_id'] = role_id
                self._keys[acc_key]['privilege'] = privilege
            else:
                self._keys[acc_key] = {
                    'id': _id,
                    'secret': '',
                    'name': name,
                    'role_id': role_id,
                    'privilege': privilege
                }
            if acc_sec is not None:
                self._keys[acc_key]['secret'] = acc_sec

            print(self._keys)

    def update_by_role_id(self, role_id, privilege):
        with self._lock:
            for i in self._keys:
                if self._keys[i]['role_id'] == role_id:
                    self._keys[i]['privilege'] = privilege

            print(self._keys)

    def remove_by_id(self, ids):
        with self._lock:
            key_to_remove = list()
            for i in self._keys:
                if self._keys[i]['id'] in ids:
                    key_to_remove.append(i)
            for k in key_to_remove:
                del self._keys[k]

            print(self._keys)


def tp_integration():
    """
    取得第三方服务集成密钥管理器的唯一实例

    :rtype : IntegrationManager
    """

    import builtins
    if '__integration_manager__' not in builtins.__dict__:
        builtins.__dict__['__integration_manager__'] = IntegrationManager()
    return builtins.__dict__['__integration_manager__']
