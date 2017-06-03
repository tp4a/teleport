# -*- coding: utf-8 -*-

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


def create_and_init(db, step_begin, step_end):
    try:
        _db_exec(db, step_begin, step_end, '创建表 account', """CREATE TABLE `{}account` (
`account_id` integer PRIMARY KEY {},
`account_type` int(11) DEFAULT 0,
`account_name` varchar(32) DEFAULT NULL,
`account_pwd` varchar(128) DEFAULT NULL,
`account_status` int(11) DEFAULT 0,
`account_lock` int(11) DEFAULT 0,
`account_desc` varchar(255),
`oath_secret` varchar(64),
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
`group_name` varchar(255) DEFAULT ''
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
                 'INSERT INTO `{}account` VALUES (1, 100, "admin", "{}", 0, 0, "超级管理员", "");'.format(db.table_prefix, _admin_sec_password)
                 )

        _db_exec(db, step_begin, step_end,
                 '设定数据库版本',
                 'INSERT INTO `{}config` VALUES ("db_ver", "{}");'.format(db.table_prefix, db.DB_VERSION)
                 )

        return True
    except:
        log.e('ERROR\n')
        return False
