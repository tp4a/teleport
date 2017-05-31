# -*- coding: utf-8 -*-

import time
from eom_app.app.util import sec_generate_password
from eom_common.eomcore.logger import log


def _db_exec(db, step_begin, step_end, msg, sql):
    _step = step_begin(msg)

    ret = db.exec(sql)
    if not ret:
        step_end(_step, -1)
        raise RuntimeError('[FAILED] {}'.format(sql))
    else:
        step_end(_step, 0)


def _export_table(db, table_name, fields):
    ret = ['', '-- table: {}'.format(table_name), '-- fields: {}'.format(', '.join(fields)), 'TRUNCATE TABLE `{}`;'.format(table_name)]

    fields_str = '`,`'.join(fields)
    sql = 'SELECT `{}` FROM `{}{}`'.format(fields_str, db.table_prefix, table_name)
    d = db.query(sql)
    if not d or len(d) == 0:
        ret.append('-- table is empty.')
    else:
        fields_count = len(fields)
        for i in range(len(d)):
            x = []
            for j in range(fields_count):
                x.append(d[i][j].__str__())
            val = "','".join(x).replace('\n', '\\n')
            sql = "INSERT INTO `{}` VALUES ('{}');".format(table_name, val)
            ret.append(sql)

    return '\r\n'.join(ret)


def export_database(db):
    ret = []
    now = time.localtime(time.time())
    ret.append('-- {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} '.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec))
    if db.db_type == db.DB_TYPE_SQLITE:
        ret.append('-- export from SQLite Database')
    elif db.db_type == db.DB_TYPE_MYSQL:
        ret.append('-- export from MySQL Database')
    else:
        return 'Unknown Database Type'

    _fields = ['account_id', 'account_type', 'account_name', 'account_pwd', 'account_status', 'account_lock', 'account_desc']
    ret.append(_export_table(db, 'account', _fields))
    _fields = ['auth_id', 'account_name', 'host_id', 'host_auth_id']
    ret.append(_export_table(db, 'auth', _fields))
    _fields = ['cert_id', 'cert_name', 'cert_pub', 'cert_pri', 'cert_desc']
    ret.append(_export_table(db, 'key', _fields))
    _fields = ['name', 'value']
    ret.append(_export_table(db, 'config', _fields))
    _fields = ['group_id', 'group_name']
    ret.append(_export_table(db, 'group', _fields))
    _fields = ['host_id', 'group_id', 'host_sys_type', 'host_ip', 'host_port', 'protocol', 'host_lock', 'host_desc']
    ret.append(_export_table(db, 'host_info', _fields))
    _fields = ['id', 'host_id', 'auth_mode', 'user_name', 'user_pswd', 'user_param', 'cert_id', 'encrypt', 'log_time']
    ret.append(_export_table(db, 'auth_info', _fields))
    _fields = ['id', 'session_id', 'account_name', 'host_ip', 'host_port', 'sys_type', 'auth_type', 'protocol', 'user_name', 'ret_code', 'begin_time', 'end_time', 'log_time']
    ret.append(_export_table(db, 'log', _fields))

    return '\r\n'.join(ret)


def create_and_init(db, step_begin, step_end):
    try:
        _db_exec(db, step_begin, step_end, '创建表 account', """CREATE TABLE `{}account` (
`account_id` integer PRIMARY KEY {},
`account_type` int(11) DEFAULT 0,
`account_name` varchar(32) DEFAULT NULL,
`account_pwd` varchar(128) DEFAULT NULL,
`account_status` int(11) DEFAULT 0,
`account_lock` int(11) DEFAULT 0,
`account_desc` varchar(255)
);""".format(db.table_prefix, db.auto_increment))

        _db_exec(db, step_begin, step_end, '创建表 auth', """CREATE TABLE `{}auth`(
`auth_id`  INTEGER PRIMARY KEY {},
`account_name`  varchar(255),
`host_id`  INTEGER,
`host_auth_id`  int(11) NOT NULL
);""".format(db.table_prefix, db.auto_increment))

        # 注意，这个key表原名为cert，考虑到其中存放的是ssh密钥对，与证书无关，因此改名为key
        # 这也是升级到数据库版本5的标志！
        _db_exec(db, step_begin, step_end, '创建表 key', """CREATE TABLE `{}key` (
`cert_id`  integer PRIMARY KEY {},
`cert_name`  varchar(255),
`cert_pub`  varchar(2048) DEFAULT '',
`cert_pri`  varchar(4096) DEFAULT '',
`cert_desc`  varchar(255)
);
""".format(db.table_prefix, db.auto_increment))

        _db_exec(db, step_begin, step_end, '创建表 config', """CREATE TABLE `{}config` (
`name`  varchar(128) NOT NULL,
`value`  varchar(255),
PRIMARY KEY (`name` ASC)
);""".format(db.table_prefix))

        _db_exec(db, step_begin, step_end, '创建表 group', """CREATE TABLE `{}group` (
`group_id` integer PRIMARY KEY {},
`group_name` varchar(255) DEFAULT''
);""".format(db.table_prefix, db.auto_increment))

        _db_exec(db, step_begin, step_end, '创建表 host_info', """CREATE TABLE `{}host_info`(
`host_id`  integer PRIMARY KEY {},
`group_id`  int(11) DEFAULT 0,
`host_sys_type`  int(11) DEFAULT 1,
`host_ip`  varchar(32) DEFAULT '',
`host_port`  int(11) DEFAULT 0,
`protocol`  int(11) DEFAULT 0,
`host_lock`  int(11) DEFAULT 0,
`host_desc`  varchar(255) DEFAULT ''
);""".format(db.table_prefix, db.auto_increment))

        _db_exec(db, step_begin, step_end, '创建表 auth_info', """CREATE TABLE `{}auth_info`(
`id`  INTEGER PRIMARY KEY {},
`host_id`  INTEGER,
`auth_mode`  INTEGER,
`user_name`  varchar(255),
`user_pswd`  varchar(255),
`user_param` varchar(255),
`cert_id`  INTEGER,
`encrypt`  INTEGER,
`log_time`  varchar(60)
);""".format(db.table_prefix, db.auto_increment))

        _db_exec(db, step_begin, step_end, '创建表 key', """CREATE TABLE `{}log` (
`id`  INTEGER PRIMARY KEY {},
`session_id`  varchar(32),
`account_name`  varchar(64),
`host_ip`  varchar(32),
`host_port`  INTEGER,
`sys_type`  INTEGER DEFAULT 0,
`auth_type`  INTEGER,
`protocol` INTEGER,
`user_name`  varchar(64),
`ret_code`  INTEGER,
`begin_time`  INTEGER,
`end_time`  INTEGER,
`log_time`  varchar(64)
);""".format(db.table_prefix, db.auto_increment))

        _admin_sec_password = sec_generate_password('admin')

        _db_exec(db, step_begin, step_end,
                 '建立管理员账号',
                 'INSERT INTO `{}account` VALUES (1, 100, "admin", "{}", 0, 0, "超级管理员");'.format(db.table_prefix, _admin_sec_password)
                 )

        _db_exec(db, step_begin, step_end,
                 '设定数据库版本',
                 'INSERT INTO `{}config` VALUES ("db_ver", "{}");'.format(db.table_prefix, db.DB_VERSION)
                 )

        return True
    except:
        log.e('ERROR\n')
        return False
