# -*- coding: utf-8 -*-

import os
from . import rpc
from . import auth
from . import host
from . import cert
from . import user
from . import pwd
from . import set
from . import group
from . import index
from . import record
from . import maintenance
import tornado.web

from eom_app.app.configs import app_cfg

cfg = app_cfg()

__all__ = ['controllers']

controllers = [
    (r'/', index.IndexHandler),

    # (r'/install/', maintenance.InstallHandler),
    # (r'/install', maintenance.InstallHandler),
    (r'/maintenance/', maintenance.IndexHandler),
    (r'/maintenance', maintenance.IndexHandler),

    (r'/rpc', rpc.RpcHandler),

    (r'/auth/login', auth.LoginHandler),
    (r'/auth/verify-user', auth.VerifyUser),
    (r'/auth/logout', auth.LogoutHandler),
    (r'/auth/get-captcha', auth.GetCaptchaHandler),
    (r'/auth/verify-captcha', auth.VerifyCaptchaHandler),
    (r'/auth/verify-ticket', auth.VerifyTicketHandler),
    (r'/auth/modify-pwd', auth.ModifyPwd),

    (r'/group/list', group.GetListHandler),
    (r'/group/', group.IndexHandler),
    (r'/group', group.IndexHandler),

    (r'/cert/list', cert.GetListHandler),
    (r'/cert/', cert.IndexHandler),
    (r'/cert', cert.IndexHandler),

    (r'/pwd', pwd.IndexHandler),
    (r'/user', user.IndexHandler),
    (r'/user/list', user.GetListHandler),

    # add another path to static-path
    (r"/log/replay/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(cfg.data_path, 'replay')}),
    (r'/log/list', record.LogList),
    (r'/log/record/(.*)/(.*)', record.RecordHandler),
    (r'/log/command-log/(.*)/(.*)', record.ComandLogHandler),
    (r'/log/get-record-header', record.RecordGetHeader),
    (r'/log/get-record-file-info', record.RecordGetInfo),
    (r'/log/delete-log', record.DeleteLog),
    # (r'/log/play-rdp/(.*)/(.*)', record.PlayRdpHandler),
    (r'/log/', record.LogHandler),
    (r'/log', record.LogHandler),

    (r'/exit', auth.LogoutHandler),

    (r'/user/delete-user', user.DeleteUser),
    (r'/user/modify-user', user.ModifyUser),
    (r'/user/add-user', user.AddUser),
    (r'/user/lock-user', user.LockUser),
    (r'/user/reset-user', user.ResetUser),
    (r'/user/host-list', user.HostList),
    (r'/user/alloc-host', user.AllocHost),
    (r'/user/alloc-host-user', user.AllocHostUser),
    (r'/user/delete-host', user.DeleteHost),
    (r'/user/delete-host-user', user.DeleteHostUser),
    (r'/user/auth/(.*)', user.AuthHandler),

    (r'/host/list', host.GetListHandler),
    (r'/host/add-host', host.AddHost),
    (r'/host/lock-host', host.LockHost),
    (r'/host/delete-host', host.DeleteHost),
    (r'/host/export-host', host.ExportHost),
    (r'/host/get-cert-list', host.GetCertList),
    (r'/host/add-cert', host.AddCert),
    (r'/host/delete-cert', host.DeleteCert),
    (r'/host/update-cert', host.UpdateCert),
    (r'/host/get-group-list', host.GetGrouplist),
    (r'/host/add-group', host.AddGroup),
    (r'/host/update-group', host.UpdateGroup),
    (r'/host/delete-group', host.DeleteGroup),
    (r'/host/add-host-to-group', host.AddHostToGroup),
    # (r'/host/get-host-extend-info', host.GetHostExtendInfo),
    # (r'/host/update-host-extend-info', host.UpdateHostExtendInfo),
    (r'/host/update', host.UpdateHandler),
    (r'/host/load-file', host.LoadFile),
    (r'/host/', host.IndexHandler),
    (r'/host', host.IndexHandler),
    (r'/host/get-session-id', host.GetSessionId),
    (r'/host/admin-get-session-id', host.AdminGetSessionId),
    (r'/host/admin-fast-get-session-id', host.AdminFastGetSessionId),

    (r'/host/sys-user/list', host.SysUserList),
    (r'/host/sys-user/add', host.SysUserAdd),
    (r'/host/sys-user/update', host.SysUserUpdate),
    (r'/host/sys-user/delete', host.SysUserDelete),

    (r'/set/update-config', set.UpdateConfig),
    # (r'/set/os-operator', set.OsOperator),
    (r'/set/', set.IndexHandler),
    (r'/set', set.IndexHandler),

    # 通过访问一个特殊URL来停止WEB服务，仅用于开发阶段，生产系统中请删除下一行
    (r'/EXIT-4E581FEFD7AB497D833D71A51C61D898', index.ExitHandler),
]
