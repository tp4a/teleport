# -*- coding: utf-8 -*-

TP_LOGIN_AUTH_SYS_DEFAULT = 0    # 系统默认（根据系统配置进行）
TP_LOGIN_AUTH_USERNAME_PASSWORD = 0x0001    # 用户名+密码
TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA = 0x0002    # 用户名+密码+验证码
TP_LOGIN_AUTH_USERNAME_OATH = 0x0004    # 用户名+OATH
TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH = 0x0008    # 用户名+密码+OATH

APP_MODE_NORMAL = 1
APP_MODE_MAINTENANCE = 2

# ==========================================================================
# 用户类型
# ==========================================================================
TP_USER_TYPE_NONE = 0
TP_USER_TYPE_LOCAL = 1
TP_USER_TYPE_LDAP = 2

# ==========================================================================
# 远程主机账号认证方式
# ==========================================================================
TP_AUTH_TYPE_NONE = 0
TP_AUTH_TYPE_PASSWORD = 1
TP_AUTH_TYPE_PRIVATE_KEY = 2

# ==========================================================================
# 远程主机访问协议
# ==========================================================================
TP_PROTOCOL_TYPE_UNKNOWN = 0

TP_PROTOCOL_TYPE_RDP = 1
TP_PROTOCOL_TYPE_SSH = 2
TP_PROTOCOL_TYPE_TELNET = 3

# =======================================================
# 远程连接子协议
# =======================================================
TP_PROTOCOL_TYPE_RDP_DESKTOP = 100
TP_PROTOCOL_TYPE_SSH_SHELL = 200
TP_PROTOCOL_TYPE_SSH_SFTP = 201
TP_PROTOCOL_TYPE_TELNET_SHELL = 300

# ==========================================================================
# 远程主机操作系统类型
# ==========================================================================
TP_OS_TYPE_WINDOWS = 1
TP_OS_TYPE_LINUX = 2

# =======================================================
# 远程连接会话状态
# =======================================================
TP_SESS_STAT_RUNNING = 0  # 会话开始了，尚未结束
TP_SESS_STAT_END = 9999  # 会话成功结束
TP_SESS_STAT_ERR_AUTH_DENIED = 1  # 会话结束，因为认证失败
TP_SESS_STAT_ERR_CONNECT = 2  # 会话结束，因为无法连接到远程主机
TP_SESS_STAT_ERR_BAD_SSH_KEY = 3  # 会话结束，因为无法识别SSH私钥
TP_SESS_STAT_ERR_INTERNAL = 4  # 会话结束，因为内部错误
TP_SESS_STAT_ERR_UNSUPPORT_PROTOCOL = 5  # 会话结束，因为协议不支持(RDP)
TP_SESS_STAT_ERR_BAD_PKG = 6  # 会话结束，因为收到错误的报文
TP_SESS_STAT_ERR_RESET = 7  # 会话结束，因为teleport核心服务重置了
TP_SESS_STAT_ERR_IO = 8  # 会话结束，因为网络中断
TP_SESS_STAT_ERR_SESSION = 9  # 会话结束，因为无效的会话ID
TP_SESS_STAT_STARTED = 100  # 已经连接成功了，开始记录录像了
TP_SESS_STAT_ERR_START_INTERNAL = 104  # 会话结束，因为内部错误
TP_SESS_STAT_ERR_START_BAD_PKG = 106  # 会话结束，因为收到错误的报文
TP_SESS_STAT_ERR_START_RESET = 107  # 会话结束，因为teleport核心服务重置了
TP_SESS_STAT_ERR_START_IO = 108  # 会话结束，因为网络中断

# ==========================================================================
# 分组类型
# ==========================================================================
TP_USER = 1
TP_GROUP_USER = 2
TP_ACCOUNT = 3
TP_GROUP_ACCOUNT = 4
TP_HOST = 5
TP_GROUP_HOST = 6

# =======================================================
# 对象状态（用户/用户组/主机/主机组/账号/账号组/运维授权策略/审计授权策略/...）
# =======================================================
TP_STATE_NORMAL = 1  # 正常
TP_STATE_DISABLED = 2  # 禁用
TP_STATE_LOCKED = 3  # 临时禁用（用于用户登录连续错误n次）

TP_GROUP_TYPES = {
    TP_GROUP_USER: '用户组',
    TP_GROUP_HOST: '主机组',
    TP_GROUP_ACCOUNT: '账号组'
}

# =======================================================
# 授权策略对象
# =======================================================
TP_POLICY_OPERATOR = 0  # 授权（操作者：用户/用户组）
TP_POLICY_ASSET = 1  # 被授权（资产：主机/主机组/账号/账号组）

# =======================================================
# 授权策略方式
# =======================================================
TP_POLICY_AUTH_UNKNOWN = 0  # 0=未知
TP_POLICY_AUTH_USER_ACC = 1  # 1=用户:账号
TP_POLICY_AUTH_USER_gACC = 2  # 2=用户:账号组
TP_POLICY_AUTH_USER_HOST = 3  # 3=用户:主机
TP_POLICY_AUTH_USER_gHOST = 4  # 4=用户:主机组
TP_POLICY_AUTH_gUSER_ACC = 5  # 5=用户组:账号
TP_POLICY_AUTH_gUSER_gACC = 6  # 6=用户组:账号组
TP_POLICY_AUTH_gUSER_HOST = 7  # 7=用户组:主机
TP_POLICY_AUTH_gUSER_gHOST = 8  # 8=用户组:主机组
# 下列四个仅用于审计授权
# TP_POLICY_AUTH_USER_USER = 9  # 1=用户:用户
# TP_POLICY_AUTH_USER_gUSER = 10  # 2=用户:用户组
# TP_POLICY_AUTH_gUSER_USER = 11  # 5=用户组:用户
# TP_POLICY_AUTH_gUSER_gUSER = 12  # 6=用户组:用户组


# =======================================================
# 授权标记
# =======================================================
TP_FLAG_ALL = 0xFFFFFFFF
# 会话记录相关
TP_FLAG_RECORD_REPLAY = 0x0001  # 允许记录历史（录像回放）
TP_FLAG_RECORD_REAL_TIME = 0x0002  # 允许实时监控
# RDP相关
TP_FLAG_RDP_DESKTOP = 0x0001  # 0x1=允许远程桌面
TP_FLAG_RDP_CLIPBOARD = 0x0002  # 0x2=允许剪贴板
TP_FLAG_RDP_DISK = 0x0004  # 0x4=允许磁盘映射
TP_FLAG_RDP_APP = 0x0008  # 0x8=允许远程APP（尚未实现）
TP_FLAG_RDP_CONSOLE = 0x1000  # 0x1000=允许连接到管理员会话（RDP的console选项）
# SSH相关
TP_FLAG_SSH_SHELL = 0x0001  # 0x1=允许SHELL
TP_FLAG_SSH_SFTP = 0x0002  # 0x2=允许SFTP
TP_FLAG_SSH_X11 = 0x0004  # 0x4=允许X11转发（尚未实现）
TP_FLAG_SSH_EXEC = 0x0008  # 0x8=允许exec执行远程命令（尚未实现）
TP_FLAG_SSH_TUNNEL = 0x0010  # 0x10=allow ssh tunnel. (not impl.)

# ==========================================================================
# 权限定义（因为权限是可以组合的，所以使用按位或的方式，目前最多能够支持32个权限粒度）
# ==========================================================================
TP_PRIVILEGE_NONE = 0
TP_PRIVILEGE_ALL = 0xFFFFFFFF  # 具有所有权限（仅限系统管理员角色）

TP_PRIVILEGE_LOGIN_WEB = 0x00000001  # 允许登录WEB

TP_PRIVILEGE_USER_CREATE = 0x00000002  # 创建/编辑用户
TP_PRIVILEGE_USER_DELETE = 0x00000004  # 删除用户
TP_PRIVILEGE_USER_LOCK = 0x00000008  # 锁定/解锁用户
TP_PRIVILEGE_USER_GROUP = 0x00000010  # 用户分组管理

TP_PRIVILEGE_ASSET_CREATE = 0x00000020  # 创建/编辑资产
TP_PRIVILEGE_ASSET_DELETE = 0x00000040  # 删除资产
TP_PRIVILEGE_ASSET_LOCK = 0x00000080  # 锁定/解锁资产
TP_PRIVILEGE_ASSET_GROUP = 0x00000100  # 资产分组管理

TP_PRIVILEGE_OPS = 0x00000200  # 远程主机运维
TP_PRIVILEGE_ACCOUNT = 0x00000400  # 远程主机账号管理（增删改查）
TP_PRIVILEGE_ACCOUNT_GROUP = 0x00000800  # 远程主机账号分组管理
TP_PRIVILEGE_OPS_AUZ = 0x00001000  # 远程主机运维授权管理
TP_PRIVILEGE_SESSION_BLOCK = 0x00002000  # 阻断在线会话
TP_PRIVILEGE_SESSION_VIEW = 0x00004000  # 查看在线会话

TP_PRIVILEGE_AUDIT = 0x00008000  # 审计（查看历史会话）
TP_PRIVILEGE_AUDIT_AUZ = 0x00010000  # 审计策略授权管理
# TP_PRIVILEGE_AUDIT_SYSLOG = 0x00020000  # 查看系统日志

TP_PRIVILEGE_SYS_ROLE = 0x00040000  # 角色管理
TP_PRIVILEGE_SYS_CONFIG = 0x00080000  # 系统配置维护
# TP_PRIVILEGE_SYS_OPS_HISTORY = 0x00100000  # 历史会话管理（例如删除历史会话、设定多长时间之前的历史会话自动删除等）
TP_PRIVILEGE_SYS_LOG = 0x00200000  # 查看系统日志

# ===================================================================
# error code
#   see $source-root$/common/teleport/teleport_const.h
# ===================================================================

TPE_OK = 0

TPE_NEED_MORE_DATA = 1

TPE_NEED_LOGIN = 2
TPE_PRIVILEGE = 3

TPE_NOT_IMPLEMENT = 7
TPE_EXISTS = 8
TPE_NOT_EXISTS = 9

TPE_FAILED = 100
TPE_NETWORK = 101
TPE_DATABASE = 102
TPE_EXPIRED = 103

TPE_HTTP_METHOD = 120
TPE_HTTP_URL_ENCODE = 121

TPE_UNKNOWN_CMD = 124
TPE_JSON_FORMAT = 125
TPE_PARAM = 126
TPE_DATA = 127

TPE_OPENFILE = 300

TPE_HTTP_404_NOT_FOUND = 404

TPE_CAPTCHA_EXPIRED = 10000
TPE_CAPTCHA_MISMATCH = 10001
TPE_OATH_MISMATCH = 10002
TPE_SYS_MAINTENANCE = 10003
TPE_OATH_ALREADY_BIND = 10004 

TPE_USER_LOCKED = 10100
TPE_USER_DISABLED = 10101
TPE_USER_AUTH = 10102

TPE_NO_ASSIST = 100000
TPE_OLD_ASSIST = 100001
TPE_START_CLIENT = 100002

TPE_NO_CORE_SERVER = 200000
