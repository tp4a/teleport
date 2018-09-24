# -*- coding: utf-8 -*-

import os
import sqlite3
import pymysql
import threading

import builtins

from app.const import *
from app.base.configs import tp_cfg
from app.base.utils import AttrDict, tp_make_dir
from app.base.logger import log
from .database.create import DatabaseInit
# from .database.upgrade import DatabaseUpgrade
from .database.export import export_database

__all__ = ['get_db', 'SQL']


# TODO: use SQLAlchemy


class TPDatabase:
    # 注意，每次调整数据库结构，必须增加版本号，并且在升级接口中编写对应的升级操作
    DB_VERSION = 6

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

        self.connected = False  # 数据库是否已经连接上了
        self.need_create = False  # 数据尚未存在，需要创建
        self.need_upgrade = False  # 数据库已存在但版本较低，需要升级
        self.current_ver = 0

        self.auto_increment = ''
        self.place_holder = ''

        self._table_prefix = ''
        self._conn_pool = None

    @property
    def table_prefix(self):
        return self._table_prefix

    def init(self):
        cfg = tp_cfg()
        if 'sqlite' == cfg.database.type:
            if cfg.database.sqlite_file is None:
                cfg.set_default('database::sqlite-file', os.path.join(cfg.data_path, 'db', 'teleport.db'))
            if not self._init_sqlite(cfg.database.sqlite_file):
                return False
            if self.need_create:
                return True
        elif 'mysql' == cfg.database.type:
            if not self._init_mysql(cfg.database.mysql_host, cfg.database.mysql_port,
                                    cfg.database.mysql_db, cfg.database.mysql_prefix,
                                    cfg.database.mysql_user, cfg.database.mysql_password):
                return False
        else:
            log.e('unknown database type `{}`, support sqlite/mysql now.\n'.format(cfg.database.type))
            return False

        return True

    def connect(self):
        if self._conn_pool.connect():
            self.connected = True

    def check_status(self):
        if self.need_create:
            return True
        # 看看数据库中是否存在指定的数据表（如果不存在，可能是一个空数据库文件），则可能是一个新安装的系统
        # ret = self.query('SELECT COUNT(*) FROM `sqlite_master` WHERE `type`="table" AND `name`="{}account";'.format(self._table_prefix))
        ret = self.is_table_exists('{}config'.format(self._table_prefix))
        if ret is None or not ret:
            log.w('database need create.\n')
            self.need_create = True
            return

        # 尝试从配置表中读取当前数据库版本号（如果不存在，说明是比较旧的版本了）
        ret = self.query('SELECT `value` FROM `{}config` WHERE `name`="db_ver";'.format(self._table_prefix))
        if ret is None or 0 == len(ret):
            self.current_ver = 1
        else:
            self.current_ver = int(ret[0][0])

        if self.current_ver < self.DB_VERSION:
            log.w('database need upgrade.\n')
            self.need_upgrade = True
            return

    def load_system_config(self):
        sys_cfg = dict()
        db_ret = self.query('SELECT `name`, `value` FROM `{}config`;'.format(self._table_prefix))
        for item in db_ret:
            sys_cfg[item[0]] = item[1]

        if len(sys_cfg) > 0:
            tp_cfg().update_sys(sys_cfg)

    def _init_sqlite(self, db_file):
        self.db_type = self.DB_TYPE_SQLITE
        self.auto_increment = 'AUTOINCREMENT'
        self.place_holder = '?'
        self.sqlite_file = db_file

        self._table_prefix = 'tp_'
        self._conn_pool = TPSqlitePool(db_file)

        if not os.path.exists(db_file):

            p = os.path.dirname(os.path.abspath(db_file))
            if not os.path.exists(p):
                os.makedirs(p)

            log.w('database need create.\n')
            self.need_create = True
            return True

        return True

    def _init_mysql(self, mysql_host, mysql_port, mysql_db, mysql_prefix, mysql_user, mysql_password):
        self.db_type = self.DB_TYPE_MYSQL
        self.auto_increment = 'AUTO_INCREMENT'
        self.place_holder = '%s'

        self._table_prefix = mysql_prefix
        self.mysql_host = mysql_host
        self.mysql_port = mysql_port
        self.mysql_db = mysql_db
        self.mysql_user = mysql_user
        self.mysql_password = mysql_password

        self._conn_pool = TPMysqlPool(mysql_host, mysql_port, mysql_db, mysql_user, mysql_password)

        return True

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
            ret = self.query('SELECT TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA="{}" and TABLE_NAME="{}";'.format(self.mysql_db, table_name))
            if ret is None:
                return None
            if len(ret) == 0:
                return False
            else:
                return True
        else:
            log.e('Unknown database type.\n')
            return None

    def is_field_exists(self, table_name, field_name):
        if self.db_type == self.DB_TYPE_SQLITE:
            ret = self.query('PRAGMA table_info(`{}`);'.format(table_name))
            if ret is None:
                return None
            if len(ret) == 0:
                return False
            else:
                for f in ret:
                    if f[1] == field_name:
                        return True
                return False
        elif self.db_type == self.DB_TYPE_MYSQL:
            ret = self.query('DESC `{}` `{}`;'.format(table_name, field_name))
            if ret is None:
                return None
            if len(ret) == 0:
                return False
            else:
                return True
        else:
            log.e('Unknown database type.\n')
            return None

    def query(self, sql, args=None):
        if self.need_create:
            return None
        if self.db_type == self.DB_TYPE_SQLITE and args is None:
            args = ()

        # log.d('[db] {}, {}\n'.format(sql, args))
        # _start = datetime.datetime.utcnow().timestamp()
        ret = self._conn_pool.query(sql, args)
        # _end = datetime.datetime.utcnow().timestamp()
        # log.d('[db]   cost {} seconds.\n'.format(_end - _start))
        return ret

    def exec(self, sql, args=None):
        if self.db_type == self.DB_TYPE_SQLITE and args is None:
            args = ()
        # log.d('[db] {}\n'.format(sql, args))
        # print('[db]', sql, args)
        # _start = datetime.datetime.utcnow().timestamp()
        ret = self._conn_pool.exec(sql, args)
        # _end = datetime.datetime.utcnow().timestamp()
        # log.d('[db]   cost {} seconds.\n'.format(_end - _start))
        return ret

    def transaction(self, sql_list):
        # log.d('[db] transaction\n')
        # for sql in sql_list:
        #     log.d('[db]  * {}\n'.format(sql))

        # _start = datetime.datetime.utcnow().timestamp()
        ret = self._conn_pool.transaction(sql_list)
        # _end = datetime.datetime.utcnow().timestamp()
        # log.d('[db] transaction\n')
        # log.d('[db]   cost {} seconds.\n'.format(_end - _start))
        return ret

    def last_insert_id(self):
        return self._conn_pool.last_insert_id()

    def create_and_init(self, step_begin, step_end, sysadmin, email, password):
        log.v('start database create and initialization process.\n')

        if self.db_type == self.DB_TYPE_SQLITE:
            db_path = os.path.dirname(self.sqlite_file)
            if not os.path.exists(db_path):
                tp_make_dir(db_path)
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

        if DatabaseInit(self, step_begin, step_end).do_create_and_init(sysadmin, email, password):
            log.v('database created.\n')
            self.need_create = False
            self.load_system_config()
            return True
        else:
            log.e('database create and initialize failed.\n')
            return False

    # def upgrade_database(self, step_begin, step_end):
    #     log.v('start database upgrade process.\n')
    #     if DatabaseUpgrade(self, step_begin, step_end).do_upgrade():
    #         log.v('database upgraded.\n')
    #         self.need_upgrade = False
    #         return True
    #     else:
    #         log.e('database upgrade failed.\n')
    #         return False

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
        return export_database(self)


class TPDatabasePool:
    def __init__(self):
        self._locker = threading.RLock()
        self._connections = dict()

    def connect(self):
        return False if self._get_connect() is None else True

    def query(self, sql, args):
        _conn = self._get_connect()
        if _conn is None:
            return None
        return self._do_query(_conn, sql, args)

    def exec(self, sql, args):
        _conn = self._get_connect()
        if _conn is None:
            return False
        return self._do_exec(_conn, sql, args)

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

    def _do_query(self, conn, sql, args):
        return None

    def _do_exec(self, conn, sql, args):
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
        # if not os.path.exists(self._db_file):
        #     log.e('[sqlite] can not connect, database file not exists.\n')
        #     return None

        try:
            return sqlite3.connect(self._db_file)
        except:
            log.e('[sqlite] can not connect, does the database file correct?\n')
            return None

    def _do_query(self, conn, sql, args):
        cursor = conn.cursor()
        try:
            cursor.execute(sql, args)
            db_ret = cursor.fetchall()
            return db_ret
        except Exception as e:
            log.e('[sqlite] _do_query() failed: {}\n'.format(e.__str__()))
            log.e('[sqlite] SQL={}'.format(sql))
        finally:
            cursor.close()

    def _do_exec(self, conn, sql, args):
        try:
            with conn:
                conn.execute(sql, args)
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
            conn = pymysql.connect(host=self._host,
                                   user=self._user,
                                   passwd=self._password,
                                   db=self._db_name,
                                   port=self._port,
                                   autocommit=False,
                                   connect_timeout=3.0,
                                   charset='utf8')

            self._do_exec(conn, 'SET SESSION sql_mode=(SELECT CONCAT(@@sql_mode,",NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"));', args=())

            # x = self._do_query(conn, 'SELECT @@sql_mode;', args=())
            # print(x)
            #
            err = self._do_exec(conn, 'SET SESSION sql_mode=(SELECT REPLACE(@@sql_mode,"ONLY_FULL_GROUP_BY",""));', args=())
            if err is None:
                log.e('[mysql] can not disable ONLY_FULL_GROUP_BY flag.\n')

            return conn
        except pymysql.err.OperationalError as e:
            errno, _ = e.args
            if 2003 == errno:
                log.e('[mysql] connect [{}:{}] failed: {}\n'.format(self._host, self._port, e.__str__()))
            return None
        except Exception as e:
            log.e('[mysql] connect [{}:{}] failed: {}\n'.format(self._host, self._port, e.__str__()))
            return None

    def _reconnect(self):
        log.w('[mysql] lost connection, reconnect.\n')
        with self._locker:
            thread_id = threading.get_ident()
            if thread_id not in self._connections:
                log.e('[mysql] database pool internal error.\n')
                return None
            _conn = self._do_connect()
            if _conn is not None:
                self._connections[thread_id] = _conn
                return _conn
            else:
                del self._connections[thread_id]
                return None

    def _do_query(self, conn, sql, args):
        for retry in range(2):
            cursor = conn.cursor()
            try:
                cursor.execute(sql, args)
                db_ret = cursor.fetchall()
                conn.commit()
                return db_ret
            except pymysql.err.OperationalError as e:
                errno, _ = e.args
                if retry == 1 or errno not in [2006, 2013]:
                    log.v('[mysql] SQL={}\n'.format(sql))
                    log.e('[mysql] _do_query() failed: {}\n'.format(e.__str__()))
                    return None
                conn = self._reconnect()
                if conn is None:
                    return None
            except pymysql.err.InterfaceError as e:
                if retry == 1:
                    log.v('[mysql] SQL={}\n'.format(sql))
                    log.e('[mysql] _do_query() failed: {}\n'.format(e.__str__()))
                    return None
                conn = self._reconnect()
                if conn is None:
                    return None

            except Exception as e:
                log.v('[mysql] SQL={}\n'.format(sql))
                log.e('[mysql] _do_query() failed: {}\n'.format(e.__str__()))
                return None
            finally:
                cursor.close()

    def _do_exec(self, conn, sql, args):
        for retry in range(2):
            cursor = conn.cursor()
            try:
                cursor.execute(sql, args)
                conn.commit()
                return True
            except pymysql.err.OperationalError as e:
                errno, _ = e.args
                if retry == 1 or errno not in [2006, 2013]:
                    log.v('[mysql] SQL={}\n'.format(sql))
                    log.e('[mysql] _do_exec() failed: {}\n'.format(e.__str__()))
                    return None
                conn = self._reconnect()
                if conn is None:
                    return None

            except pymysql.err.InterfaceError as e:
                if retry == 1:
                    log.v('[mysql] SQL={}\n'.format(sql))
                    log.e('[mysql] _do_exec() failed: {}\n'.format(e.__str__()))
                    return None
                conn = self._reconnect()
                if conn is None:
                    return None

            except Exception as e:
                log.e('[mysql] _do_exec() failed: {}\n'.format(e.__str__()))
                log.e('[mysql] SQL={}'.format(sql))
                return None
            finally:
                cursor.close()

    def _do_transaction(self, conn, sql_list):
        for retry in range(2):
            cursor = conn.cursor()
            try:
                conn.begin()
                for sql in sql_list:
                    cursor.execute(sql)
                conn.commit()
                return True
            except pymysql.err.OperationalError as e:
                errno, _ = e.args
                if retry == 1 or errno not in [2006, 2013]:
                    log.e('[mysql] _do_transaction() failed: {}\n'.format(e.__str__()))
                    return False
                conn = self._reconnect()
                if conn is None:
                    return None

            except pymysql.err.InterfaceError as e:
                if retry == 1:
                    log.e('[mysql] _do_transaction() failed: {}\n'.format(e.__str__()))
                    return None
                conn = self._reconnect()
                if conn is None:
                    return None

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


class SQL:
    def __init__(self, db):
        self._db = db
        self._table_used = []
        self._alt_name = []
        self._select_fields = []
        self._output_fields = []

        self._from = {}  # {n:name, a: alt-name, f: fields, o: output-mapping}
        self._left_join = []  # 每一项的内容等同于 _from
        self._where = ''
        self._order_by = []
        self._group_by = ''
        self._limit = None

        self._ret_page_index = 0
        self._ret_total_recorder = 0
        self._ret_recorder = []

    def reset(self):
        self._table_used = []
        self._alt_name = []
        self._select_fields = []
        self._output_fields = []

        self._from = {}
        self._left_join = []
        self._where = ''
        self._order_by = []
        self._group_by = ''
        self._limit = None

        self._ret_page_index = 0
        self._ret_total_recorder = 0
        self._ret_recorder = []

        return self

    @property
    def total_count(self):
        return self._ret_total_recorder

    @property
    def recorder(self):
        return self._ret_recorder

    @property
    def page_index(self):
        return self._ret_page_index

    def count(self, name):
        _sql = list()
        _sql.append('SELECT COUNT(*)')
        _sql.append('FROM `{}{}`'.format(self._db.table_prefix, name))
        if len(self._where) > 0:
            _sql.append('WHERE {}'.format(self._where))
        _sql.append(';')
        sql = ' '.join(_sql)
        db_ret = self._db.query(sql)
        if db_ret is None or 0 == len(db_ret):
            return TPE_OK, 0
        return TPE_OK, db_ret[0][0]

    def select_from(self, name, fields, alt_name=None, out_map=None):
        if len(fields) == 0:
            raise RuntimeError('empty fields.')
        if len(self._from) != 0:
            raise RuntimeError('select_from() should call only once.')
        self._from = {'n': name, 'a': name, 'f': fields}
        if alt_name is not None:
            self._from['a'] = alt_name

        self._table_used.append(name)
        self._alt_name.append(self._from['a'])

        _o = {}
        for f in fields:
            _o[f] = f
        if out_map is not None:
            for k in out_map:
                if k not in _o:
                    raise RuntimeError('invalid out_map. {} not in fields.'.format(k))
                _o[k] = out_map[k]

        _o = list()
        for f in fields:
            if out_map is not None and f in out_map:
                _field = out_map[f]
            else:
                _field = f

            if _field not in _o:
                _o.append(_field)
            else:
                raise RuntimeError('duplicated output field: {}'.format(_field))

        self._select_fields = ['{}.{}'.format(self._from['a'], k) for k in fields]
        self._output_fields = _o
        return self

    def left_join(self, name, fields, join_on, alt_name=None, out_map=None):
        if len(fields) == 0:
            raise RuntimeError('empty fields.')
        if name in self._table_used:
            raise RuntimeError('duplicated table for left-join: {}'.format(name))

        _j = {'n': name, 'a': name, 'on': join_on, 'f': fields}
        if alt_name is not None:
            if alt_name in self._alt_name:
                raise RuntimeError('duplicated alt-table-name for left-join: {}'.format(alt_name))
            _j['a'] = alt_name

        _o = list()
        for f in fields:
            if out_map is not None and f in out_map:
                _field = out_map[f]
            else:
                _field = f

            if _field not in _o:
                _o.append(_field)
            else:
                raise RuntimeError('duplicated output field: {}'.format(_field))

        for k in _o:
            if k in self._output_fields:
                print('---', k, '---', self._output_fields)
                raise RuntimeError('duplicated output field: {}'.format(k))

        self._select_fields.extend(['{}.{}'.format(_j['a'], k) for k in fields])
        self._output_fields.extend(_o)

        self._left_join.append(_j)
        return self

    def delete_from(self, name):
        self._from = name
        return self

    def where(self, _where):
        self._where = _where
        return self

    def order_by(self, name, is_asc=True):
        _sort = 'ASC' if is_asc else 'DESC'
        self._order_by.append('{} {}'.format(name, _sort))
        return self

    def group_by(self, name):
        self._group_by = name
        return self

    def limit(self, page_index, per_page):
        self._limit = {'page_index': page_index, 'per_page': per_page}
        return self

    def _make_sql_query_string(self):
        sql = list()
        sql.append('SELECT {}'.format(','.join(self._select_fields)))
        sql.append('FROM {}{} AS {}'.format(self._db.table_prefix, self._from['n'], self._from['a']))

        for _l in self._left_join:
            sql.append('LEFT JOIN {}{} AS {} ON {}'.format(self._db.table_prefix, _l['n'], _l['a'], _l['on']))

        if len(self._where) > 0:
            sql.append('WHERE {}'.format(self._where))

        if len(self._group_by) > 0:
            sql.append('GROUP BY {}'.format(self._group_by))

        if len(self._order_by) > 0:
            sql.append('ORDER BY {}'.format(','.join(self._order_by)))

        if self._limit is not None:
            if self._ret_total_recorder <= self._limit['page_index'] * self._limit['per_page']:
                self._ret_page_index = int(self._ret_total_recorder / self._limit['per_page'])
                if self._ret_page_index < 0:
                    self._ret_page_index = 0
            else:
                self._ret_page_index = self._limit['page_index']
            sql.append('LIMIT {},{}'.format(self._ret_page_index * self._limit['per_page'], self._limit['per_page']))

        sql.append(';')
        return ' '.join(sql)

    def _make_sql_counter_string(self):
        sql = list()
        sql.append('SELECT COUNT(*)')
        sql.append('FROM {}{} AS {}'.format(self._db.table_prefix, self._from['n'], self._from['a']))

        for _l in self._left_join:
            sql.append('LEFT JOIN {}{} AS {} ON {}'.format(self._db.table_prefix, _l['n'], _l['a'], _l['on']))

        if len(self._where) > 0:
            sql.append('WHERE {}'.format(self._where))

        if len(self._group_by) > 0:
            sql.append('GROUP BY {}'.format(self._group_by))

        sql.append(';')
        return ' '.join(sql)

    def _make_sql_delete_string(self):
        sql = list()
        sql.append('DELETE FROM {}{}'.format(self._db.table_prefix, self._from))
        if len(self._where) > 0:
            sql.append('WHERE {}'.format(self._where))
        else:
            raise RuntimeError('delete_from() need where expression.')

        sql.append(';')
        return ' '.join(sql)

    def query(self):
        # 如果要分页，那么需要计算记录总数
        if self._limit is not None:
            sql = self._make_sql_counter_string()
            # log.d(sql, '\n')
            db_ret = self._db.query(sql)
            if db_ret is None or 0 == len(db_ret):
                self._ret_page_index = 0
                return TPE_OK
            self._ret_total_recorder = db_ret[0][0]
            if self._ret_total_recorder == 0:
                self._ret_page_index = 0
                return TPE_OK

        sql = self._make_sql_query_string()
        # log.d(sql, '\n')
        db_ret = self._db.query(sql)

        for db_item in db_ret:
            item = AttrDict()
            for i in range(len(self._output_fields)):
                item[self._output_fields[i]] = db_item[i]

            self._ret_recorder.append(item)

        return TPE_OK

    def exec(self):
        sql = self._make_sql_delete_string()
        # log.d(sql, '\n')
        if not self._db.exec(sql):
            return TPE_DATABASE
        else:
            return TPE_OK


def get_db():
    """
    :rtype : TPDatabase
    """
    if '__teleport_db__' not in builtins.__dict__:
        builtins.__dict__['__teleport_db__'] = TPDatabase()
    return builtins.__dict__['__teleport_db__']
