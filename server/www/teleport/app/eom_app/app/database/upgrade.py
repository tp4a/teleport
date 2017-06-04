# -*- coding: utf-8 -*-

import json
import os
import shutil

from eom_common.eomcore.logger import log


class DatabaseUpgrade:
    def __init__(self, db, step_begin, step_end):
        self.db = db
        self.step_begin = step_begin
        self.step_end = step_end

    def do_upgrade(self):
        for i in range(self.db.DB_VERSION):
            if self.db.current_ver < i + 1:
                _f_name = '_upgrade_to_v{}'.format(i + 1)
                if _f_name in dir(self):
                    if self.__getattribute__(_f_name)():
                        self.db.current_ver = i + 1
                    else:
                        return False

        return True

    def _upgrade_to_v2(self):
        # 服务端升级到版本1.2.102.3时，管理员后台和普通用户后台合并了，数据库略有调整

        _step = self.step_begin('检查数据库版本v2...')

        try:
            # 判断依据：
            # 如果存在名为 ${prefix}sys_user 的表，说明是旧版本，需要升级

            ret = self.db.is_table_exists('{}sys_user'.format(self.db.table_prefix))
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                self.step_end(_step, 0, '跳过 v1 到 v2 的升级操作')
                return True
            self.step_end(_step, 0, '需要升级到v2')

            if self.db.db_type == self.db.DB_TYPE_SQLITE:
                _step = self.step_begin(' - 备份数据库文件')
                _bak_file = '{}.before-v1-to-v2'.format(self.db.sqlite_file)
                if not os.path.exists(_bak_file):
                    shutil.copy(self.db.sqlite_file, _bak_file)
                self.step_end(_step, 0)

            # 将原来的普通用户的account_type从 0 改为 1
            _step = self.step_begin(' - 调整用户账号类型...')
            if not self.db.exec('UPDATE `{}account` SET `account_type`=1 WHERE `account_type`=0;'.format(self.db.table_prefix)):
                self.step_end(_step, -1)
                return False
            else:
                self.step_end(_step, 0)

            # 将原来的管理员合并到用户账号表中
            _step = self.step_begin(' - 合并管理员和普通用户账号...')
            db_ret = self.db.query('SELECT * FROM `{}sys_user`;'.format(self.db.table_prefix))
            if db_ret is None:
                self.step_end(_step, 0)
                return True

            for i in range(len(db_ret)):
                user_name = db_ret[i][1]
                user_pwd = db_ret[i][2]

                if not self.db.exec("""INSERT INTO `{}account`
    (`account_type`, `account_name`, `account_pwd`, `account_status`, `account_lock`, `account_desc`)
    VALUES (100,"{}","{}",0,0,"{}");""".format(self.db.table_prefix, user_name, user_pwd, '超级管理员')):
                    self.step_end(_step, -1)
                    return False

            # 移除旧的表（暂时改名而不是真的删除）
            _step = self.step_begin(' - 移除不再使用的数据表...')
            if not self.db.exec('ALTER TABLE `{}sys_user` RENAME TO `_bak_ts_sys_user`;'.format(self.db.table_prefix)):
                self.step_end(_step, 0)
                return False
            else:
                self.step_end(_step, -1)

            return True

        except:
            log.e('failed.\n')
            self.step_end(_step, -1)
            return False

    def _upgrade_to_v3(self):
        # 服务端升级到版本1.5.217.9时，为了支持一机多用户多协议，数据库结构有较大程度改动

        _step = self.step_begin('检查数据库版本v3...')

        try:
            # 判断依据：
            # 如果不存在名为 ts_host_info 的表，说明是旧版本，需要升级

            ret = self.db.is_table_exists('{}host_info'.format(self.db.table_prefix))
            if ret is None:
                self.step_end(_step, -1)
                return False
            elif ret:
                self.step_end(_step, 0, '跳过 v2 到 v3 的升级操作')
                return True
            self.step_end(_step, 0, '需要升级到v3')

            if self.db.db_type == self.db.DB_TYPE_SQLITE:
                _step = self.step_begin(' - 备份数据库文件')
                _bak_file = '{}.before-v2-to-v3'.format(self.db.sqlite_file)
                if not os.path.exists(_bak_file):
                    shutil.copy(self.db.sqlite_file, _bak_file)
                self.step_end(_step, 0)

            _step = self.step_begin(' - 调整数据表...')
            if not self.db.exec('ALTER TABLE `{}auth` ADD `host_auth_id` INTEGER;'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '无法在auth表中加入host_auth_id字段')
                return False

            if not self.db.exec('UPDATE `{}auth` SET `host_auth_id`=`host_id`;'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '无法将auth表中host_auth_id字段的值均调整为host_id字段的值')
                return False

            if not self.db.exec('ALTER TABLE `{}log` ADD `protocol` INTEGER;'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '无法在log表中加入protocol字段')
                return False

            if not self.db.exec('UPDATE `{}log` SET `protocol`=1 WHERE `sys_type`=1;'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '无法修正log表中的protocol字段数据(1)')
                return False

            if not self.db.exec('UPDATE `{}log` SET `protocol`=2 WHERE `sys_type`=2;'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '无法修正log表中的protocol字段数据(2)')
                return False

            if not self.db.exec('UPDATE `{}log` SET `ret_code`=9999 WHERE `ret_code`=0;'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '无法修正log表中的ret_code字段数据')
                return False

            self.step_end(_step, 0)
            _step = self.step_begin(' - 拆分数据表...')

            # 新建两个表，用于拆分原来的 ts_host 表
            if not self.db.exec("""CREATE TABLE `{}host_info` (
    `host_id` integer PRIMARY KEY {},
    `group_id`  int(11) DEFAULT 0,
    `host_sys_type`  int(11) DEFAULT 1,
    `host_ip`  varchar(32) DEFAULT '',
    `pro_port`  varchar(255) NULL,
    `host_lock`  int(11) DEFAULT 0,
    `host_desc` varchar(128) DEFAULT ''
    );""".format(self.db.table_prefix, self.db.auto_increment)):
                self.step_end(_step, -1)
                return False

            if not self.db.exec("""CREATE TABLE `{}auth_info` (
    `id`  INTEGER PRIMARY KEY {},
    `host_id`  INTEGER,
    `pro_type`  INTEGER,
    `auth_mode`  INTEGER,
    `user_name`  varchar(255),
    `user_pswd`  varchar(255),
    `cert_id`  INTEGER,
    `encrypt`  INTEGER,
    `log_time`  varchar(60)
    );""".format(self.db.table_prefix, self.db.auto_increment)):
                self.step_end(_step, -1)
                return False

            # 将原来的 ts_host 表改名
            if not self.db.exec('ALTER TABLE `{}host` RENAME TO `_bak_{}host;`'.format(self.db.table_prefix, self.db.table_prefix)):
                self.step_end(_step, -1)
                return False

            self.step_end(_step, 0)
            _step = self.step_begin(' - 调整数据内容...')

            # 从原来 ts_host 表中查询出所有数据
            db_ret = self.db.query('SELECT * FROM `_bak_{}host;`'.format(self.db.table_prefix))
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

                    if host_pro_type == 1:
                        _pro_port['rdp']['enable'] = 1
                        _pro_port['rdp']['port'] = host_pro_port
                    elif host_pro_type == 2:
                        _pro_port['ssh']['enable'] = 1
                        _pro_port['ssh']['port'] = host_pro_port
                    pro_port = json.dumps(_pro_port)

                    sql = 'INSERT INTO `{}host_info` (`host_id`, `group_id`, `host_sys_type`, `host_ip`, `pro_port`, `host_lock`, `host_desc`) ' \
                          'VALUES ({}, {}, {}, "{}", "{}", {}, "{}");'.format(self.db.table_prefix, host_id, group_id, host_sys_type, host_ip, pro_port, host_lock, host_desc)
                    if not self.db.exec(sql):
                        self.step_end(_step, -1)
                        return False

                    sql = 'INSERT INTO `{}auth_info` (`host_id`, `pro_type`, `auth_mode`, `user_name`, `user_pswd`, `cert_id`, `encrypt`, `log_time`) ' \
                          'VALUES ({}, {}, {}, "{}", "{}", {}, {}, "{}");'.format(self.db.table_prefix, host_id, host_pro_type, host_auth_mode, host_user_name, host_user_pwd, cert_id, host_encrypt, '1')
                    if not self.db.exec(sql):
                        self.step_end(_step, -1)
                        return False

            self.step_end(_step, 0)
            return True

        except:
            log.e('failed.\n')
            self.step_end(_step, -1)
            return False

    def _upgrade_to_v4(self):
        _step = self.step_begin('检查数据库版本v4...')

        # 服务端升级到版本1.6.224.3时，加入telnet支持，数据库有调整
        try:
            # 判断依据：
            # 如果ts_host_info表中还有pro_port字段，说明是旧版本，需要升级

            db_ret = self.db.query('SELECT `pro_port` FROM `{}host_info` LIMIT 0;'.format(self.db.table_prefix))
            if db_ret is None:
                self.step_end(_step, 0, '跳过 v3 到 v4 的升级操作')
                return True
            self.step_end(_step, 0, '需要升级到v4')

            if self.db.db_type == self.db.DB_TYPE_SQLITE:
                _step = self.step_begin(' - 备份数据库文件')
                _bak_file = '{}.before-v3-to-v4'.format(self.db.sqlite_file)
                if not os.path.exists(_bak_file):
                    shutil.copy(self.db.sqlite_file, _bak_file)
                self.step_end(_step, 0)

            _step = self.step_begin(' - 为telnet增加默认配置')
            # 如果ts_config表中没有ts_server_telnet_port项，则增加默认值52389
            db_ret = self.db.query('SELECT * FROM `{}config` WHERE `name`="ts_server_telnet_port";'.format(self.db.table_prefix))
            if len(db_ret) == 0:
                if not self.db.exec('INSERT INTO `{}config` (`name`, `value`) VALUES ("ts_server_telnet_port", "52389");'.format(self.db.table_prefix)):
                    self.step_end(_step, -1)
                    return False
            self.step_end(_step, 0)

            _step = self.step_begin(' - 调整认证数据表数据...')
            auth_info_ret = self.db.query('SELECT `id`, `host_id`, `pro_type`, `auth_mode`, `user_name`, `user_pswd`, `cert_id`, `encrypt`, `log_time` FROM `{}auth_info`;'.format(self.db.table_prefix))
            auth_ret = self.db.query('SELECT `auth_id`, `account_name`, `host_id`, `host_auth_id` FROM `{}auth`;'.format(self.db.table_prefix))

            max_host_id = 0
            new_host_info = []
            new_auth_info = []
            new_auth = []

            # 从原来的表中查询数据
            host_info_ret = self.db.query('SELECT `host_id`, `group_id`, `host_sys_type`, `host_ip`, `pro_port`, `host_lock`, `host_desc` FROM {}host_info;'.format(self.db.table_prefix))
            if host_info_ret is None:
                self.step_end(_step, 0, '尚无认证数据，跳过处理')
                return True

            # 先找出最大的host_id，这样如果要拆分一个host，就知道新的host_id应该是多少了
            for i in range(len(host_info_ret)):
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
                            if auth_info_ret[j][2] == 1:  # 用到了此主机的RDP
                                have_rdp = True
                            elif auth_info_ret[j][2] == 2:  # 用到了此主机的SSH
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

            # 现在有了新的ts_host_info表，重构ts_auth_info表
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

            self.step_end(_step, 0)
            _step = self.step_begin(' - 重新整理认证数据表结构及数据...')

            # 将整理好的数据写入新的临时表
            # 先创建三个临时表
            if not self.db.exec("""CREATE TABLE `{}auth_tmp` (
    `auth_id`  INTEGER PRIMARY KEY {},
    `account_name`  varchar(255),
    `host_id`  INTEGER,
    `host_auth_id`  int(11) NOT NULL
    );""".format(self.db.table_prefix, self.db.auto_increment)):
                self.step_end(_step, -1, '无法创建认证数据临时表')
                return False

            if not self.db.exec("""CREATE TABLE `{}host_info_tmp` (
    `host_id`  integer PRIMARY KEY {},
    `group_id`  int(11) DEFAULT 0,
    `host_sys_type`  int(11) DEFAULT 1,
    `host_ip`  varchar(32) DEFAULT '',
    `host_port`  int(11) DEFAULT 0,
    `protocol`  int(11) DEFAULT 0,
    `host_lock`  int(11) DEFAULT 0,
    `host_desc`   DEFAULT ''
    );""".format(self.db.table_prefix, self.db.auto_increment)):
                self.step_end(_step, -1, '无法创建主机信息数据临时表')
                return False

            if not self.db.exec("""CREATE TABLE `{}auth_info_tmp` (
    `id`  INTEGER PRIMARY KEY {},
    `host_id`  INTEGER,
    `auth_mode`  INTEGER,
    `user_name`  varchar(255),
    `user_pswd`  varchar(255),
    `user_param` varchar(255),
    `cert_id`  INTEGER,
    `encrypt`  INTEGER,
    `log_time`  varchar(60)
    );""".format(self.db.table_prefix, self.db.auto_increment)):
                self.step_end(_step, -1, '无法创建认证信息数据临时表')
                return False

            for i in range(len(new_host_info)):
                sql = 'INSERT INTO `{}host_info_tmp` (`host_id`, `group_id`, `host_sys_type`, `host_ip`, `host_port`, `protocol`, `host_lock`, `host_desc`) ' \
                      'VALUES ({}, {}, {}, \'{}\', {}, {}, {}, "{}");'.format(
                    self.db.table_prefix,
                    new_host_info[i]['host_id'], new_host_info[i]['group_id'], new_host_info[i]['host_sys_type'],
                    new_host_info[i]['host_ip'], new_host_info[i]['host_port'], new_host_info[i]['protocol'],
                    new_host_info[i]['host_lock'], new_host_info[i]['host_desc']
                )
                if not self.db.exec(sql):
                    self.step_end(_step, -1, '无法调整数据(1)')
                    return False

            for i in range(len(new_auth_info)):
                sql = 'INSERT INTO `{}auth_info_tmp` (`id`, `host_id`, `auth_mode`, `user_name`, `user_pswd`, `user_param`, `cert_id`, `encrypt`, `log_time`) ' \
                      'VALUES ({}, {}, {}, "{}", "{}", "{}", {}, {}, "{}");'.format(
                    self.db.table_prefix,
                    new_auth_info[i]['id'], new_auth_info[i]['host_id'], new_auth_info[i]['auth_mode'],
                    new_auth_info[i]['user_name'], new_auth_info[i]['user_pswd'], new_auth_info[i]['user_param'],
                    new_auth_info[i]['cert_id'], new_auth_info[i]['encrypt'], '1'
                )
                if not self.db.exec(sql):
                    self.step_end(_step, -1, '无法调整数据(2)')
                    return False

            for i in range(len(new_auth)):
                sql = 'INSERT INTO `{}auth_tmp` (`auth_id`, `account_name`, `host_id`, `host_auth_id`) ' \
                      'VALUES ({}, \'{}\', {}, {});'.format(
                    self.db.table_prefix,
                    new_auth[i]['auth_id'], new_auth[i]['account_name'], new_auth[i]['host_id'], new_auth[i]['host_auth_id']
                )
                if not self.db.exec(sql):
                    self.step_end(_step, -1, '无法调整数据(3)')
                    return False

            # 表改名
            if not self.db.exec('ALTER TABLE `{}auth` RENAME TO `__bak_{}auth`;'.format(self.db.table_prefix, self.db.table_prefix)):
                self.step_end(_step, -1, '无法处理临时表(1)')
                return False

            if not self.db.exec('ALTER TABLE `{}auth_info` RENAME TO `__bak_{}auth_info`;'.format(self.db.table_prefix, self.db.table_prefix)):
                self.step_end(_step, -1, '无法处理临时表(2)')
                return False

            if not self.db.exec('ALTER TABLE `{}host_info` RENAME TO `__bak_{}host_info`;'.format(self.db.table_prefix, self.db.table_prefix)):
                self.step_end(_step, -1, '无法处理临时表(3)')
                return False

            if not self.db.exec('ALTER TABLE `{}auth_tmp` RENAME TO `{}auth`;'.format(self.db.table_prefix, self.db.table_prefix)):
                self.step_end(_step, -1, '无法处理临时表(4)')
                return False

            if not self.db.exec('ALTER TABLE `{}auth_info_tmp` RENAME TO `{}auth_info`;'.format(self.db.table_prefix, self.db.table_prefix)):
                self.step_end(_step, -1, '无法处理临时表(5)')
                return False

            if not self.db.exec('ALTER TABLE `{}host_info_tmp` RENAME TO `{}host_info`;'.format(self.db.table_prefix, self.db.table_prefix)):
                self.step_end(_step, -1, '无法处理临时表(6)')
                return False

            self.step_end(_step, 0)
            return True

        except:
            log.e('failed.\n')
            self.step_end(_step, -1)
            return False

    def _upgrade_to_v5(self):
        _step = self.step_begin('检查数据库版本v5...')

        # 服务端升级到版本2.1.0.1时，为解决将来数据库升级的问题，在 ts_config 表中加入 db_ver 指明当前数据结构版本
        try:
            # 判断依据：
            # 如果 config 表中不存在名为db_ver的数据，说明是旧版本，需要升级

            if not self.db.is_table_exists('{}config'.format(self.db.table_prefix)):
                if not self.db.exec("""CREATE TABLE `{}config` (
    `name`  varchar(128) NOT NULL,
    `value`  varchar(255),
    PRIMARY KEY (`name` ASC)
);""".format(self.db.table_prefix)):
                    self.step_end(_step, -1, 'config表不存在且无法创建')
                    return False

            db_ret = self.db.query('SELECT `value` FROM `{}config` WHERE `name`="db_ver";'.format(self.db.table_prefix))
            if db_ret is None:
                self.step_end(_step, -1)
                return False
            if len(db_ret) > 0 and int(db_ret[0][0]) >= self.db.DB_VERSION:
                self.step_end(_step, 0, '跳过 v4 到 v5 的升级操作')
                return True
            self.step_end(_step, 0, '需要升级到v5')

            _step = self.step_begin(' - 调整数据表字段名与表名')
            if not self.db.exec('ALTER TABLE `{}cert` RENAME TO `{}key`;'.format(self.db.table_prefix, self.db.table_prefix)):
                self.step_end(_step, -1)
                return False
            self.step_end(_step, 0)

            _step = self.step_begin(' - 更新数据库版本号')
            if not self.db.exec('INSERT INTO `{}config` VALUES ("db_ver", "{}");'.format(self.db.table_prefix, self.db.DB_VERSION)):
                self.step_end(_step, -1)
                return False
            else:
                self.step_end(_step, 0)
                return True

        except:
            log.e('failed.\n')
            self.step_end(_step, -1)
            return False

    def _upgrade_to_v6(self):
        _step = self.step_begin('检查数据库版本v6...')

        # 服务端升级到版本2.2.9时，为增加双因子认证，为account表增加oath_secret字段
        db_ret = self.db.is_field_exists('{}account'.format(self.db.table_prefix), 'oath_secret')
        if db_ret is None:
            self.step_end(_step, -1, '无法连接到数据库')
            return False
        if db_ret:
            self.step_end(_step, 0, '跳过 v5 到 v6 的升级操作')
            return True

        self.step_end(_step, 0, '需要升级到v6')

        try:

            _step = self.step_begin(' - 在account表中加入oath_secret字段')
            if not self.db.exec('ALTER TABLE {}account ADD oath_secret VARCHAR(64) DEFAULT ""'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '失败')
                return False

            _step = self.step_begin(' - 更新数据库版本号')
            if not self.db.exec('UPDATE `{}config` SET `value`="6" WHERE `name`="db_ver";'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '无法更新数据库版本号')
                return False
            else:
                self.step_end(_step, 0)
                return True

        except:
            log.e('failed.\n')
            self.step_end(_step, -1)
            return False
