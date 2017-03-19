# coding=utf-8
#
# Created: 04/02/2012
# -------------------------------------------------------------------------------

import os
import sqlite3
import threading

from .logger import log

sqlite_pool = None


def get_sqlite_pool():
    global sqlite_pool
    if sqlite_pool is None:
        sqlite_pool = SqlitePool()
    return sqlite_pool


class eom_sqlite:
    """
    """

    def __init__(self, path):
        self._db_file = path
        self._conn = None

    def connect(self):
        # if not os.path.exists(self._db_file):
        #     return None
        try:
            self._conn = sqlite3.connect(self._db_file)
        except:
            self._conn = None
            raise RuntimeError('can not open database.')
        return self._conn

    def ExecProcQuery(self, sql):
        if self._conn is None:
            if self.connect() is None:
                return None
        cursor = self._conn.cursor()
        try:

            cursor.execute(sql)
            db_ret = cursor.fetchall()
            return db_ret
        except Exception:
            return None
        finally:
            cursor.close()

    def ExecProcNonQuery(self, sql):
        if self._conn is None:
            if self.connect() is None:
                return False

        cursor = self._conn.cursor()
        try:
            cursor.execute(sql)
            self._conn.commit()
        except Exception:
            log.e('can not create/open database.\n')
            return False
        finally:
            cursor.close()

        return True

    def ExecManyProcNonQuery(self, sql):
        if self._conn is None:
            if self.connect() is None:
                return False

        cursor = self._conn.cursor()
        try:
            cursor.executescript(sql)
            self._conn.commit()
            cursor.close()
        except Exception as e:
            log.e('can not create/open database.\n')
            return False

        return True

    def close(self):
        self._conn.close()
        self._conn = None


class SqlitePool:
    def __init__(self):
        self._conn_sys = dict()
        self._path = ''
        self._locker_sys = threading.RLock()
        self._config_server_ip = ''

    def init(self, path):
        self._conn_sys.clear()
        self._path = os.path.join(path, 'ts_db.db')
        log.w('use sqlite database, db file: {}\n'.format(self._path))
        if not os.path.exists(self._path):
            return False

        try:
            sql_con = self.get_tssqlcon()
            str_sql = 'SELECT value FROM ts_config WHERE name=\"ts_server_ip\";'
            db_ret = sql_con.ExecProcQuery(str_sql)
            self._config_server_ip = db_ret[0][0]
        except Exception:
            self._config_server_ip = '127.0.0.1'
        return True

    def init_full_path(self, full_path):
        self._conn_sys.clear()
        self._path = full_path
        if not os.path.exists(self._path):
            return False

        try:
            sql_con = self.get_tssqlcon()
            str_sql = 'SELECT value FROM ts_config WHERE name=\"ts_server_ip\";'
            db_ret = sql_con.ExecProcQuery(str_sql)
            self._config_server_ip = db_ret[0][0]
        except Exception:
            self._config_server_ip = '127.0.0.1'
        return True

    def get_config_server_ip(self):
        return self._config_server_ip

    def get_tssqlcon(self):
        with self._locker_sys:
            thread_id = threading.get_ident()
            if thread_id not in self._conn_sys:
                _eom_sqlite = eom_sqlite(self._path)
                self._conn_sys[thread_id] = _eom_sqlite
            else:
                _eom_sqlite = self._conn_sys[thread_id]

        return _eom_sqlite

    def close(self):
        with self._locker_sys:
            thread_id = threading.get_ident()
            if thread_id not in self._conn_sys:
                return
            else:
                _eom_sqlite = self._conn_sys[thread_id]
                self._conn_sys.pop(thread_id)
                _eom_sqlite.close()
