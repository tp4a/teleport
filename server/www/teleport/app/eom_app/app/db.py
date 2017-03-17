# -*- coding: utf-8 -*-

import builtins
import os
import sqlite3
import threading

from eom_common.eomcore.logger import log
from .configs import app_cfg
from .database.create import create_and_init, TELEPORT_DATABASE_VERSION

cfg = app_cfg()

__all__ = ['get_db']


# 注意，每次调整数据库结构，必须增加版本号，并且在升级接口中编写对应的升级操作
# TELEPORT_DATABASE_VERSION = 2


class TPDatabase:
    def __init__(self):
        if '__teleport_db__' in builtins.__dict__:
            raise RuntimeError('TPDatabase object exists, you can not create more than one instance.')

        self._table_prefix = ''

        self.need_create = False  # 数据尚未存在，需要创建
        self.need_upgrade = False  # 数据库已存在但版本较低，需要升级
        self._conn_pool = None

    @property
    def table_prefix(self):
        return self._table_prefix

    def init_mysql(self):
        # NOT SUPPORTED YET
        pass

    def init_sqlite(self, db_file):
        self._table_prefix = 'ts_'
        self._conn_pool = TPSqlitePool(db_file)

        if not os.path.exists(db_file):
            log.w('database need create.\n')
            self.need_create = True
            return

        # 看看数据库中是否存在用户表（如果不存在，可能是一个空数据库文件），则可能是一个新安装的系统
        ret = self.query('SELECT COUNT(*) FROM `sqlite_master` WHERE `type`="table" AND `name`="{}account";'.format(self._table_prefix))
        if ret is None or ret[0][0] == 0:
            log.w('database need create.\n')
            self.need_create = True
            return

        # 尝试从配置表中读取当前数据库版本号（如果不存在，说明是比较旧的版本了，则置为0）
        ret = self.query('SELECT `value` FROM {}config WHERE `name`="db_ver";'.format(self._table_prefix))
        if ret is None or 0 == len(ret):
            log.w('database need upgrade.\n')
            self.need_upgrade = True

    def query(self, sql):
        return self._conn_pool.query(sql)

    def exec(self, sql):
        return self._conn_pool.exec(sql)

    def create_and_init(self, step_begin, step_end):
        step_begin('准备创建数据表')
        if create_and_init(self, step_begin, step_end):
            self.need_create = False
            return True
        else:
            return False


class TPDatabasePool:
    def __init__(self):
        self._locker = threading.RLock()
        self._connections = dict()

    def query(self, sql):
        _conn = self._get_connect()
        if _conn is None:
            return None
        return self._do_query(_conn, sql)

    def exec(self, sql):
        _conn = self._get_connect()
        if _conn is None:
            return False
        return self._do_exec(_conn, sql)

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
        return None

    def _do_exec(self, conn, sql):
        return None


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
            return None
        finally:
            cursor.close()

    def _do_exec(self, conn, sql):
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            conn.commit()
            return True
        except sqlite3.OperationalError:
            return False
        finally:
            cursor.close()


def get_db():
    """
    :rtype : TPDatabase
    """
    if '__teleport_db__' not in builtins.__dict__:
        builtins.__dict__['__teleport_db__'] = TPDatabase()
    return builtins.__dict__['__teleport_db__']
