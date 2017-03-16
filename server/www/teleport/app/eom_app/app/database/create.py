# -*- coding: utf-8 -*-

from eom_common.eomcore.logger import log
from eom_app.app.util import sec_generate_password

# 升级数据表结构时必须升级此版本号，并编写响应的升级SQL
TELEPORT_DATABASE_VERSION = 10


def create_and_init(db, step_begin, step_end):
    _admin_sec_password = sec_generate_password('admin')

    _step = step_begin('创建表 account')

    ret = db.exec("""CREATE TABLE `{}account` (
  `account_id` integer PRIMARY KEY AUTOINCREMENT,
  `account_type` int(11) DEFAULT 0,
  `account_name` varchar(32) DEFAULT NULL,
  `account_pwd` varchar(32) DEFAULT NULL,
  `account_status` int(11) DEFAULT 0,
  `account_lock` int(11) DEFAULT 0,
  `account_desc` varchar(255)
);""".format(db.table_prefix))
    if not ret:
        log.e('create table `account` failed.')
        step_end(_step, -1)
        return
    else:
        log.i('create table `account` ok.')
        step_end(_step, 0)
