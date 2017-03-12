# -*- coding: utf-8 -*-

import json
import os
import shutil
import sys

from eom_env import *
from eom_common.eomcore.eom_sqlite import get_sqlite_pool
from eom_common.eomcore.logger import *

log.set_attribute(min_level=LOG_DEBUG, log_datetime=False, trace_error=log.TRACE_ERROR_FULL)

db_file = os.path.join(PATH_DATA, 'ts_db.db')


def main():
    if not os.path.exists(db_file):
        log.v('\n')
        log.v('Teleport Server Database Creation\n')

        # 如果数据库文件尚未存在，则直接创建之
        get_sqlite_pool().init(PATH_DATA)

        if not create_base_db():
            return 1

    else:
        log.v('\n')
        log.v('Teleport Server Upgrade\n')

        if not get_sqlite_pool().init(PATH_DATA):
            log.e('upgrade failed.\n')
            return 1

        if not upgrade_to_1_2_102_3():
            log.e('failed to upgrade database to version 1.2.102.3 ...\n')
            return 1
        if not upgrade_to_1_5_217_9():
            log.e('failed to upgrade database to version 1.5.217.9 ...\n')
            return 1

        if not upgrade_to_1_6_224_3():
            log.e('failed to upgrade database to version 1.6.224.3 ...\n')
            return 1

    return 0


def create_base_db():
    try:
        # f = open(db_file, 'w')
        # f.close()
        sql_file = os.path.join(PATH_DATA, 'main.sql')
        if not os.path.exists(sql_file):
            log.e("sql file not exists.\n")
            return False

        f = open(sql_file, 'r', encoding='utf-8')
        sql = f.read()
        f.close()
        sql_con = get_sqlite_pool().get_tssqlcon()
        sql_con.ExecManyProcNonQuery(sql)

    except Exception:
        return False

    return True


def upgrade_to_1_2_102_3():
    # 服务端升级到版本1.2.102.3时，管理员后台和普通用户后台合并了，数据库略有调整
    try:
        sql_con = get_sqlite_pool().get_tssqlcon()

        # 如果存在名为 ts_sys_user 的表，说明是旧版本，需要升级
        str_sql = 'SELECT COUNT(*) FROM sqlite_master where type="table" and name="ts_sys_user";'
        db_ret = sql_con.ExecProcQuery(str_sql)
        if (db_ret[0][0] == 0):
            return True

        log.v('upgrade database to version 1.2.102.3 ...\n')
        bak_file = '{}.before-1.2.102.3'.format(db_file)
        if not os.path.exists(bak_file):
            shutil.copy(db_file, bak_file)

        # 将原来的普通用户的account_type从 0 改为 1
        str_sql = 'UPDATE ts_account SET account_type=1 WHERE account_type=0;'
        sql_con.ExecProcNonQuery(str_sql)

        # 将原来的管理员合并到用户账号表中
        str_sql = 'SELECT * FROM ts_sys_user;'
        db_ret = sql_con.ExecProcQuery(str_sql)
        if db_ret is None:
            return True

        for i in range(len(db_ret)):
            user_name = db_ret[i][1]
            user_pwd = db_ret[i][2]
            str_sql = 'INSERT INTO ts_account (account_type, account_name, account_pwd, account_status, ' \
                      'account_lock, account_desc) VALUES (100,"{}","{}",0,0,"{}");'.format(user_name, user_pwd, '超级管理员')
            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not found super admin account.\n')
                return False

        # 移除旧的表（暂时改名而不是真的删除）
        str_sql = 'ALTER TABLE ts_sys_user RENAME TO _bak_ts_sys_user;'
        ret = sql_con.ExecProcNonQuery(str_sql)
        if not ret:
            log.e('can not rename table `ts_sys_user`.\n')
            return False

    except:
        return False

    return True


def upgrade_to_1_5_217_9():
    # 服务端升级到版本1.5.217.9时，为了支持一机多用户多协议，数据库结构有较大程度改动
    try:
        sql_con = get_sqlite_pool().get_tssqlcon()

        # 如果不存在名为 ts_host_info 的表，说明是旧版本，需要升级
        str_sql = 'SELECT COUNT(*) FROM sqlite_master where type="table" and name="ts_host_info";'
        db_ret = sql_con.ExecProcQuery(str_sql)
        if (db_ret[0][0] == 1):
            return True

        log.v('upgrade database to version 1.5.217.9 ...\n')
        bak_file = '{}.before-1.5.217.9'.format(db_file)
        if not os.path.exists(bak_file):
            shutil.copy(db_file, bak_file)

        # 将原来的 ts_auth 表中增加一个字段
        str_sql = 'ALTER TABLE ts_auth ADD host_auth_id INTEGER;'
        ret = sql_con.ExecProcNonQuery(str_sql)
        if not ret:
            log.e('can not modify table `ts_auth`.\n')
            return False

        # 为新增字段进行赋值
        str_sql = 'UPDATE ts_auth SET host_auth_id=host_id;'
        ret = sql_con.ExecProcNonQuery(str_sql)
        # print(ret)
        if not ret:
            log.e('can not update table `ts_auth`.\n')
            return False

        # 新建两个表，用于拆分原来的 ts_host 表
        str_sql = '''CREATE TABLE "ts_host_info" (
"host_id"  integer PRIMARY KEY AUTOINCREMENT,
"group_id"  int(11) DEFAULT 0,
"host_sys_type"  int(11) DEFAULT 1,
"host_ip"  varchar(32) DEFAULT '',
"pro_port"  varchar(256) NULL,
"host_lock"  int(11) DEFAULT 0,
"host_desc" varchar(128) DEFAULT ''
);'''

        ret = sql_con.ExecProcNonQuery(str_sql)
        if not ret:
            log.e('can not create table `ts_host_info`.\n')
            return False

        str_sql = '''CREATE TABLE "ts_auth_info" (
"id"  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
"host_id"  INTEGER,
"pro_type"  INTEGER,
"auth_mode"  INTEGER,
"user_name"  varchar(256),
"user_pswd"  varchar(256),
"cert_id"  INTEGER,
"encrypt"  INTEGER,
"log_time"  varchar(60)
);'''

        ret = sql_con.ExecProcNonQuery(str_sql)
        if not ret:
            log.e('can not create table `ts_auth_info`.\n')
            return False

        # 将原来的 ts_host 表改名
        str_sql = 'ALTER TABLE ts_host RENAME TO _bak_ts_host;'
        ret = sql_con.ExecProcNonQuery(str_sql)
        if not ret:
            log.e('can not rename table `ts_host`.\n')
            return False

        # 从原来 ts_host 表中查询出所有数据
        str_sql = 'SELECT * FROM _bak_ts_host;'
        db_ret = sql_con.ExecProcQuery(str_sql)
        if db_ret is not None:
            for i in range(len(db_ret)):
                host_id = db_ret[i][0]
                group_id = db_ret[i][1]
                host_sys_type = db_ret[i][2]
                host_ip = db_ret[i][3]
                host_pro_port = db_ret[i][4]
                host_user_name = db_ret[i][5]
                host_user_pwd = db_ret[i][6]
                host_pro_type = db_ret[i][7]
                cert_id = db_ret[i][8]
                host_lock = db_ret[i][9]
                host_encrypt = db_ret[i][10]
                host_auth_mode = db_ret[i][11]
                host_desc = db_ret[i][12]

                _pro_port = {}
                _pro_port['ssh'] = {}
                _pro_port['ssh']['enable'] = 0
                _pro_port['ssh']['port'] = 22
                _pro_port['rdp'] = {}
                _pro_port['rdp']['enable'] = 0
                _pro_port['rdp']['port'] = 3389

                if (host_pro_type == 1):
                    _pro_port['rdp']['enable'] = 1
                    _pro_port['rdp']['port'] = host_pro_port
                elif (host_pro_type == 2):
                    _pro_port['ssh']['enable'] = 1
                    _pro_port['ssh']['port'] = host_pro_port
                pro_port = json.dumps(_pro_port)

                str_sql = 'INSERT INTO ts_host_info (host_id, group_id, host_sys_type, host_ip, pro_port, host_lock, host_desc) ' \
                          'VALUES ({}, {}, {}, \'{}\', \'{}\', {}, \'{}\');'.format(host_id, group_id, host_sys_type, host_ip, pro_port, host_lock, host_desc)
                # print(str_sql)
                ret = sql_con.ExecProcNonQuery(str_sql)
                if not ret:
                    log.e('can not insert item into `ts_host_info`.\n')
                    return False

                str_sql = 'INSERT INTO ts_auth_info (host_id, pro_type, auth_mode, user_name, user_pswd, cert_id, encrypt, log_time) ' \
                          'VALUES ({}, {}, {}, \'{}\', \'{}\', {}, {}, \'{}\');'.format(host_id, host_pro_type, host_auth_mode, host_user_name, host_user_pwd, cert_id, host_encrypt, '1')
                # print(str_sql)
                ret = sql_con.ExecProcNonQuery(str_sql)
                if not ret:
                    log.e('can not insert item into `ts_auth_info`.\n')
                    return False

        str_sql = 'ALTER TABLE ts_log add protocol INTEGER;'
        # print(str_sql)
        ret = sql_con.ExecProcNonQuery(str_sql)
        if not ret:
            log.e('can not upgrade database table `ts_log`.\n')
            return False

        str_sql = 'UPDATE ts_log SET protocol=1 WHERE sys_type=1;'
        ret = sql_con.ExecProcNonQuery(str_sql)
        if not ret:
            log.e('can not fix database table `ts_log`.\n')
            return False

        str_sql = 'UPDATE ts_log SET protocol=2 WHERE sys_type=2;'
        ret = sql_con.ExecProcNonQuery(str_sql)
        if not ret:
            log.e('can not fix database table `ts_log`.\n')
            return False

        str_sql = 'UPDATE ts_log SET ret_code=9999 WHERE ret_code=0;'
        ret = sql_con.ExecProcNonQuery(str_sql)
        if not ret:
            log.e('can not fix database table `ts_log`.\n')
            return False


    except:
        return False

    return True


# def upgrade_to_1_6_224_3():
#     # 服务端升级到版本1.6.224.3时，加入telnet支持，数据库有调整
#     try:
#         sql_con = get_sqlite_pool().get_tssqlcon()
#
#         # # 如果ts_config表中没有ts_server_telnet_port项，则增加默认值52389
#         # str_sql = 'SELECT * FROM ts_config WHERE name="ts_server_telnet_port";'
#         # db_ret = sql_con.ExecProcQuery(str_sql)
#         # if len(db_ret) == 0:
#         #     log.v('upgrade database to version 1.6.224.3 ...\n')
#         #
#         #     str_sql = 'INSERT INTO ts_config (name, value) VALUES (\'ts_server_telnet_port\', \'52389\');'
#         #     db_ret = sql_con.ExecProcNonQuery(str_sql)
#         #     if not db_ret:
#         #         log.e('can not add telnet default port into `ts_config`.\n')
#         #         return False
#         #
#
#         # 如果ts_host_info表中还有pro_port字段，说明是旧版本，需要处理
#         str_sql = 'SELECT pro_port FROM ts_host_info LIMIT 0;'
#         db_ret = sql_con.ExecProcQuery(str_sql)
#         if db_ret is not None:
#             # 发现旧版本
#
#             log.v('upgrade database to version 1.6.224.3 ...\n')
#             bak_file = '{}.before-1.6.224.3'.format(db_file)
#             if not os.path.exists(bak_file):
#                 shutil.copy(db_file, bak_file)
#
#             # 删除所有的表，重建新的
#             # os.remove(db_file)
#             str_sql = '''
# ALTER TABLE ts_account RENAME TO __bak_ts_account;
# ALTER TABLE ts_auth RENAME TO __bak_ts_auth;
# ALTER TABLE ts_cert RENAME TO __bak_ts_cert;
# ALTER TABLE ts_config RENAME TO __bak_ts_config;
# ALTER TABLE ts_group RENAME TO __bak_ts_group;
# ALTER TABLE ts_host_info RENAME TO __bak_ts_host_info;
# ALTER TABLE ts_auth_info RENAME TO __bak_ts_auth_info;
# ALTER TABLE ts_log RENAME TO __bak_ts_log;
# '''
#             sql_con.ExecManyProcNonQuery(str_sql)
#
#             return create_base_db()
#
#
#     except:
#         log.e('failed.\n')
#         return False
#
#     return True

def upgrade_to_1_6_224_3():
    # 服务端升级到版本1.6.224.3时，加入telnet支持，数据库有调整
    try:
        sql_con = get_sqlite_pool().get_tssqlcon()

        # 如果ts_config表中没有ts_server_telnet_port项，则增加默认值52389
        str_sql = 'SELECT * FROM ts_config WHERE name="ts_server_telnet_port";'
        db_ret = sql_con.ExecProcQuery(str_sql)
        if len(db_ret) == 0:
            # log.v('upgrade database to version 1.6.224.3 ...\n')

            str_sql = 'INSERT INTO ts_config (name, value) VALUES (\'ts_server_telnet_port\', \'52389\');'
            db_ret = sql_con.ExecProcNonQuery(str_sql)
            if not db_ret:
                log.e('can not add telnet default port into `ts_config`.\n')
                return False

        # 如果ts_host_info表中还有pro_port字段，说明是旧版本，需要处理
        str_sql = 'SELECT pro_port FROM ts_host_info LIMIT 0;'
        db_ret = sql_con.ExecProcQuery(str_sql)
        if db_ret is None:
            return True

        # 发现旧版本
        log.v('upgrade database to version 1.6.224.3 ...\n')
        bak_file = '{}.before-1.6.224.3'.format(db_file)
        if not os.path.exists(bak_file):
            shutil.copy(db_file, bak_file)

        str_sql = 'SELECT id, host_id, pro_type, auth_mode, user_name, user_pswd, cert_id, encrypt, log_time FROM ts_auth_info;'
        auth_info_ret = sql_con.ExecProcQuery(str_sql)
        # if auth_info_ret is not None:
        #     for i in range(len(auth_info_ret)):
        #         #host_id = db_ret[i][0]
        #         print(auth_info_ret[i])

        str_sql = 'SELECT auth_id, account_name, host_id, host_auth_id FROM ts_auth;'
        auth_ret = sql_con.ExecProcQuery(str_sql)
        # if auth_ret is not None:
        #     for i in range(len(auth_ret)):
        #         #host_id = db_ret[i][0]
        #         print(auth_ret[i])

        max_host_id = 0
        new_host_info = []
        new_auth_info = []
        new_auth = []

        # 从原来的表中查询数据
        str_sql = 'SELECT host_id, group_id, host_sys_type, host_ip, pro_port, host_lock, host_desc FROM ts_host_info;'
        host_info_ret = sql_con.ExecProcQuery(str_sql)
        if host_info_ret is not None:
            # 先找出最大的host_id，这样如果要拆分一个host，就知道新的host_id应该是多少了
            for i in range(len(host_info_ret)):
                # print(host_info_ret[i])
                #j = json.loads(host_info_ret[i][4])
                if host_info_ret[i][0] > max_host_id:
                    max_host_id = host_info_ret[i][0]
            max_host_id += 1

            # 然后构建新的host列表
            for i in range(len(host_info_ret)):
                host_info = {}
                host_info_alt = None

                protocol = json.loads(host_info_ret[i][4])
                host_info['host_id'] = host_info_ret[i][0]
                host_info['group_id'] = host_info_ret[i][1]
                host_info['host_sys_type'] = host_info_ret[i][2]
                host_info['host_ip'] = host_info_ret[i][3]
                host_info['host_lock'] = host_info_ret[i][5]
                host_info['host_desc'] = host_info_ret[i][6]
                host_info['_old_host_id'] = host_info_ret[i][0]
                host_info['host_port'] = 0
                host_info['protocol'] = 0

                have_rdp = False
                have_ssh = False
                if auth_info_ret is not None:
                    for j in range(len(auth_info_ret)):
                        if auth_info_ret[j][1] == host_info['host_id']:
                            if auth_info_ret[j][2] == 1:        # 用到了此主机的RDP
                                have_rdp = True
                            elif auth_info_ret[j][2] == 2:      # 用到了此主机的SSH
                                have_ssh = True

                if have_rdp and have_ssh:
                    # 需要拆分
                    host_info['protocol'] = 1
                    host_info['host_port'] = protocol['rdp']['port']

                    host_info_alt = {}
                    host_info_alt['host_id'] = max_host_id
                    max_host_id += 1
                    host_info_alt['group_id'] = host_info_ret[i][1]
                    host_info_alt['host_sys_type'] = host_info_ret[i][2]
                    host_info_alt['host_ip'] = host_info_ret[i][3]
                    host_info_alt['host_lock'] = host_info_ret[i][5]
                    host_info_alt['host_desc'] = host_info_ret[i][6]
                    host_info_alt['_old_host_id'] = host_info_ret[i][0]
                    host_info_alt['host_port'] = protocol['ssh']['port']
                    host_info_alt['protocol'] = 2
                elif have_rdp:
                    host_info['protocol'] = 1
                    host_info['host_port'] = protocol['rdp']['port']
                elif have_ssh:
                    host_info['host_port'] = protocol['ssh']['port']
                    host_info['protocol'] = 2

                new_host_info.append(host_info)
                if host_info_alt is not None:
                    new_host_info.append(host_info_alt)

            # print('=====================================')
            # for i in range(len(new_host_info)):
            #     print(new_host_info[i])

            # 现在有了新的ts_host_info表，重构ts_auth_info表
            # 'SELECT id, host_id, pro_type, auth_mode, user_name, user_pswd, cert_id, encrypt, log_time FROM ts_auth_info;'
            if auth_info_ret is not None:
                for i in range(len(auth_info_ret)):
                    auth_info = {}
                    auth_info['id'] = auth_info_ret[i][0]
                    auth_info['auth_mode'] = auth_info_ret[i][3]
                    auth_info['user_name'] = auth_info_ret[i][4]
                    auth_info['user_pswd'] = auth_info_ret[i][5]
                    auth_info['cert_id'] = auth_info_ret[i][6]
                    auth_info['encrypt'] = auth_info_ret[i][7]
                    auth_info['log_time'] = auth_info_ret[i][8]
                    auth_info['user_param'] = 'ogin:\nassword:'
                    found = False
                    for j in range(len(new_host_info)):
                        if auth_info_ret[i][1] == new_host_info[j]['_old_host_id'] and auth_info_ret[i][2] == new_host_info[j]['protocol']:
                            found = True
                            auth_info['host_id'] = new_host_info[j]['host_id']
                            auth_info['_old_host_id'] = new_host_info[j]['_old_host_id']
                            break
                    if found:
                        new_auth_info.append(auth_info)

            # for i in range(len(new_auth_info)):
            #     print(new_auth_info[i])

            # 最后重构ts_auth表
            if auth_ret is not None:
                for i in range(len(auth_ret)):
                    auth = {}
                    auth['auth_id'] = auth_ret[i][0]
                    auth['account_name'] = auth_ret[i][1]
                    found = False
                    for j in range(len(new_auth_info)):
                        if auth_ret[i][2] == new_auth_info[j]['_old_host_id'] and auth_ret[i][3] == new_auth_info[j]['id']:
                            found = True
                            auth['host_id'] = new_auth_info[j]['host_id']
                            auth['host_auth_id'] = new_auth_info[j]['id']
                            break
                    if found:
                        new_auth.append(auth)

            # for i in range(len(new_auth)):
            #     print(new_auth[i])

            # 将整理好的数据写入新的临时表
            # 先创建三个临时表
            str_sql = '''CREATE TABLE "ts_auth_tmp" (
            "auth_id"  INTEGER PRIMARY KEY AUTOINCREMENT,
            "account_name"  varchar(256),
            "host_id"  INTEGER,
            "host_auth_id"  int(11) NOT NULL
            );'''

            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not create table `ts_auth_tmp`.\n')
                return False

            str_sql = '''CREATE TABLE "ts_host_info_tmp" (
            "host_id"  integer PRIMARY KEY AUTOINCREMENT,
            "group_id"  int(11) DEFAULT 0,
            "host_sys_type"  int(11) DEFAULT 1,
            "host_ip"  varchar(32) DEFAULT '',
            "host_port"  int(11) DEFAULT 0,
            "protocol"  int(11) DEFAULT 0,
            "host_lock"  int(11) DEFAULT 0,
            "host_desc"   DEFAULT ''
            );'''

            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not create table `ts_host_info_tmp`.\n')
                return False

            str_sql = '''CREATE TABLE "ts_auth_info_tmp" (
            "id"  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "host_id"  INTEGER,
            "auth_mode"  INTEGER,
            "user_name"  varchar(256),
            "user_pswd"  varchar(256),
            "user_param" varchar(256),
            "cert_id"  INTEGER,
            "encrypt"  INTEGER,
            "log_time"  varchar(60)
            );'''

            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not create table `ts_auth_info_tmp`.\n')
                return False

            for i in range(len(new_host_info)):
                str_sql = 'INSERT INTO ts_host_info_tmp (host_id, group_id, host_sys_type, host_ip, host_port, protocol, host_lock, host_desc) ' \
                          'VALUES ({}, {}, {}, \'{}\', {}, {}, {}, \'{}\');'.format(
                    new_host_info[i]['host_id'], new_host_info[i]['group_id'], new_host_info[i]['host_sys_type'],
                    new_host_info[i]['host_ip'], new_host_info[i]['host_port'], new_host_info[i]['protocol'],
                    new_host_info[i]['host_lock'], new_host_info[i]['host_desc']
                )
                ret = sql_con.ExecProcNonQuery(str_sql)
                if not ret:
                    log.e('can not insert item into `ts_host_info`.\n')
                    return False

            for i in range(len(new_auth_info)):
                str_sql = 'INSERT INTO ts_auth_info_tmp (id, host_id, auth_mode, user_name, user_pswd, user_param, cert_id, encrypt, log_time) ' \
                          'VALUES ({}, {}, {}, \'{}\', \'{}\', \'{}\', {}, {}, \'{}\');'.format(
                    new_auth_info[i]['id'], new_auth_info[i]['host_id'], new_auth_info[i]['auth_mode'],
                    new_auth_info[i]['user_name'], new_auth_info[i]['user_pswd'], new_auth_info[i]['user_param'],
                    new_auth_info[i]['cert_id'], new_auth_info[i]['encrypt'], '1'
                )
                # print(str_sql)
                ret = sql_con.ExecProcNonQuery(str_sql)
                if not ret:
                    log.e('can not insert item into `ts_auth_info`.\n')
                    return False

            for i in range(len(new_auth)):
                str_sql = 'INSERT INTO ts_auth_tmp (auth_id, account_name, host_id, host_auth_id) ' \
                          'VALUES ({}, \'{}\', {}, {});'.format(
                    new_auth[i]['auth_id'], new_auth[i]['account_name'], new_auth[i]['host_id'], new_auth[i]['host_auth_id']
                )
                # print(str_sql)
                ret = sql_con.ExecProcNonQuery(str_sql)
                if not ret:
                    log.e('can not insert item into `ts_auth`.\n')
                    return False

            # 表改名
            str_sql = 'ALTER TABLE ts_auth RENAME TO __bak_ts_auth;'
            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not rename table `ts_auth` to `__bak_ts_auth`.\n')
                return False

            str_sql = 'ALTER TABLE ts_auth_info RENAME TO __bak_ts_auth_info;'
            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not rename table `ts_auth_info` to `__bak_ts_auth_info`.\n')
                return False

            str_sql = 'ALTER TABLE ts_host_info RENAME TO __bak_ts_host_info;'
            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not rename table `ts_host_info` to `__bak_ts_host_info`.\n')
                return False

            str_sql = 'ALTER TABLE ts_auth_tmp RENAME TO ts_auth;'
            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not rename table `ts_auth_tmp` to `ts_auth`.\n')
                return False

            str_sql = 'ALTER TABLE ts_auth_info_tmp RENAME TO ts_auth_info;'
            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not rename table `ts_auth_info_tmp` to `ts_auth_info`.\n')
                return False

            str_sql = 'ALTER TABLE ts_host_info_tmp RENAME TO ts_host_info;'
            ret = sql_con.ExecProcNonQuery(str_sql)
            if not ret:
                log.e('can not rename table `ts_host_info_tmp` to `ts_host_info`.\n')
                return False


    except:
        log.e('failed.\n')
        return False

    return True


if __name__ == '__main__':
    sys.exit(main())
