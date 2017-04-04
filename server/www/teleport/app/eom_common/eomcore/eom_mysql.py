# -*- coding: utf-8 -*-

import pymysql
import threading
from .logger import *

mysql_pool = None


def get_mysql_pool():
    global mysql_pool
    if mysql_pool is None:
        mysql_pool = MySqlPool()
    return mysql_pool


class MySQL:

    def __init__(self, host, user, pwd, db, port=3306):
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.db = db
        self.login_timeout = 3
        self.conn = None

    def connect(self):
        """
        得到连接信息
        返回: conn.cursor()
        """
        if not self.db:
            raise (NameError, "没有设置数据库信息")
        # self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.pwd,
        # login_timeout=self.login_timeout, database=self.db, charset="utf8")
        try:
            if self.conn is not None:
                self.conn.ping()
            else:
                self.conn = pymysql.connect(host=self.host,
                                        user=self.user,
                                        passwd=self.pwd,
                                        db=self.db,
                                        port=self.port,
                                        connect_timeout=self.login_timeout,
                                        charset='utf8')
        except pymysql.err.OperationalError:
            log.e('pymsql 连接数据库失败[%s:%d]\n' % (self.host, self.port))
            return None
        except Exception as e:
            log.e('con 连接数据库失败[%s:%d]\n' % (self.host, self.port))
            return None

        cur = self.conn.cursor()
        if not cur:
            log.e('cur 连接数据库失败[%s:%d]\n' % (self.host, self.port))
            raise (NameError, "连接数据库失败")
        else:
            return cur

    # 调用实例 ms.ExecProcQuery('exec P_Agent_Cmd_Get @CmdGroupId=7')
    def ExecProcQuery(self, sql):
        try:
            if self.connect() is None:
                self.conn = None
                return None

            cur = self.conn.cursor()

            cur.execute(sql)

            resList = cur.fetchall()
            self.conn.commit()
        except pymysql.OperationalError as e:
            if self.conn is not None:
                self.conn.close()
            log.e('ExecProcQuery[%s,%s]\n' % (sql, str(e)))
            return None
        except Exception as e:
            if self.conn is not None:
                self.conn.close()
            log.e('ExecProcQuery[%s,%s]\n' % (sql, str(e)))
            return None
        return resList

    def ExecProcNonQuery(self, sql):
        try:

            if self.connect() is None:
                self.conn = None
                return False

            cur = self.conn.cursor()
            cur.execute(sql)
            self.conn.commit()
            return True
        except pymysql.OperationalError as e:
            # self.conn.close()
            if self.conn is not None:
                self.conn.close()
            log.e('ExecProcNonQuery[%s,%s]\n' % (sql, str(e)))
            return False
        except Exception as e:
            if self.conn is not None:
                self.conn.close()
            log.e('ExecProcNonQuery[%s,%s]\n' % (sql, str(e)))
            return False

    @staticmethod
    def ExecNonQuery(mysql, sql):
        try:
            if mysql.connect() is None:
                mysql.conn = None
                return False

            cur = mysql.conn.cursor()
            cur.execute(sql)
            # self.conn.commit()
            return True
        except pymysql.OperationalError as e:
            # self.conn.close()
            if mysql.conn is not None:
                mysql.conn.close()
            log.e('ExecProcNonQuery[%s,%s]\n' % (sql, str(e)))
            return False
        except Exception as e:
            if mysql.conn is not None:
                mysql.conn.close()
            log.e('ExecProcNonQuery[%s,%s]\n' % (sql, str(e)))
            return False

    @staticmethod
    def EndExecNonQuery(mysql):
        try:
            if mysql is None or mysql.conn is None:
                return False
            mysql.conn.commit()
            return True
        except pymysql.OperationalError as e:
            # self.conn.close()
            if mysql.conn is not None:
                mysql.conn.close()
            return False
        except Exception as e:
            if mysql.conn is not None:
                mysql.conn.close()
            return False

    def CallProc(self, proc_name, in_args, out_in_args=None):
        sql = ''
        ret_code = list()
        try:
            # print(in_args)
            result = list()

            self.connect()

            cur = self.conn.cursor()
            cur.callproc(proc_name, in_args)
            #

            data_set = cur.fetchall()
            result.append(data_set)
            while True:
                has_set = cur.nextset()
                if not has_set:
                    break
                data_set = cur.fetchall()
                result.append(data_set)

            cur.execute('select 0;')
            self.conn.commit()

            if out_in_args is not None:
                sql = 'select '
                for item in out_in_args:
                    str_item = '@_{0}_{1},'.format(proc_name, item)
                    sql += str_item

                sql = sql[:-1]
                code = cur.execute(sql)
                # code = cur.execute('select @_p_test_1_2,@_p_test_1_3,@_p_test_1_4')
                # ret_code = list()
                if code == 1:
                    (data_set,) = cur.fetchall()
                    length = len(data_set)
                    for i in range(length):
                        ret_code.append(data_set[i])
            return result, ret_code

        except pymysql.OperationalError as e:
            if self.conn is not None:
                self.conn.close()
            log.e('ExecProcNonQuery[%s,%s]\n' % (sql, str(e)))
            return None
        except Exception as e:
            if self.conn is not None:
                self.conn.close()
            log.e('ExecProcNonQuery[%s,%s]\n' % (sql, str(e)))
            return None


class MySqlPool:
    def __init__(self):
        self._conn_log = dict()
        self._conn_sys = dict()
        self._conn_common = dict()
        self._db_ip = ''
        self._db_port = 0
        self._db_user = ''
        self._db_pass = ''
        self._locker_log = threading.RLock()
        self._locker_sys1 = threading.RLock()
        self._locker_sys2 = threading.RLock()

    def init(self, db_ip, db_port, db_user, db_pass):
        self._db_ip = db_ip
        self._db_port = db_port
        self._db_user = db_user
        self._db_pass = db_pass

    def get_websqlcon(self):
        with self._locker_log:
            thread_id = threading.get_ident()
            if thread_id not in self._conn_log:
                my_sql = MySQL(self._db_ip, self._db_user, self._db_pass, 'ts_web', self._db_port)
                self._conn_log[thread_id] = my_sql
                return my_sql

            my_sql = self._conn_log[thread_id]
        return my_sql

    def get_tssqlcon(self):
        with self._locker_sys1:
            thread_id = threading.get_ident()
            if thread_id not in self._conn_sys:
                my_sql = MySQL(self._db_ip, self._db_user, self._db_pass, 'ts_db', self._db_port)
                self._conn_sys[thread_id] = my_sql
                return my_sql

            my_sql = self._conn_sys[thread_id]
        return my_sql
