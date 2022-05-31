# -*- coding: utf-8 -*-

# from app.const import *
# from app.logic.auth.password import tp_password_generate_secret
# from app.base.utils import tp_timestamp_sec
from app.base.logger import log
# import shutil


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

    def _db_exec(self, msg, sql):
        _step = self.step_begin(msg)

        ret = False
        if type(sql) == str:
            ret = self.db.exec(sql)
        elif type(sql) == list or type(sql) == set:
            for s in sql:
                ret = self.db.exec(s)
                if not ret:
                    break
        else:
            raise RuntimeError('[FAILED] internal error.')

        if not ret:
            self.step_end(_step, -1)
            raise RuntimeError('[FAILED] {}'.format(sql))
        else:
            self.step_end(_step, 0)

    def _upgrade_to_v7(self):
        # 注意：v2.x的最后版本时，数据库版本号为v6，但是v3.0.0技术预览版未升级数据库版本号，仍然为v6
        #      因此升级时要做检查，如果是当前数据库版本号为v6，要进一步判断是否为v2.x系列的数据库。
        # 服务端升级到v3.2.2时，数据库有部分调整
        _step = self.step_begin('检查数据库版本 v7...')

        try:
            # 检查是否是 v2.x 版本的数据库（也是v6版数据库）
            # 依据为，v3.x的服务端开始，数据库中有 tp_role 数据表。
            ret = self.db.is_table_exists('{}role'.format(self.db.table_prefix))
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                self.step_end(_step, -1, '抱歉，不支持从v2.x升级到v3.x，数据库不兼容！请卸载旧版本，全新安装新版本！')
                return True
        except:
            log.e('failed.\n')
            self.step_end(_step, -1)
            return False

        self.step_end(_step, 0, '需要升级')

        try:
            # 1. 创建缺失的 core_server 表
            _step = self.step_begin(' - 检查 core_server 数据表...')
            ret = self.db.is_table_exists('{}core_server'.format(self.db.table_prefix))
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                _step = self.step_begin(' - 创建数据表 core_server...')
                self._v7_create_core_server()
                self._db_exec(
                    ' - 设置本机核心服务配置项...',
                    'INSERT INTO `{}core_server` (`sn`, `secret`, `ip`, `port`, `state`) VALUES '
                    '("0000", "", "127.0.0.1", 52080, 1);'
                    ''.format(self.db.table_prefix)
                )
                self.step_end(_step, 0)

            # 2. 检查 user 表中是否有 ldap_dn/valid_from/valid_to 字段
            _step = self.step_begin(' - 检查 user 数据表 ldap_dn 字段...')
            ret = self.db.is_field_exists('{}user'.format(self.db.table_prefix), 'ldap_dn')
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                if not self.db.exec('ALTER TABLE `{}user` ADD `ldap_dn` VARCHAR(128) DEFAULT ""'.format(self.db.table_prefix)):
                    self.step_end(_step, -1, '失败')
                    return False
                else:
                    self.step_end(_step, 0)

            _step = self.step_begin(' - 检查 user 数据表 valid_from 字段...')
            ret = self.db.is_field_exists('{}user'.format(self.db.table_prefix), 'valid_from')
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                if not self.db.exec('ALTER TABLE `{}user` ADD `valid_from` INT(11) DEFAULT 0'.format(self.db.table_prefix)):
                    self.step_end(_step, -1, '失败')
                    return False
                else:
                    self.step_end(_step, 0)

            _step = self.step_begin(' - 检查 user 数据表 valid_to 字段...')
            ret = self.db.is_field_exists('{}user'.format(self.db.table_prefix), 'valid_to')
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                if not self.db.exec('ALTER TABLE `{}user` ADD `valid_to` INT(11) DEFAULT 0'.format(self.db.table_prefix)):
                    self.step_end(_step, -1, '失败')
                    return False
                else:
                    self.step_end(_step, 0)

            # 3. 检查 acc 表中是否有 host_ip/router_ip/router_port 字段
            _step = self.step_begin(' - 检查 acc 数据表 host_ip 字段...')
            ret = self.db.is_field_exists('{}acc'.format(self.db.table_prefix), 'host_ip')
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                if not self.db.exec('ALTER TABLE `{}acc` ADD `host_ip` VARCHAR(40) DEFAULT ""'.format(self.db.table_prefix)):
                    self.step_end(_step, -1, '失败')
                    return False
            self.step_end(_step, 0)

            _step = self.step_begin(' - 检查 acc 数据表 router_ip 字段...')
            ret = self.db.is_field_exists('{}acc'.format(self.db.table_prefix), 'router_ip')
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                if not self.db.exec('ALTER TABLE `{}acc` ADD `router_ip` VARCHAR(40) DEFAULT ""'.format(self.db.table_prefix)):
                    self.step_end(_step, -1, '失败')
                    return False
            self.step_end(_step, 0)

            _step = self.step_begin(' - 检查 acc 数据表 router_port 字段...')
            ret = self.db.is_field_exists('{}acc'.format(self.db.table_prefix), 'router_port')
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                if not self.db.exec('ALTER TABLE `{}acc` ADD `router_port` INT(11) DEFAULT 0'.format(self.db.table_prefix)):
                    self.step_end(_step, -1, '失败')
                    return False
            self.step_end(_step, 0)

            # 4. 检查 record 表中是否有 core_sn/reason 字段
            _step = self.step_begin(' - 检查 record 数据表 core_sn 字段...')
            ret = self.db.is_field_exists('{}record'.format(self.db.table_prefix), 'core_sn')
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                if not self.db.exec('ALTER TABLE `{}record` ADD `core_sn` VARCHAR(5) DEFAULT "0000"'.format(self.db.table_prefix)):
                    self.step_end(_step, -1, '失败')
                    return False
            self.step_end(_step, 0)

            _step = self.step_begin(' - 检查 record 数据表 reason 字段...')
            ret = self.db.is_field_exists('{}record'.format(self.db.table_prefix), 'reason')
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                if not self.db.exec('ALTER TABLE `{}record` ADD `reason` VARCHAR(255) DEFAULT ""'.format(self.db.table_prefix)):
                    self.step_end(_step, -1, '失败')
                    return False
            self.step_end(_step, 0)

            _step = self.step_begin(' - 更新数据库版本号...')
            if not self.db.exec('UPDATE `{}config` SET `value`="7" WHERE `name`="db_ver";'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '无法更新数据库版本号')
                return False
            self.step_end(_step, 0)

            _step = self.step_begin('升级到 v7 完成')
            self.step_end(_step, 0)

            return True

        except:
            log.e('failed.\n')
            self.step_end(_step, -1)
            return False

    def _v7_create_core_server(self):
        """ 核心服务（为分布式准备）
        v7 新增
        特别注意：分布式部署时，核心服务的RPC通讯端口仅允许来自web服务的IP访问
        """
        f = list()
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        f.append('`sn` varchar(5) NOT NULL')
        f.append('`desc` varchar(255) DEFAULT ""')
        f.append('`secret` varchar(64) DEFAULT ""')
        f.append('`ip` varchar(128) NOT NULL')
        f.append('`port` int(11) DEFAULT 0')
        f.append('`state` int(3) DEFAULT 1')
        self._db_exec(
            ' - 创建核心服务器表...',
            'CREATE TABLE `{}core_server` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _upgrade_to_v8(self):
        _step = self.step_begin('准备升级到数据库版本 v8...')
        self.step_end(_step, 0, '')

        try:
            # 1. 创建新增的 integration_auth 表
            _step = self.step_begin(' - 检查 integration_auth 数据表...')
            ret = self.db.is_table_exists('{}integration_auth'.format(self.db.table_prefix))
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                _step = self.step_begin(' - 创建数据表 integration_auth...')
                self._v8_integration_auth()
                self.step_end(_step, 0)

            # 2. 创建新增的 ops_token 表
            _step = self.step_begin(' - 检查 ops_token 数据表...')
            ret = self.db.is_table_exists('{}ops_token'.format(self.db.table_prefix))
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                _step = self.step_begin(' - 创建数据表 ops_token...')
                self._v8_ops_token()
                self.step_end(_step, 0)

            # 3. 创建新增的 ops_token 表
            _step = self.step_begin(' - 检查 ops_token_key 数据表...')
            ret = self.db.is_table_exists('{}ops_token_key'.format(self.db.table_prefix))
            if ret is None:
                self.step_end(_step, -1, '无法连接到数据库')
                return False
            elif not ret:
                _step = self.step_begin(' - 创建数据表 ops_token_key...')
                self._v8_ops_token_key()
                self.step_end(_step, 0)

            # 4. 更新数据库版本号
            _step = self.step_begin('更新数据库版本号...')
            if not self.db.exec('UPDATE `{}config` SET `value`="8" WHERE `name`="db_ver";'.format(self.db.table_prefix)):
                self.step_end(_step, -1, '无法更新数据库版本号')
                return False
            self.step_end(_step, 0)

            _step = self.step_begin('升级到 v8 完成')
            self.step_end(_step, 0)

            return True

        except:
            log.e('failed.\n')
            self.step_end(_step, -1)
            return False

    def _v8_integration_auth(self):
        """ 第三方服务集成认证信息（v8版新增）"""
        f = list()
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        f.append('`acc_key` varchar(32) DEFAULT ""')
        f.append('`acc_sec` varchar(64) DEFAULT ""')
        f.append('`role_id` int(11) DEFAULT 0')
        f.append('`name` varchar(64) DEFAULT ""')
        f.append('`comment` varchar(64) DEFAULT ""')
        f.append('`creator_id` int(11) DEFAULT 0')
        f.append('`create_time` int(11) DEFAULT 0')
        self._db_exec(
            ' - 创建第三方服务集成认证信息表...',
            'CREATE TABLE `{}integration_auth` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _v8_ops_token(self):
        """ 远程连接授权码（用于客户端软件配置，无需登录TP-WEB，可直接进行远程）（v8版新增） """
        f = list()
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        f.append('`mode` int(5) DEFAULT 0')
        f.append('`token` varchar(32) NOT NULL')
        f.append('`uni_id` varchar(128) DEFAULT ""')
        f.append('`u_id` int(11) DEFAULT 0')
        f.append('`acc_id` int(11) DEFAULT 0')
        f.append('`valid_from` int(11) DEFAULT 0')
        f.append('`valid_to` int(11) DEFAULT 0')
        self._db_exec(
            ' - 创建远程连接授权码表...',
            'CREATE TABLE `{}ops_token` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _v8_ops_token_key(self):
        """ 远程连接临时授权码对应Key（v8版新增） """
        f = list()
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        f.append('`ops_token_id` int(11) DEFAULT 0')
        f.append('`password` varchar(32) DEFAULT ""')
        self._db_exec(
            ' - 创建远程连接授权码表...',
            'CREATE TABLE `{}ops_token_key` ({});'.format(self.db.table_prefix, ','.join(f))
        )
