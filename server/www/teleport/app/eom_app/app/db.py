# -*- coding: utf-8 -*-

import os
import threading
import sqlite3
import builtins

from .configs import app_cfg
from eom_common.eomcore.logger import log

cfg = app_cfg()

__all__ = ['get_db']

# 注意，每次调整数据库结构，必须增加版本号，并且在升级接口中编写对应的升级操作
TELEPORT_DATABASE_VERSION = 2


class TPDatabase:
    def __init__(self):
        if '__teleport_db__' in builtins.__dict__:
            raise RuntimeError('TPDatabase object exists, you can not create more than one instance.')

        self.need_create = False  # 数据尚未存在，需要创建
        self.need_upgrade = False  # 数据库已存在但版本较低，需要升级
        self._conn_pool = None

    def init_mysql(self):
        # NOT SUPPORTED YET
        pass

    def init_sqlite(self, db_file):
        self._conn_pool = TPSqlitePool(db_file)

        if not os.path.exists(db_file):
            log.w('database need create.\n')
            self.need_create = True
            return

        # 看看数据库中是否存在用户表（如果不存在，可能是一个空数据库文件），则可能是一个新安装的系统
        ret = self._conn_pool.query('SELECT COUNT(*) FROM sqlite_master where type="table" and name="ts_account";')
        if ret[0][0] == 0:
            log.w('database need create.\n')
            self.need_create = True
            return

        # 尝试从配置表中读取当前数据库版本号（如果不存在，说明是比较旧的版本了，则置为0）
        ret = self._conn_pool.query('SELECT value FROM ts_config where name="db_ver";')
        if 0 == len(ret):
            log.w('database need upgrade.\n')
            self.need_upgrade = True


class TPDatabasePool:
    def __init__(self):
        self._locker = threading.RLock()
        self._connections = dict()

    def query(self, sql):
        _conn = self._get_connect()
        if _conn is None:
            return list()
        return self._do_query(_conn, sql)

    def _get_connect(self):
        with self._locker:
            thread_id = threading.get_ident()
            if thread_id not in self._connections:
                _conn = self._do_connect()
                self._connections[thread_id] = _conn
            else:
                _conn = self._connections[thread_id]

        return _conn

    def _do_connect(self):
        return None

    def _do_query(self, conn, sql):
        return list()


class TPSqlitePool(TPDatabasePool):
    def __init__(self, db_file):
        super().__init__()
        self._db_file = db_file

    def _do_connect(self):
        try:
            return sqlite3.connect(self._db_file)
        except:
            log.e('[sqlite] can not connect, does the database file correct?')
            return None

    def _do_query(self, conn, sql):
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            db_ret = cursor.fetchall()
            return db_ret
        except sqlite3.OperationalError:
            return list()
        finally:
            cursor.close()


def get_db():
    """
    :rtype : TPDatabase
    """
    if '__teleport_db__' not in builtins.__dict__:
        builtins.__dict__['__teleport_db__'] = TPDatabase()
    return builtins.__dict__['__teleport_db__']
