# -*- coding: utf-8 -*-

from app.base.configs import tp_cfg
from app.controller import auth
from . import account
from . import audit
from . import dashboard
from . import group
from . import host
from . import index
from . import maintenance
from . import ops
from . import rpc
from . import system
from . import user
from . import ws

__all__ = ['controllers', 'fix_controller']

controllers = [
    (r'/', index.IndexHandler),

    # ====================================================
    # 控制台
    # ====================================================
    #  - 控制台页面
    (r'/dashboard', dashboard.IndexHandler),

    # ====================================================
    # 外部调用接口
    # ====================================================
    (r'/rpc', rpc.RpcHandler),

    # ====================================================
    # 登录认证相关
    # ====================================================
    #  - 登录页面
    (r'/auth/login', auth.LoginHandler),
    #  - [json] 执行登录操作
    (r'/auth/do-login', auth.DoLoginHandler),
    #  - 执行登出操作，并跳转到登录页面
    (r'/auth/logout', auth.LogoutHandler),
    #  - [json] 执行登出操作
    (r'/auth/do-logout', auth.DoLogoutHandler),
    #  - [png] 验证码图片
    (r'/auth/captcha', auth.CaptchaHandler),
    #  - [json] 执行验证码验证操作
    (r'/auth/verify-captcha', auth.VerifyCaptchaHandler),

    # ====================================================
    # 用户相关
    # ====================================================
    #  - 个人中心页面
    (r'/user/me', user.MeHandler),
    #  - 用户管理页面
    (r'/user/user', user.UserListHandler),
    #  - [json] 批量导入
    (r'/user/upload-import', user.DoImportHandler),
    #  - [json] 获取指定用户详细信息
    (r'/user/get-user/(.*)', user.DoGetUserInfoHandler),
    #  - [json] 创建/更新用户
    (r'/user/update-user', user.DoUpdateUserHandler),
    #  - [json] 禁用/解禁/删除用户
    (r'/user/update-users', user.DoUpdateUsersHandler),
    #  - [json] 获取用户列表
    (r'/user/get-users', user.DoGetUsersHandler),
    #  - 用户重设密码页面 /auth/reset-password
    (r'/user/reset-password', user.ResetPasswordHandler),
    #  - [json] 重置密码
    (r'/user/do-reset-password', user.DoResetPasswordHandler),
    #  - 用户绑定OATH
    (r'/user/bind-oath', user.BindOathHandler),
    #  - [json] 用户绑定OATH
    (r'/user/gen-oath-secret', user.DoGenerateOathSecretHandler),
    #  - 显示OATH密钥二维码
    (r'/user/oath-secret-qrcode', user.OathSecretQrCodeHandler),
    #  - [json] 获取用户信息
    (r'/user/verify-user', user.DoVerifyUserHandler),
    #  - [json] 绑定身份认证器
    (r'/user/do-bind-oath', user.DoBindOathHandler),
    #  - [json] 取消绑定身份认证器
    (r'/user/do-unbind-oath', user.DoUnBindOathHandler),
    #
    #  - 用户组管理页面
    (r'/user/group', user.GroupListHandler),
    #  - 某个用户组的管理页面
    (r'/user/group/(.*)', user.GroupInfoHandler),
    #  - [json] 获取用户组列表（包括不超过5个组内成员）
    (r'/user/get-groups-with-member', user.DoGetGroupWithMemberHandler),
    #  - [json] 获取角色列表
    (r'/user/get-role-list', user.DoGetRoleListHandler),
    #  - [json] 批量设置角色
    (r'/user/set-role', user.DoSetRoleForUsersHandler),

    # ====================================================
    # 资产相关
    # ====================================================
    #  - 主机及账号管理页面
    (r'/asset/host', host.HostListHandler),
    #  - [json] 批量导入
    (r'/asset/upload-import', host.DoImportHandler),
    #
    #  - 主机分组管理页面
    (r'/asset/host-group', host.HostGroupListHandler),
    #  - 某个主机组的管理页面
    (r'/asset/host-group/(.*)', host.HostGroupInfoHandler),
    #  - [json] 添加/更新主机
    (r'/asset/update-host', host.DoUpdateHostHandler),
    #  - [json] 禁用/解禁/删除主机（可同时操作多个主机）
    (r'/asset/update-hosts', host.DoUpdateHostsHandler),
    #  - [json] 删除主机（可同时删除多个）
    # (r'/asset/remove-hosts', host.DoRemoveHostsHandler),
    #  - [json] 获取主机列表
    (r'/asset/get-hosts', host.DoGetHostsHandler),
    #  - [json] 获取账号组列表（包括不超过5个组内成员）
    (r'/asset/get-host-groups-with-member', host.DoGetHostGroupWithMemberHandler),
    #
    #  - 远程账号分组管理页面
    (r'/asset/account-group', account.AccGroupListHandler),
    #  - 某个账号组的管理页面
    (r'/asset/account-group/(.*)', account.AccGroupInfoHandler),
    #  - [json] 添加/更新 远程账号
    (r'/asset/update-account', account.DoUpdateAccountHandler),
    #  - [json] 禁用/解禁/删除 远程账号
    (r'/asset/update-accounts', account.DoUpdateAccountsHandler),
    #  - [json] 获取账号列表
    (r'/asset/get-accounts', account.DoGetAccountsHandler),
    #  - [json] 获取账号组列表（包括不超过5个组内成员）
    (r'/asset/get-account-groups-with-member', account.DoGetAccountGroupWithMemberHandler),


    # ====================================================
    # 远程运维相关
    # ====================================================
    #  - 运维授权管理页面
    (r'/ops/auz', ops.AuzListHandler),
    #  - 远程运维页面
    (r'/ops/remote', ops.RemoteHandler),
    #  - 在线会话管理页面
    (r'/ops/session', ops.SessionListsHandler),
    #  - 某个策略的管理页面
    (r'/ops/policy/detail/(.*)', ops.PolicyDetailHandler),
    #  - [json] 获取策略列表
    (r'/ops/get-policies', ops.DoGetPoliciesHandler),
    #  - [json] 添加/更新策略
    (r'/ops/policy/update', ops.DoUpdatePolicyHandler),
    #  - [json] 禁用/解禁/删除策略
    (r'/ops/policies/update', ops.DoUpdatePoliciesHandler),
    #  - [json] 向指定策略中添加对象（操作者或资产）
    (r'/ops/policy/add-members', ops.DoAddMembersHandler),
    #  - [json] 从指定策略中移除对象（操作者或资产）
    (r'/ops/policy/remove-members', ops.DoRemoveMembersHandler),
    #  - [json] 获取指定策略中的操作者
    (r'/ops/policy/get-operators', ops.DoGetOperatorsHandler),
    #  - [json] 获取指定策略中的被授权资产
    (r'/ops/policy/get-asset', ops.DoGetAssetHandler),
    #  - [json] 调整顺序（rank）
    (r'/ops/policy/rank-reorder', ops.DoRankReorderHandler),
    #  - [json] set policy flags.
    (r'/ops/policy/set-flags', ops.DoSetFlagsHandler),
    #  - [json] 获取会话ID
    (r'/ops/get-session-id', ops.DoGetSessionIDHandler),
    #  - [json] 获取被授权的主机（及账号）
    (r'/ops/get-remotes', ops.DoGetRemotesHandler),
    #  - [json] 构建授权映射表
    (r'/ops/build-auz-map', ops.DoBuildAuzMapHandler),
    #  - [json] 强行终止指定会话
    (r'/ops/kill', ops.DoKillSessionsHandler),

    # ====================================================
    # 审计相关
    # ====================================================
    #  - 审计授权管理页面
    (r'/audit/auz', audit.AuzListHandler),
    #  - 审计页面（录像列表）
    (r'/audit/record', audit.RecordHandler),
    #  - [json] 审计页面（录像列表）
    (r'/audit/get-records', audit.DoGetRecordsHandler),
    #  - 某个策略的管理页面
    (r'/audit/policy/detail/(.*)', audit.PolicyDetailHandler),
    #  - [json] 获取策略列表
    (r'/audit/get-policies', audit.DoGetPoliciesHandler),
    #  - [json] 添加/更新策略
    (r'/audit/policy/update', audit.DoUpdatePolicyHandler),
    #  - [json] 禁用/解禁/删除策略
    (r'/audit/policies/update', audit.DoUpdatePoliciesHandler),
    #  - [json] 调整顺序（rank）
    (r'/audit/policy/rank-reorder', audit.DoRankReorderHandler),
    #  - [json] 获取指定策略中的操作者
    (r'/audit/policy/get-auditors', audit.DoGetAuditorsHandler),
    #  - [json] 获取指定策略中的被授权目标
    (r'/audit/policy/get-auditees', audit.DoGetAuditeesHandler),
    #  - [json] 向指定策略中添加对象（操作者或资产）
    (r'/audit/policy/add-members', audit.DoAddMembersHandler),
    #  - [json] 从指定策略中移除对象（操作者或资产）
    (r'/audit/policy/remove-members', audit.DoRemoveMembersHandler),
    #  - [json] 构建授权映射表
    (r'/audit/build-auz-map', audit.DoBuildAuzMapHandler),
    #
    #  - ssh录像回放页面
    (r'/audit/replay/(.*)/(.*)', audit.ReplayHandler),
    #  - ssh命令日志页面
    (r'/audit/command-log/(.*)/(.*)', audit.ComandLogHandler),
    #  - [json] 读取录像头
    (r'/audit/get-record-header', audit.DoGetRecordHeaderHandler),
    #  - [json] 读取录像数据
    (r'/audit/get-record-data', audit.DoGetRecordDataHandler),

    #  - 读取录像文件（用于RDP录像回放）
    (r'/audit/get-file', audit.DoGetFileHandler),

    # (r'/host/export-host', host.ExportHostHandler),
    # (r'/config/export-database', config.ExportDatabaseHandler),
    # (r'/config/import-database', config.ImportDatabaseHandler),

    # ====================================================
    # 分组操作相关
    # ====================================================
    #  - [json] 创建或更新分组
    (r'/group/update', group.DoUpdateGroupHandler),
    #  - [json] 禁用分组
    (r'/group/lock', group.DoLockGroupHandler),
    #  - [json] 解禁分组
    (r'/group/unlock', group.DoUnlockGroupHandler),
    #  - [json] 删除分组
    (r'/group/remove', group.DoRemoveGroupHandler),
    #  - [json] 向指定组里增加成员
    (r'/group/add-members', group.DoAddMembersHandler),
    #  - [json] 从指定组里移除成员
    (r'/group/remove-members', group.DoRemoveMembersHandler),
    #  - [json] 获取指定的组列表
    (r'/group/get-groups', group.DoGetGroupsHandler),

    # ====================================================
    # 系统管理设置相关
    # ====================================================
    #  - 角色管理页面
    (r'/system/role', system.RoleHandler),
    #  - [json] 创建/更新 角色
    (r'/system/role-update', system.DoRoleUpdateHandler),
    #  - [json] 删除 角色
    (r'/system/role-remove', system.DoRoleRemoveHandler),
    #  - 系统日志页面
    (r'/system/syslog', system.SysLogHandler),
    #  - [json] 获取系统日志列表
    (r'/system/get-logs', system.DoGetLogsHandler),
    #  - 系统配置页面
    (r'/system/config', system.ConfigHandler),
    #  - [json] 系统配置-保存配置
    (r'/system/save-cfg', system.DoSaveCfgHandler),
    #  - [json] 系统配置-发送测试邮件
    (r'/system/send-test-mail', system.DoSendTestMailHandler),
    #  - [json] 系统配置-清理存储空间
    (r'/system/cleanup-storage', system.DoCleanupStorageHandler),
    #  - [json] 列出LDAP服务器的用户的属性，便于管理员做属性映射
    (r'/system/do-ldap-config-list-attr', system.DoLdapListUserAttrHandler),
    #  - [json] 测试LDAP的配置
    (r'/system/do-ldap-config-test', system.DoLdapConfigTestHandler),
    #  - [json] 获取LDAP用户列表
    (r'/system/do-ldap-get-users', system.DoLdapGetUsersHandler),
    #  - [json] 导入LDAP用户
    (r'/system/do-ldap-import', system.DoLdapImportHandler),

    #
    #  - [json] 获取服务器时间
    (r'/system/get-time', system.DoGetTimeHandler),
    #  - [json] 重建授权映射
    (r'/system/rebuild-ops-auz-map', system.DoRebuildOpsAuzMapHandler),
    (r'/system/rebuild-audit-auz-map', system.DoRebuildAuditAuzMapHandler),

    # ====================================================
    # 安装维护相关
    # ====================================================
    #  - 初始安装设置（新安装，未创建数据库时自动跳转到此页面）
    (r'/maintenance/install', maintenance.InstallHandler),
    #  - 升级（数据库版本发生变化时跳转到此页面）
    # (r'/maintenance/upgrade', maintenance.UpgradeHandler),
    #  - [json] 维护过程中页面与后台的通讯接口
    (r'/maintenance/rpc', maintenance.RpcHandler),

    # WebSocket for real-time information
    # ws-client call 'http://ip:7190/ws/action/'
    (r'/ws/(.*)', ws.WebSocketHandler),

    (r'/.*', index.CatchAllHandler),
]


def fix_controller():
    dbg_mode, _ = tp_cfg().get_bool('common::debug-mode', False)
    if dbg_mode:
        controllers.append((r'/exit/9E37CBAEE2294D9D9965112025CEE87F', index.ExitHandler))
