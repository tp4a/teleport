# -*- coding: utf-8 -*-

from app.const import *
from app.logic.auth.password import tp_password_generate_secret
from app.base.utils import tp_timestamp_utc_now
from app.base.logger import log


class DatabaseInit:
    def __init__(self, db, step_begin, step_end):
        self.db = db
        self.step_begin = step_begin
        self.step_end = step_end

    def do_create_and_init(self, sysadmin, email, password):
        try:
            self._create_config()
            self._create_core_server()
            self._create_role()
            self._create_user()
            self._create_user_rpt()
            self._create_host()
            self._create_acc()
            self._create_acc_auth()
            self._create_group()
            self._create_group_map()
            self._create_ops_policy()
            self._create_ops_auz()
            self._create_ops_map()
            self._create_audit_policy()
            self._create_audit_auz()
            self._create_audit_map()
            self._create_syslog()
            self._create_record()
            self._create_record_audit()
            self._make_builtin_data(sysadmin, email, password)
        except:
            log.e('[db] can not create and initialize database.\n')
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

    def _create_config(self):
        """ 配置表
        所有的配置项均以字符串形式存储，可以使用JSON化的数据格式
        """

        f = list()

        # name: 配置项名称
        f.append('`name` varchar(64) NOT NULL')
        # name: 配置项内容
        f.append('`value` varchar(255) NOT NULL')

        # 设置主键
        f.append('PRIMARY KEY (`name` ASC)')

        self._db_exec(
            '创建配置项表...',
            'CREATE TABLE `{}config` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_core_server(self):
        """ 核心服务（为分布式准备）
        特别注意：分布式部署时，核心服务的RPC通讯端口仅允许来自web服务的IP访问
        """

        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        # sn: 核心服务主机编号（4位数字构成的字符串，全0表示运行在与web服务同一台主机上）
        f.append('`sn` varchar(5) NOT NULL')
        # desc: 核心服务主机描述
        f.append('`desc` varchar(255) DEFAULT ""')

        # secret: 核心服务主机密钥（核心服务主机需要配置此密钥才能连接web服务）
        f.append('`secret` varchar(64) DEFAULT ""')

        # ip: 核心服务主机的RPC服务IP和端口，用于合成RPC访问地址，例如 http://127.0.0.1:52080/rpc
        f.append('`ip` varchar(128) NOT NULL')
        f.append('`port` int(11) DEFAULT 0')

        # state: 状态，1=正常，2=禁用，3=离线，4=重启中，5=版本不匹配
        f.append('`state` int(3) DEFAULT 1')

        self._db_exec(
            '创建核心服务器表...',
            'CREATE TABLE `{}core_server` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_role(self):
        """ 角色
        """

        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        # name: 角色名称
        f.append('`name` varchar(128) NOT NULL')
        # desc: 角色描述
        f.append('`desc` varchar(255) DEFAULT ""')

        # privilege: 权限，可按位异或组合，请参考 TP_PRIVILEGE_XXXX 定义
        f.append('`privilege` bigint(11) DEFAULT 0')

        # creator_id: 创建者的id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')

        self._db_exec(
            '创建角色表...',
            'CREATE TABLE `{}role` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_user(self):
        """ 用户账号
        """

        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        # role_id: 角色id, 关联到role表
        f.append('`role_id` int(11) DEFAULT 0')

        # username: teleport系统登录名
        f.append('`username` varchar(32) NOT NULL')
        # surname: 真实姓名
        f.append('`surname` varchar(64) DEFAULT ""')
        # type 1=本地账号，2=LDAP（待扩展）
        f.append('`type` int(11) DEFAULT 1')
        # ldap_dn: 用户的ldap全路径名称，仅用于LDAP导入的用户
        f.append('`ldap_dn` varchar(128) DEFAULT ""')
        # avatar: 用户头像图片地址
        f.append('`avatar` varchar(64) DEFAULT ""')
        # auth_type: 0=使用全局设置，其他参考 TP_LOGIN_AUTH_XXX 系列值
        f.append('`auth_type` int(11) DEFAULT 0')
        # password: 登录密码（如果是LDAP账号则忽略此字段）
        f.append('`password` varchar(128) DEFAULT ""')
        # oath_secret: 身份验证器密钥
        f.append('`oath_secret` varchar(64) DEFAULT ""')
        # state: 状态，1=正常，2=禁用，3=临时锁定
        f.append('`state` int(3) DEFAULT 1')
        # fail_count: 连续登录失败的次数（根据设置，超过一定数量时将临时锁定）
        f.append('`fail_count` int(11) DEFAULT 0')
        # lock_time: 账户被锁定的时间（根据设置，超过一定时间后可以自动解锁）
        f.append('`lock_time` int(11) DEFAULT 0')
        # last_chpass: 最近一次修改密码时间（根据设置，密码可能有有效期限制）
        f.append('`last_chpass` int(11) DEFAULT 0')
        # email: 用户邮箱
        f.append('`email` varchar(64) DEFAULT ""')
        f.append('`mobile` varchar(24) DEFAULT ""')
        f.append('`qq` varchar(24) DEFAULT ""')
        f.append('`wechat` varchar(32) DEFAULT ""')
        f.append('`desc` varchar(255) DEFAULT ""')

        # login_time: 本次成功登录时间
        f.append('`login_time` int(11) DEFAULT 0')
        # last_login: 最近一次成功登录时间
        f.append('`last_login` int(11) DEFAULT 0')
        # login_ip: 本次成功登录IP
        f.append('`login_ip` varchar(40) DEFAULT ""')
        # last_ip: 最近一次成功登录IP
        f.append('`last_ip` varchar(40) DEFAULT ""')

        # creator_id: 创建者的用户id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')

        self._db_exec(
            '创建用户表...',
            'CREATE TABLE `{}user` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_user_rpt(self):
        """ 用户忘记密码时重置需要进行验证的token，24小时有效
        rpt = Reset Password Token
        """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        # user_id:  user's id
        f.append('`user_id` int(11) DEFAULT 0')
        # token: token
        f.append('`token` varchar(48) DEFAULT ""')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')

        self._db_exec(
            '创建用户密码重置表...',
            'CREATE TABLE `{}user_rpt` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_group(self):
        """ 组信息（各种组，包括用户组、主机组、账号组等）
        """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        # type  2=用户组，4=远程账号组，6=资产组（主机）
        f.append('`type` int(11) DEFAULT 0')
        # name: 组名称
        f.append('`name` varchar(128) DEFAULT ""')
        # desc: 详细描述
        f.append('`desc` varchar(255) DEFAULT ""')

        # state: 状态，1=正常，2=禁用
        f.append('`state` int(3) DEFAULT 1')

        # creator_id: 创建者的id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')

        self._db_exec(
            '创建组信息表...',
            'CREATE TABLE `{}group` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_group_map(self):
        """ 组与成员的映射关系
        """

        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        # type  2=用户组，4=远程账号组，6=资产组（主机）
        f.append('`type` int(11) DEFAULT 0')
        # gid: 组的ID
        f.append('`gid` int(11) DEFAULT 0')
        # mid: 成员的ID
        f.append('`mid` int(11) DEFAULT 0')

        self._db_exec(
            '创建组成员映射表...',
            'CREATE TABLE `{}group_map` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_host(self):
        """ 主机
        """

        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))

        # type  0=未分类，1=物理主机，2=虚拟主机，3=路由器，4=交换机
        f.append('`type` int(11) DEFAULT 0')
        # os_type: 操作系统类型，1=win（101=win2003srv，102=win2008srv，etc...），2=linux（201=ubuntu，202=centos，etc...），3=others.
        f.append('`os_type` int(11) DEFAULT 1')
        # os_ver: 操作系统具体名称和版本，可选（手工填写，将来可以通过自动发现功能自动获取）
        f.append('`os_ver` varchar(128) DEFAULT ""')
        # name: 名称，用于快速区分
        f.append('`name` varchar(64) DEFAULT ""')

        # ip: IP地址，长度40是为了将来的ipv6准备的，IPV6=X:X:X:X:X:X:X:X，每个X为最长4字节，总计39字节
        f.append('`ip` varchar(40) NOT NULL')
        # router_ip: 路由IP，仅用于路由连接模式（即，teleport与远程主机之间有路由网关，该路由网关通过端口映射不同的远程主机）
        f.append('`router_ip` varchar(40) DEFAULT ""')
        # router_port: 路由端口，仅用于路由连接模式
        f.append('`router_port` int(11) DEFAULT 0')

        # state: 状态，1=正常，2=禁用
        f.append('`state` int(3) DEFAULT 1')
        # acc_count: 远程账号数量（注意创建/删除远程账号时更新此数据）
        f.append('`acc_count` int(11) DEFAULT 0')
        # cid: 公司内部用，资产统一编号
        f.append('`cid` varchar(64) DEFAULT ""')

        # desc: 对此资产的详细描述
        f.append('`desc` varchar(255) DEFAULT ""')

        # creator_id: 账号创建者的id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')

        # 将来使用host_attr表来动态扩展主机信息

        self._db_exec(
            '创建主机表...',
            'CREATE TABLE `{}host` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_acc(self):
        """ 账号 """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        # host_id: 对应的主机ID
        f.append('`host_id` int(11) DEFAULT 0')

        # 下面三个主机相关字段用于显示（注意更新host表时同步更新此字段）

        # host_ip: 主机IP地址
        f.append('`host_ip` varchar(40) NOT NULL')
        # router_ip: 路由IP
        f.append('`router_ip` varchar(40) DEFAULT ""')
        # router_port: 路由端口
        f.append('`router_port` int(11) DEFAULT 0')

        # protocol_type: 协议类型，0=？，1=SSH，2=RDP，3=TELNET
        f.append('`protocol_type` int(11) DEFAULT 0')
        # protocol_port: 协议端口，0=主机使用端口映射方式，需要使用对应主机的router_addr进行连接
        f.append('`protocol_port` int(11) DEFAULT 0')
        # state: 状态，1=正常，2=禁用
        f.append('`state` int(3) DEFAULT 1')

        # acc_auth_id: 认证信息数据ID
        #  如果 acc_auth_id 不为0，则表示此条账号信息记录中的认证数据是从对应的 acc_auth_id 相同的
        #  在更新 acc_auth_id 对应数据时，同步更新本条目的数据
        #  且在 acc_auth_id 被引用的前提下，不允许删除 acc_auth 表中对应记录
        f.append('`acc_auth_id` int(11) DEFAULT 0')

        # auth_type: 登录认证类型：0=无认证，1=password，2=public-key
        f.append('`auth_type` int(11) DEFAULT 0')
        # username: 登录账号
        f.append('`username` varchar(128) DEFAULT ""')
        # username_prompt: 输入用户名的提示（仅用于telnet协议）
        f.append('`username_prompt` varchar(128) DEFAULT ""')
        # password_prompt: 输入密码的提示（仅用于telnet协议）
        f.append('`password_prompt` varchar(128) DEFAULT ""')
        # password: 登录密码（仅当auth=1时有效）
        f.append('`password` varchar(255) DEFAULT ""')
        # pri_key: 私钥（仅当auth=2时有效）
        f.append('`pri_key` varchar(4096) DEFAULT ""')

        # creator_id: 账号创建者的id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')
        # last_secret: 最后一次改密时间
        f.append('`last_secret` int(11) DEFAULT 0')

        self._db_exec(
            '创建账号表...',
            'CREATE TABLE `{}acc` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_acc_auth(self):
        """ 账号认证信息 """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        # name: 此条账号认证信息的名称，用于显示
        f.append('`name` varchar(128) DEFAULT ""')

        # auth_type: 登录认证类型：0=无认证，1=password，2=public-key
        f.append('`auth_type` int(11) DEFAULT 0')
        # username: 登录账号
        f.append('`username` varchar(128) DEFAULT ""')
        # username_prompt: 输入用户名的提示（仅用于telnet协议）
        f.append('`username_prompt` varchar(128) DEFAULT ""')
        # password_prompt: 输入密码的提示（仅用于telnet协议）
        f.append('`password_prompt` varchar(128) DEFAULT ""')
        # password: 登录密码（仅当auth=1时有效）
        f.append('password varchar(255) DEFAULT ""')
        # pri_key: 私钥（仅当auth=2时有效）
        f.append('`pri_key` varchar(4096) DEFAULT ""')

        # creator_id: 创建者的id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')

        self._db_exec(
            '创建账号认证信息表...',
            'CREATE TABLE `{}acc_auth` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_ops_policy(self):
        """ 远程运维授权策略 """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))

        # rank: 排序，非常重要，影响到策略生效的顺序
        f.append('`rank` int(11) DEFAULT 0')

        # name: 策略名称
        f.append('`name` varchar(128) DEFAULT ""')
        # desc: 策略描述
        f.append('`desc` varchar(255) DEFAULT ""')
        # start_time: 策略有效期起始时间(为0则忽略)
        f.append('`start_time` int(11) DEFAULT 0')
        # end_time: 策略有效期结束时间(为0则忽略)
        f.append('`end_time` int(11) DEFAULT 0')

        # state: 状态，1=正常，2=禁用
        f.append('`state` int(3) DEFAULT 1')

        # limit_ip: 是否启用来源限制，0=不限制，1=白名单，2=黑名单（尚未实现）
        f.append('`limit_ip` int(3) DEFAULT 0')
        # ip_list: 限制IP列表（白名单或者黑名单）
        f.append('`ip_list` TEXT')

        # limit_time: 是否启用限时连接，0=不限制，1=限制（尚未实现）
        f.append('`limit_time` int(3) DEFAULT 0')
        # 每一个weekX表示一天的时间段，按位异或表示24个小时的每个小时是否限制连接，对应位为0表示不限制（允许连接）
        f.append('`limit_week1` int(11) DEFAULT 0')
        f.append('`limit_week2` int(11) DEFAULT 0')
        f.append('`limit_week3` int(11) DEFAULT 0')
        f.append('`limit_week4` int(11) DEFAULT 0')
        f.append('`limit_week5` int(11) DEFAULT 0')
        f.append('`limit_week6` int(11) DEFAULT 0')
        f.append('`limit_week7` int(11) DEFAULT 0')

        # flag_record: 会话记录标记（可异或）
        #  0x1=允许记录会话历史（可回放录像），0x2=允许实时监控（尚未实现）
        f.append('`flag_record` bigint(11) DEFAULT {}'.format(TP_FLAG_ALL))

        # flag_rdp: RDP标志（可异或）
        #  0x1=允许远程桌面，0x2=允许剪贴板，0x4=允许磁盘映射，0x8=允许远程APP（尚未实现）
        #  0x1000=允许连接到管理员会话（RDP的console选项）
        f.append('`flag_rdp` bigint(11) DEFAULT {}'.format(TP_FLAG_ALL))
        # flag_ssh: SSH标志（可异或）
        #  0x1=允许SHELL，0x2=允许SFTP，0x4=允许X11转发（尚未实现），0x8=允许exec执行远程命令（尚未实现）,0x10=allow tunnel(not impl.)
        f.append('`flag_ssh` bigint(11) DEFAULT {}'.format(TP_FLAG_ALL))
        # flag_telnet: TELNET标志（可异或）
        f.append('`flag_telnet` bigint(11) DEFAULT {}'.format(TP_FLAG_ALL))
        # flag_1: 备用标志
        f.append('`flag_1` bigint(11) DEFAULT 0')
        # flag_2: 备用标志
        f.append('`flag_2` bigint(11) DEFAULT 0')

        # creator_id: 创建者的id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')

        self._db_exec(
            '创建运维授权策略表...',
            'CREATE TABLE `{}ops_policy` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_ops_auz(self):
        """ 运维授权策略明细 """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))

        # policy_id: 所属的策略
        f.append('`policy_id` int(11) DEFAULT 0')

        # type 指明本条记录是授权还是被授权，0=授权（操作者：用户/用户组），1=被授权（资产：主机/主机组/账号/账号组）
        f.append('`type` int(11) DEFAULT 0')

        # rtype : 外链对象类型
        #  - 1 = 用户
        #  - 2 = 用户组
        #  - 3 = 账号
        #  - 4 = 账号组
        #  - 5 = 主机
        #  - 6 = 主机组
        f.append('`rtype` int(11) DEFAULT 0')
        # rid: 外链对象的ID
        f.append('`rid` int(11) DEFAULT 0')
        # name: 外链对象的名称
        f.append('`name` varchar(64) DEFAULT ""')
        # state: 状态，1=正常，2=禁用，3=临时锁定
        f.append('`state` int(3) DEFAULT 1')

        # creator_id: 创建者的id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')

        self._db_exec(
            '创建运维授权策略明细表...',
            'CREATE TABLE `{}ops_auz` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_ops_map(self):
        """ 运维授权映射 """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))

        # uni_id: 快速定位的索引 "pid-guid-uid-ghid-hid-gaid-aid"
        f.append('`uni_id` varchar(128) NOT NULL')
        # ua_id: 快速定位的索引 "user_id - account-id"
        f.append('`ua_id` varchar(36) NOT NULL')

        # p_id: 授权策略ID
        f.append('`p_id` int(11) DEFAULT 0')
        # p_rank: 授权策略顺序
        f.append('`p_rank` int(11) DEFAULT 0')
        # p_state: 授权策略状态
        f.append('`p_state` int(11) DEFAULT 0')

        # policy_auth_type: 授权方式（0=未知，1=用户:账号，2=用户:账号组，3=用户:主机，4=用户:主机组，5=用户组:账号，6=用户组:账号组，7=用户组:主机，8=用户组:主机组）
        f.append('`policy_auth_type` int(11) DEFAULT 0')

        # u_id: 用户ID
        f.append('`u_id` int(11) DEFAULT 0')
        # u_state: 用户状态
        f.append('`u_state` int(11) DEFAULT 0')
        # gu_id: 用户组ID
        f.append('`gu_id` int(11) DEFAULT 0')
        # gu_state: 用户组状态
        f.append('`gu_state` int(11) DEFAULT 0')

        # h_id: 主机ID
        f.append('`h_id` int(11) DEFAULT 0')
        # h_state: 主机状态
        f.append('`h_state` int(11) DEFAULT 0')
        # gh_id: 主机组ID
        f.append('`gh_id` int(11) DEFAULT 0')
        # gh_state: 主机组状态
        f.append('`gh_state` int(11) DEFAULT 0')

        # a_id: 账号ID
        f.append('`a_id` int(11) DEFAULT 0')
        # a_state: 账号状态
        f.append('`a_state` int(11) DEFAULT 0')
        # ga_id: 账号组ID
        f.append('`ga_id` int(11) DEFAULT 0')
        # ga_state: 账号组状态
        f.append('`ga_state` int(11) DEFAULT 0')

        # 后续字段仅用于显示

        # u_name: 用户登录名
        f.append('`u_name` varchar(32) DEFAULT ""')
        # u_surname: 用户姓名
        f.append('`u_surname` varchar(64) DEFAULT ""')

        # h_name: 主机名称
        f.append('`h_name` varchar(64) DEFAULT ""')
        # ip: IP地址
        f.append('`ip` varchar(40) NOT NULL')
        # router_ip: 路由IP
        f.append('`router_ip` varchar(40) DEFAULT ""')
        # router_port: 路由端口
        f.append('`router_port` int(11) DEFAULT 0')

        # a_name: 登录账号
        f.append('`a_name` varchar(128) DEFAULT ""')
        # protocol_type: 协议类型，0=？，1=SSH，2=RDP，3=TELNET
        f.append('`protocol_type` int(11) DEFAULT 0')
        # protocol_port: 协议端口
        f.append('`protocol_port` int(11) DEFAULT 0')

        self._db_exec(
            '创建运维授权映射表...',
            'CREATE TABLE `{}ops_map` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_audit_policy(self):
        """ 审计授权策略 """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))

        # rank: 排序，非常重要，影响到策略生效的顺序
        f.append('`rank` int(11) DEFAULT 0')

        # name: 策略名称
        f.append('`name` varchar(128) DEFAULT ""')
        # desc: 策略描述
        f.append('`desc` varchar(255) DEFAULT ""')

        # state: 状态，1=正常，2=禁用
        f.append('`state` int(3) DEFAULT 1')

        # creator_id: 授权者的id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 授权时间
        f.append('`create_time` int(11) DEFAULT 0')

        self._db_exec(
            '创建审计授权策略表...',
            'CREATE TABLE `{}audit_policy` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_audit_auz(self):
        """ 审计授权策略明细 """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))

        # policy_id: 所属的策略
        f.append('`policy_id` int(11) DEFAULT 0')

        # type 指明本条记录是授权还是被授权，0=授权（用户/用户组），1=被授权（资产：用户/用户组/主机/主机组）
        f.append('`type` int(11) DEFAULT 0')

        # rtype : 外链类型
        #  - 1 = 用户
        #  - 2 = 用户组
        #  - 3 = 账号 - 此表中不使用
        #  - 4 = 账号组 - 此表中不使用
        #  - 5 = 主机
        #  - 6 = 主机组
        f.append('`rtype` int(11) DEFAULT 0')
        # sid: 外链的ID
        f.append('`rid` int(11) DEFAULT 0')
        # name: 外链对象的名称
        f.append('`name` varchar(64) DEFAULT ""')
        # state: 状态，1=正常，2=禁用，3=临时锁定
        f.append('`state` int(3) DEFAULT 1')

        # creator_id: 创建者的id，0=系统默认创建
        f.append('`creator_id` int(11) DEFAULT 0')
        # create_time: 创建时间
        f.append('`create_time` int(11) DEFAULT 0')

        self._db_exec(
            '创建审计授权策略明细表...',
            'CREATE TABLE `{}audit_auz` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_audit_map(self):
        """ 审计授权映射（用户->主机一一对应） """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))

        # uni_id: 快速定位的索引 "pid-guid-uid-ghid-hid"
        f.append('`uni_id` varchar(128) NOT NULL')
        # uh_id: 快速定位的索引 "user_id - host-id"
        f.append('`uh_id` varchar(36) NOT NULL')

        # p_id: 授权策略ID
        f.append('`p_id` int(11) DEFAULT 0')
        # p_rank: 授权策略顺序
        f.append('`p_rank` int(11) DEFAULT 0')
        # p_state: 授权策略状态
        f.append('`p_state` int(11) DEFAULT 0')

        # policy_auth_type: 授权方式（0=未知，3=用户:主机，4=用户:主机组，7=用户组:主机，8=用户组:主机组）
        f.append('`policy_auth_type` int(11) DEFAULT 0')

        # u_id: 用户ID
        f.append('`u_id` int(11) DEFAULT 0')
        # u_state: 用户状态
        f.append('`u_state` int(11) DEFAULT 0')
        # gu_id: 用户组ID
        f.append('`gu_id` int(11) DEFAULT 0')
        # gu_state: 用户组状态
        f.append('`gu_state` int(11) DEFAULT 0')

        # h_id: 主机ID
        f.append('`h_id` int(11) DEFAULT 0')
        # gh_id: 主机组ID
        f.append('`gh_id` int(11) DEFAULT 0')

        # 后续字段仅用于显示

        # u_name: 用户登录名
        f.append('`u_name` varchar(32) DEFAULT ""')
        # u_surname: 用户姓名
        f.append('`u_surname` varchar(64) DEFAULT ""')

        # h_name: 主机名称
        f.append('`h_name` varchar(64) DEFAULT ""')
        # ip: IP地址
        f.append('`ip` varchar(40) NOT NULL')
        # router_ip: 路由IP
        f.append('`router_ip` varchar(40) DEFAULT ""')
        # router_port: 路由端口
        f.append('`router_port` int(11) DEFAULT 0')

        self._db_exec(
            '创建审计授权映射表...',
            'CREATE TABLE `{}audit_map` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_syslog(self):
        """ 系统日志（用户登录、授权等等WEB上的操作） """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))

        # user_name: 用户名
        f.append('`user_name` varchar(32) DEFAULT ""')
        # user_surname: 用户真实姓名
        f.append('`user_surname` varchar(64) DEFAULT ""')

        # client_ip: 操作发起的IP地址
        f.append('`client_ip` varchar(40) DEFAULT ""')
        # code: 操作结果（成功还是失败 TPE_XXXX）
        f.append('`code` int(11) DEFAULT 0')
        # time: 日志发生时间
        f.append('`log_time` int(11) DEFAULT 0')
        # message: 说明
        f.append('`message` varchar(255) DEFAULT ""')
        # detail: 详细描述
        f.append('`detail` TEXT')

        self._db_exec(
            '创建系统日志表...',
            'CREATE TABLE `{}syslog` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_record(self):
        """ 运维录像日志 """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))

        # core_uuid:
        f.append('`core_sn` varchar(5) DEFAULT "0000"')

        # flag: 是否已审查/是否要永久保留，异或方式设置，0=初始，1=已审查，2=要永久保留
        f.append('`flag` int(11) DEFAULT 0')

        # reason: 本次运维的原因
        f.append('`reason` varchar(255) DEFAULT ""')

        # sid: 会话ID
        f.append('`sid` varchar(32) DEFAULT ""')

        # 下列三个ID主要用于在线会话管理（强行终止会话）
        # user_id: 操作的用户
        f.append('`user_id` int(11) DEFAULT 0')
        # host_id: 对应的主机
        f.append('`host_id` int(11) DEFAULT 0')
        # acc_id: 对应的远程账号（可能为0，表示在进行远程连接测试）
        f.append('`acc_id` int(11) DEFAULT 0')

        # state: 当前状态（参见 TP_SESS_XXX 系列常量）
        f.append('`state` int(11) DEFAULT 0')

        # user_name: 用户名
        f.append('`user_username` varchar(32) DEFAULT ""')
        # user_surname: 用户姓名
        f.append('`user_surname` varchar(64) DEFAULT ""')

        # host_ip: 目标主机IP
        f.append('`host_ip` varchar(40) DEFAULT ""')
        # conn_ip: 端口转发模式=路由主机IP，直连模式=目标主机IP
        f.append('`conn_ip` varchar(40) DEFAULT ""')
        f.append('`conn_port` int(11) DEFAULT 0')
        # client_ip: 操作发起的IP地址
        f.append('`client_ip` varchar(40) DEFAULT ""')

        # acc_username: 账号（远程主机登录账号名称）
        f.append('`acc_username` varchar(128) DEFAULT ""')

        # auth_type: 远程登录认证方式
        f.append('`auth_type` int(11) DEFAULT 0')
        # protocol_type: 远程连接协议
        f.append('`protocol_type` int(11) DEFAULT 0')
        # protocol_sub_type: 远程连接子协议
        f.append('`protocol_sub_type` int(11) DEFAULT 0')

        # time_begin: 会话开始时间
        f.append('`time_begin` int(11) DEFAULT 0')
        # time_end: 会话结束时间
        f.append('`time_end` int(11) DEFAULT 0')

        self._db_exec(
            '创建运维录像日志表...',
            'CREATE TABLE `{}record` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _create_record_audit(self):
        """ 运维录像日志审计操作及结果 """
        f = list()

        # id: 自增主键
        f.append('`id` integer PRIMARY KEY {}'.format(self.db.auto_increment))
        # record_id: 运维日志ID
        f.append('`record_id` int(11) DEFAULT 0')
        # user_id: 审计者ID
        f.append('`user_id` int(11) DEFAULT 0')
        # user_name: 审计者用户名
        f.append('`user_username` varchar(32) DEFAULT ""')
        # user_surname: 审计者用户姓名
        f.append('`user_surname` varchar(64) DEFAULT ""')
        # ts: 审计时间 timestamp
        f.append('`ts` int(11) DEFAULT 0')
        # ret_code: 审计结果
        f.append('`ret_code` TEXT')
        # ret_desc: 审计结果说明
        f.append('`ret_desc` TEXT')

        self._db_exec(
            '创建运维审计操作表...',
            'CREATE TABLE `{}record_audit` ({});'.format(self.db.table_prefix, ','.join(f))
        )

    def _make_builtin_data(self, sysadmin, email, password):
        _time_now = tp_timestamp_utc_now()

        self._db_exec(
            '设定数据库版本',
            'INSERT INTO `{}config` (`name`, `value`) VALUES ("db_ver", "{}");'.format(self.db.table_prefix, self.db.DB_VERSION)
        )

        self._db_exec(
            '设置本地核心服务',
            'INSERT INTO `{}core_server` (`sn`, `secret`, `ip`, `port`, `state`) VALUES '
            '("0000", "", "127.0.0.1", 52080, 1);'
            ''.format(self.db.table_prefix)
        )

        privilege_admin = TP_PRIVILEGE_ALL
        privilege_ops = TP_PRIVILEGE_LOGIN_WEB | TP_PRIVILEGE_OPS
        privilege_audit = TP_PRIVILEGE_LOGIN_WEB | TP_PRIVILEGE_AUDIT
        self._db_exec(
            '创建默认角色',
            [
                'INSERT INTO `{}role` (`id`, `name`, `privilege`, `creator_id`, `create_time`) VALUES '
                '(1, "{name}", {privilege}, 0, {create_time});'
                ''.format(self.db.table_prefix,
                          name='系统管理员', privilege=privilege_admin, create_time=_time_now),

                'INSERT INTO `{}role` (`id`, `name`, `privilege`, `creator_id`, `create_time`) VALUES '
                '(2, "{name}", {privilege}, 0, {create_time});'
                ''.format(self.db.table_prefix,
                          name='运维人员', privilege=privilege_ops, create_time=_time_now),

                'INSERT INTO `{}role` (`id`, `name`, `privilege`, `creator_id`, `create_time`) VALUES '
                '(3, "{name}", {privilege}, 0, {create_time});'
                ''.format(self.db.table_prefix,
                          name='审计员', privilege=privilege_audit, create_time=_time_now)
            ]
        )

        self._db_exec(
            '创建系统管理员账号',
            'INSERT INTO `{}user` (`type`, `auth_type`, `username`, `surname`, `password`, `role_id`, `state`, `email`, `creator_id`, `create_time`, `last_login`, `last_chpass`) VALUES '
            '(1, {auth_type}, "{username}", "{surname}", "{password}", 1, {state}, "{email}", 0, {create_time}, {last_login}, {last_chpass});'
            ''.format(self.db.table_prefix,
                      auth_type=TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA,
                      username=sysadmin, surname=sysadmin, password=tp_password_generate_secret(password), state=TP_STATE_NORMAL, email=email,
                      create_time=_time_now, last_login=_time_now, last_chpass=_time_now)
        )
