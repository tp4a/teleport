# -*- coding: utf-8 -*-

import os
import sqlite3
import pymysql
import threading

import builtins

from eom_app.app.configs import app_cfg
from eom_common.eomcore import utils
from eom_common.eomcore.logger import log
from .database.create import create_and_init
from .database.upgrade import DatabaseUpgrade
from .database.export import export_database

__all__ = ['get_db', 'DbItem']


class TPDatabase:
    # 注意，每次调整数据库结构，必须增加版本号，并且在升级接口中编写对应的升级操作
    DB_VERSION = 5

    DB_TYPE_UNKNOWN = 0
    DB_TYPE_SQLITE = 1
    DB_TYPE_MYSQL = 2

    def __init__(self):
        if '__teleport_db__' in builtins.__dict__:
            raise RuntimeError('TPDatabase object exists, you can not create more than one instance.')

        self.db_type = self.DB_TYPE_UNKNOWN
        self.sqlite_file = ''
        self.mysql_host = ''
        self.mysql_port = 0
        self.mysql_db = ''
        self.mysql_user = ''
        self.mysql_password = ''

        self.need_create = False  # 数据尚未存在，需要创建
        self.need_upgrade = False  # 数据库已存在但版本较低，需要升级
        self.current_ver = 0

        self.auto_increment = ''

        self._table_prefix = ''
        self._conn_pool = None

    @property
    def table_prefix(self):
        return self._table_prefix

    def init(self):
        cfg = app_cfg()
        if 'sqlite' == cfg.database.type:
            if cfg.database.sqlite_file is None:
                cfg.set_default('database::sqlite-file', os.path.join(cfg.data_path, 'db', 'ts_db.db'))
            if not self._init_sqlite(cfg.database.sqlite_file):
                return False
        elif 'mysql' == cfg.database.type:
            if not self._init_mysql(cfg.database.mysql_host, cfg.database.mysql_port,
                                    cfg.database.mysql_db, cfg.database.mysql_prefix,
                                    cfg.database.mysql_user, cfg.database.mysql_password):
                return False
        else:
            log.e('unknown database type `{}`, support sqlite/mysql now.\n'.format(cfg.database.type))
            return False

        # 看看数据库中是否存在指定的数据表（如果不存在，可能是一个空数据库文件），则可能是一个新安装的系统
        # ret = self.query('SELECT COUNT(*) FROM `sqlite_master` WHERE `type`="table" AND `name`="{}account";'.format(self._table_prefix))
        ret = self.is_table_exists('{}group'.format(self._table_prefix))
        if ret is None or not ret:
            log.w('database need create.\n')
            self.need_create = True
            return True

        # 尝试从配置表中读取当前数据库版本号（如果不存在，说明是比较旧的版本了）
        ret = self.query('SELECT `value` FROM `{}config` WHERE `name`="db_ver";'.format(self._table_prefix))
        if ret is None or 0 == len(ret):
            self.current_ver = 1
        else:
            self.current_ver = int(ret[0][0])

        if self.current_ver < self.DB_VERSION:
            log.w('database need upgrade.\n')
            self.need_upgrade = True
            return True

        # DO TEST
        # self.alter_table('ts_account', [['account_id', 'id'], ['account_type', 'type']])

        return True

    def _init_sqlite(self, db_file):
        self.db_type = self.DB_TYPE_SQLITE
        self.auto_increment = 'AUTOINCREMENT'
        self.sqlite_file = db_file

        self._table_prefix = 'ts_'
        self._conn_pool = TPSqlitePool(db_file)

        if not os.path.exists(db_file):
            log.w('database need create.\n')
            self.need_create = True
            return True

        return True

    def _init_mysql(self, mysql_host, mysql_port, mysql_db, mysql_prefix, mysql_user, mysql_password):
        self.db_type = self.DB_TYPE_MYSQL
        self.auto_increment = 'AUTO_INCREMENT'

        self._table_prefix = mysql_prefix
        self.mysql_host = mysql_host
        self.mysql_port = mysql_port
        self.mysql_db = mysql_db
        self.mysql_user = mysql_user
        self.mysql_password = mysql_password

        self._conn_pool = TPMysqlPool(mysql_host, mysql_port, mysql_db, mysql_user, mysql_password)

        return True

    # def init__(self, db_source):
    #     self.db_source = db_source
    #
    #     if db_source['type'] == self.DB_TYPE_MYSQL:
    #         log.e('MySQL not supported yet.')
    #         return False
    #     elif db_source['type'] == self.DB_TYPE_SQLITE:
    #         self._table_prefix = 'ts_'
    #         self._conn_pool = TPSqlitePool(db_source['file'])
    #
    #         if not os.path.exists(db_source['file']):
    #             log.w('database need create.\n')
    #             self.need_create = True
    #             return True
    #     else:
    #         log.e('Unknown database type: {}'.format(db_source['type']))
    #         return False
    #
    #     # 看看数据库中是否存在指定的数据表（如果不存在，可能是一个空数据库文件），则可能是一个新安装的系统
    #     # ret = self.query('SELECT COUNT(*) FROM `sqlite_master` WHERE `type`="table" AND `name`="{}account";'.format(self._table_prefix))
    #     ret = self.is_table_exists('{}group'.format(self._table_prefix))
    #     if ret is None or not ret:
    #         log.w('database need create.\n')
    #         self.need_create = True
    #         return True
    #
    #     # 尝试从配置表中读取当前数据库版本号（如果不存在，说明是比较旧的版本了）
    #     ret = self.query('SELECT `value` FROM `{}config` WHERE `name`="db_ver";'.format(self._table_prefix))
    #     if ret is None or 0 == len(ret):
    #         self.current_ver = 1
    #     else:
    #         self.current_ver = int(ret[0][0])
    #
    #     if self.current_ver < self.DB_VERSION:
    #         log.w('database need upgrade.\n')
    #         self.need_upgrade = True
    #         return True
    #
    #     # DO TEST
    #     # self.alter_table('ts_account', [['account_id', 'id'], ['account_type', 'type']])
    #
    #     return True

    def is_table_exists(self, table_name):
        """
        判断指定的表是否存在
        @param table_name: string
        @return: None or Boolean
        """
        if self.db_type == self.DB_TYPE_SQLITE:
            ret = self.query('SELECT COUNT(*) FROM `sqlite_master` WHERE `type`="table" AND `name`="{}";'.format(table_name))
            if ret is None:
                return None
            if len(ret) == 0:
                return False
            if ret[0][0] == 0:
                return False
            return True
        elif self.db_type == self.DB_TYPE_MYSQL:
            # select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='dbname' and TABLE_NAME='tablename' ;
            ret = self.query('SELECT TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA="{}" and TABLE_NAME="{}";'.format(self.mysql_db, table_name))
            if ret is None:
                return None
            if len(ret) == 0:
                return None
            else:
                return True
        else:
            log.e('Unknown database type.\n')
            return None

    def query(self, sql):
        # _start = datetime.datetime.utcnow().timestamp()
        ret = self._conn_pool.query(sql)
        # _end = datetime.datetime.utcnow().timestamp()
        # log.d('[db] {}\n'.format(sql))
        # log.d('[db]   cost {} seconds.\n'.format(_end - _start))
        return ret

    def exec(self, sql):
        # _start = datetime.datetime.utcnow().timestamp()
        ret = self._conn_pool.exec(sql)
        # _end = datetime.datetime.utcnow().timestamp()
        # log.d('[db] {}\n'.format(sql))
        # log.d('[db]   cost {} seconds.\n'.format(_end - _start))
        return ret

    def transaction(self, sql_list):
        # _start = datetime.datetime.utcnow().timestamp()
        ret = self._conn_pool.transaction(sql_list)
        # _end = datetime.datetime.utcnow().timestamp()
        # log.d('[db] transaction\n')
        # log.d('[db]   cost {} seconds.\n'.format(_end - _start))
        return ret

    def last_insert_id(self):
        return self._conn_pool.last_insert_id()

    def create_and_init(self, step_begin, step_end):
        log.v('start database create and initialization process.\n')

        if self.db_type == self.DB_TYPE_SQLITE:
            db_path = os.path.dirname(self.sqlite_file)
            if not os.path.exists(db_path):
                utils.make_dir(db_path)
                if not os.path.exists(db_path):
                    log.e('can not create folder `{}` to store database file.\n'.format(db_path))
                    return False
            # 创建一个空数据文件，这样才能进行connect。
            if not os.path.exists(self.sqlite_file):
                try:
                    with open(self.sqlite_file, 'w') as f:
                        pass
                except:
                    log.e('can not create db file `{}`.\n'.format(self.sqlite_file))
                    return False

        if create_and_init(self, step_begin, step_end):
            log.v('database created.\n')
            self.need_create = False
            return True
        else:
            log.e('database create and initialize failed.\n')
            return False

    def upgrade_database(self, step_begin, step_end):
        log.v('start database upgrade process.\n')
        if DatabaseUpgrade(self, step_begin, step_end).do_upgrade():
            log.v('database upgraded.\n')
            self.need_upgrade = False
            return True
        else:
            log.e('database upgrade failed.\n')
            return False

    def alter_table(self, table_names, field_names=None):
        """
        修改表名称及字段名称
        table_name: 如果是string，则指定要操作的表，如果是list，则第一个元素是要操作的表，第二个元素是此表改名的目标名称
        fields_names: 如果为None，则不修改字段名，否则应该是一个list，其中每个元素是包含两个str的list，表示将此list第一个指定的字段改名为第二个指定的名称
        @return: None or Boolean
        """
        # TODO: 此函数尚未完成
        if self.db_type == self.DB_TYPE_SQLITE:
            if not isinstance(table_names, list) and field_names is None:
                log.w('nothing to do.\n')
                return False

            if isinstance(table_names, str):
                old_table_name = table_names
                new_table_name = table_names
            elif isinstance(table_names, list) and len(table_names) == 2:
                old_table_name = table_names[0]
                new_table_name = table_names[1]
            else:
                log.w('invalid param.\n')
                return False

            if isinstance(field_names, list):
                for i in field_names:
                    if not isinstance(i, list) or 2 != len(i):
                        log.w('invalid param.\n')
                        return False

            if field_names is None:
                # 仅数据表改名
                return self.exec('ALTER TABLE `{}` RENAME TO `{}`;'.format(old_table_name, new_table_name))
            else:
                # sqlite不支持字段改名，所以需要通过临时表中转一下

                # 先获取数据表的字段名列表
                ret = self.query('SELECT * FROM `sqlite_master` WHERE `type`="table" AND `name`="{}";'.format(old_table_name))
                log.w('-----\n')
                log.w(ret[0][4])
                log.w('\n')

                # 先将数据表改名，成为一个临时表
                # tmp_table_name = '{}_sqlite_tmp'.format(old_table_name)
                # ret = self.exec('ALTER TABLE `{}` RENAME TO `{}`;'.format(old_table_name, tmp_table_name))
                # if ret is None or not ret:
                #     return ret

            pass
        elif self.db_type == self.DB_TYPE_MYSQL:
            log.e('mysql not supported yet.\n')
            return False
        else:
            log.e('Unknown database type.\n')
            return False

    def export_to_sql(self):
        # TODO: not implement.

        return export_database(self)


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

    def transaction(self, sql_list):
        _conn = self._get_connect()
        if _conn is None:
            return False
        return self._do_transaction(_conn, sql_list)

    def last_insert_id(self):
        _conn = self._get_connect()
        if _conn is None:
            return -1
        return self._last_insert_id(_conn)

    def _get_connect(self):
        with self._locker:
            thread_id = threading.get_ident()
            if thread_id not in self._connections:
                _conn = self._do_connect()
                if _conn is not None:
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

    def _do_transaction(self, conn, sql_list):
        return False

    def _last_insert_id(self, conn):
        return -1


class TPSqlitePool(TPDatabasePool):
    def __init__(self, db_file):
        super().__init__()
        self._db_file = db_file

    def _do_connect(self):
        if not os.path.exists(self._db_file):
            log.e('[sqlite] can not connect, database file not exists.\n')
            return None

        try:
            return sqlite3.connect(self._db_file)
        except:
            log.e('[sqlite] can not connect, does the database file correct?\n')
            return None

    def _do_query(self, conn, sql):
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            db_ret = cursor.fetchall()
            return db_ret
        except Exception as e:
            log.e('[sqlite] _do_query() failed: {}\n'.format(e.__str__()))
            log.e('[sqlite] SQL={}'.format(sql))
        finally:
            cursor.close()

    def _do_exec(self, conn, sql):
        try:
            with conn:
                conn.execute(sql)
            return True
        except Exception as e:
            log.e('[sqlite] _do_exec() failed: {}\n'.format(e.__str__()))
            log.e('[sqlite] SQL={}'.format(sql))
            return False

    def _do_transaction(self, conn, sql_list):
        try:
            # 使用context manager，发生异常时会自动rollback，正常执行完毕后会自动commit
            with conn:
                for sql in sql_list:
                    conn.execute(sql)
            return True
        except Exception as e:
            log.e('[sqlite] _do_transaction() failed: {}\n'.format(e.__str__()))
            return False

    def _last_insert_id(self, conn):
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT last_insert_rowid();')
            db_ret = cursor.fetchall()
            return db_ret[0][0]
        except Exception as e:
            log.e('[sqlite] _last_insert_id() failed: {}\n'.format(e.__str__()))
            return -1
        finally:
            cursor.close()


class TPMysqlPool(TPDatabasePool):
    def __init__(self, host, port, db_name, user, password):
        super().__init__()
        self._host = host
        self._port = port
        self._db_name = db_name
        self._user = user
        self._password = password

    def _do_connect(self):
        try:
            return pymysql.connect(host=self._host,
                                   user=self._user,
                                   passwd=self._password,
                                   db=self._db_name,
                                   port=self._port,
                                   autocommit=False,
                                   connect_timeout=3.0,
                                   charset='utf8')
        except Exception as e:
            log.e('[mysql] connect [{}:{}] failed: {}\n'.format(self._host, self._port, e.__str__()))
            return None

    def _do_query(self, conn, sql):
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            db_ret = cursor.fetchall()
            conn.commit()
            return db_ret
        except Exception as e:
            log.v('[mysql] SQL={}\n'.format(sql))
            log.e('[mysql] _do_query() failed: {}\n'.format(e.__str__()))
            return None
        finally:
            cursor.close()

    def _do_exec(self, conn, sql):
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            conn.commit()
            return True
        except Exception as e:
            log.e('[mysql] _do_exec() failed: {}\n'.format(e.__str__()))
            log.e('[mysql] SQL={}'.format(sql))
            return None
        finally:
            cursor.close()

    def _do_transaction(self, conn, sql_list):
        cursor = conn.cursor()
        try:
            conn.begin()
            for sql in sql_list:
                cursor.execute(sql)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            log.e('[mysql] _do_transaction() failed: {}\n'.format(e.__str__()))
            return False
        finally:
            cursor.close()

    def _last_insert_id(self, conn):
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT LAST_INSERT_ID();')
            db_ret = cursor.fetchall()
            conn.commit()
            return db_ret[0][0]
        except Exception as e:
            log.e('[mysql] _last_insert_id() failed: {}\n'.format(e.__str__()))
            return -1
        finally:
            cursor.close()


class DbItem(dict):
    def load(self, db_item, db_fields):
        if len(db_fields) != len(db_item):
            raise RuntimeError('!=')
        for i in range(len(db_item)):
            self[db_fields[i]] = db_item[i]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise


def get_db():
    """
    :rtype : TPDatabase
    """
    if '__teleport_db__' not in builtins.__dict__:
        builtins.__dict__['__teleport_db__'] = TPDatabase()
    return builtins.__dict__['__teleport_db__']
