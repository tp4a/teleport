# -*- coding: utf-8 -*-

from app.const import *

_sidebar_template = [
    {
        'privilege': TP_PRIVILEGE_LOGIN_WEB,
        'id': 'me'
    },
    {
        'privilege': TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_USER_CREATE,
        'id': 'dashboard',
        'link': '/dashboard',
        'name': '总览',
        'icon': 'fas fa-tachometer-alt',
    },
    {
        'id': 'asset',
        'link': '',
        'name': '资产',
        'icon': 'fa fa-cubes',
        'sub': [
            {
                'privilege': TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_GROUP,
                'id': 'host',
                'link': '/asset/host',
                'name': '主机及账号',
            },
            {
                'privilege': TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_GROUP,
                'id': 'host-group',
                'link': '/asset/host-group',
                'name': '主机分组管理',
            },
            {
                'privilege': TP_PRIVILEGE_ACCOUNT | TP_PRIVILEGE_ACCOUNT_GROUP,
                'id': 'account-group',
                'link': '/asset/account-group',
                'name': '账号分组管理',
            },
        ]
    },
    {
        'id': 'user',
        'link': '',
        'name': '用户',
        'icon': 'far fa-address-book',
        'sub': [
            {
                'privilege': TP_PRIVILEGE_USER_CREATE,
                'id': 'user',
                'link': '/user/user',
                'name': '用户管理',
            },
            {
                'privilege': TP_PRIVILEGE_USER_GROUP,
                'id': 'group',
                'link': '/user/group',
                'name': '用户分组管理',
            },
        ]
    },
    {
        'id': 'ops',
        'link': '',
        'name': '运维',
        'icon': 'fa fa-wrench',
        'sub': [
            {
                'privilege': TP_PRIVILEGE_OPS_AUZ,
                'id': 'auz',
                'link': '/ops/auz',
                'name': '运维授权',
            },
            {
                'privilege': TP_PRIVILEGE_OPS,
                'id': 'remote',
                'link': '/ops/remote',
                'name': '主机运维',
            },
            {
                'privilege': TP_PRIVILEGE_SESSION_VIEW | TP_PRIVILEGE_SESSION_BLOCK,
                'id': 'session',
                'link': '/ops/session',
                'name': '在线会话',
            },
        ]
    },
    {
        'id': 'audit',
        'link': '',
        'name': '审计',
        'icon': 'fa fa-eye',
        'sub': [
            {
                'privilege': TP_PRIVILEGE_AUDIT_AUZ,
                'id': 'auz',
                'link': '/audit/auz',
                'name': '审计授权',
            },
            {
                'privilege': TP_PRIVILEGE_AUDIT,
                'id': 'record',
                'link': '/audit/record',
                'name': '会话审计',
            },
        ]
    },
    {
        'id': 'system',
        'link': '',
        'name': '系统',
        'icon': 'fa fa-cog',
        'sub': [
            {
                'privilege': TP_PRIVILEGE_SYS_LOG,
                'id': 'syslog',
                'link': '/system/syslog',
                'name': '系统日志',
            },
            {
                'privilege': TP_PRIVILEGE_SYS_ROLE,
                'id': 'role',
                'link': '/system/role',
                'name': '角色管理',
            },
            {
                'privilege': TP_PRIVILEGE_SYS_CONFIG,
                'id': 'config',
                'link': '/system/config',
                'name': '系统设置',
            },
        ]
    },
    {
        'privilege': TP_PRIVILEGE_LOGIN_WEB,
        'id': 'assist',
        'link': '/assist/config',
        'target': '_blank',
        'name': '助手设置',
        'icon': 'fas fa-bolt'
    }
]


def tp_generate_sidebar(handler):
    ret = list()
    user = handler.get_current_user()

    for item in _sidebar_template:
        if 'sub' in item:
            tmp_item = {
                'id': item['id'],
                'link': item['link'],
                'name': item['name'],
                'icon': item['icon'],
                'sub': list()
            }
            for sub_item in item['sub']:
                if sub_item['privilege'] & user['privilege'] != 0:
                    tmp_item['sub'].append(sub_item)
            if len(tmp_item['sub']) > 0:
                ret.append(tmp_item)
        else:
            if item['privilege'] & user['privilege'] != 0:
                ret.append(item)

    return ret
