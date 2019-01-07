# -*- coding: utf-8 -*-

from app.base.configs import tp_cfg
from app.base.db import get_db, SQL
from app.base.logger import log
from app.base.utils import tp_timestamp_utc_now, tp_generate_random
from app.const import *
from app.model import syslog
from app.base.stats import tp_stats
from app.logic.auth.password import tp_password_verify, tp_password_generate_secret
from app.logic.auth.oath import tp_oath_verify_code
from app.logic.auth.ldap import Ldap


def get_user_info(user_id):
    """
    获取一个指定的用户的详细信息，包括关联的角色的详细信息、所属组的详细信息等等
    """
    s = SQL(get_db())
    s.select_from('user',
                  ['id', 'type', 'auth_type', 'username', 'surname', 'ldap_dn', 'password', 'oath_secret', 'role_id',
                   'state', 'fail_count', 'lock_time', 'email', 'create_time', 'last_login', 'last_ip', 'last_chpass',
                   'mobile', 'qq', 'wechat', 'desc'], alt_name='u')
    s.left_join('role', ['name', 'privilege'], join_on='r.id=u.role_id', alt_name='r', out_map={'name': 'role'})
    s.where('u.id="{}"'.format(user_id))
    err = s.query()
    if err != TPE_OK:
        return err, {}

    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS, {}

    return TPE_OK, s.recorder[0]


def get_by_username(username):
    s = SQL(get_db())
    s.select_from('user',
                  ['id', 'type', 'auth_type', 'username', 'surname', 'ldap_dn', 'password', 'oath_secret', 'role_id',
                   'state', 'fail_count', 'lock_time', 'email', 'create_time', 'last_login', 'last_ip', 'last_chpass',
                   'mobile', 'qq', 'wechat', 'desc'], alt_name='u')
    s.left_join('role', ['name', 'privilege'], join_on='r.id=u.role_id', alt_name='r', out_map={'name': 'role'})
    s.where('u.username="{}"'.format(username))
    err = s.query()
    if err != TPE_OK:
        return err

    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS, {}

    if s.recorder[0]['privilege'] is None:
        s.recorder[0]['privilege'] = 0

    return TPE_OK, s.recorder[0]


def login(handler, username, password=None, oath_code=None, check_bind_oath=False):
    sys_cfg = tp_cfg().sys

    err, user_info = get_by_username(username)
    if err != TPE_OK:
        # if err == TPE_NOT_EXISTS:
        #     syslog.sys_log({'username': username, 'surname': username}, handler.request.remote_ip, TPE_NOT_EXISTS,
        #                    '用户身份验证失败，用户`{}`不存在'.format(username))
        return err, None

    if user_info.privilege == 0:
        # 尚未为此用户设置角色
        return TPE_PRIVILEGE, None

    if check_bind_oath and len(user_info['oath_secret']) != 0:
        return TPE_OATH_ALREADY_BIND, None

    if user_info['state'] == TP_STATE_LOCKED:
        # 用户已经被锁定，如果系统配置为一定时间后自动解锁，则更新一下用户信息
        if sys_cfg.login.lock_timeout != 0:
            if tp_timestamp_utc_now() - user_info.lock_time > sys_cfg.login.lock_timeout * 60:
                user_info.fail_count = 0
                user_info.state = TP_STATE_NORMAL
        if user_info['state'] == TP_STATE_LOCKED:
            syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_LOCKED, '登录失败，用户已被临时锁定')
            return TPE_USER_LOCKED, None
    elif user_info['state'] == TP_STATE_DISABLED:
        syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_DISABLED, '登录失败，用户已被禁用')
        return TPE_USER_DISABLED, None
    elif user_info['state'] != TP_STATE_NORMAL:
        syslog.sys_log(user_info, handler.request.remote_ip, TPE_FAILED, '登录失败，用户状态异常')
        return TPE_FAILED, None

    err_msg = ''
    if password is not None:
        if user_info['type'] == TP_USER_TYPE_LOCAL:
            # 如果系统配置了密码有效期，则检查用户的密码是否失效
            if sys_cfg.password.timeout != 0:
                _time_now = tp_timestamp_utc_now()
                if user_info['last_chpass'] + (sys_cfg.password.timeout * 60 * 60 * 24) < _time_now:
                    syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_AUTH, '登录失败，用户密码已过期')
                    return TPE_USER_AUTH, None

            if not tp_password_verify(password, user_info['password']):
                err, is_locked = update_fail_count(handler, user_info)
                if is_locked:
                    err_msg = '，用户已被临时锁定'
                syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_AUTH, '登录失败，密码错误{}'.format(err_msg))
                return TPE_USER_AUTH, None
        elif user_info['type'] == TP_USER_TYPE_LDAP:
            try:
                if len(tp_cfg().sys_ldap_password) == 0:
                    syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_AUTH, 'LDAP未能正确配置，需要管理员密码')
                    return TPE_USER_AUTH, None
                else:
                    _ldap_password = tp_cfg().sys_ldap_password
                _ldap_server = tp_cfg().sys.ldap.server
                _ldap_port = tp_cfg().sys.ldap.port
                _ldap_base_dn = tp_cfg().sys.ldap.base_dn
            except:
                syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_AUTH, 'LDAP未能正确配置')
                return TPE_USER_AUTH, None

            try:
                ldap = Ldap(_ldap_server, _ldap_port, _ldap_base_dn)
                ret, err_msg = ldap.valid_user(user_info['ldap_dn'], password)
                if ret != TPE_OK:
                    if ret == TPE_USER_AUTH:
                        err, is_locked = update_fail_count(handler, user_info)
                        if is_locked:
                            err_msg = '，用户已被临时锁定'
                        syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_AUTH,
                                       'LDAP用户登录失败，密码错误{}'.format(err_msg))
                        return TPE_USER_AUTH, None
                    else:
                        syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_AUTH,
                                       'LDAP用户登录失败，{}'.format(err_msg))
                        return TPE_USER_AUTH, None
            except:
                syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_AUTH, 'LDAP用户登录失败，发生内部错误')
                return TPE_USER_AUTH, None

        else:
            syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_AUTH, '登录失败，系统内部错误')
            return TPE_USER_AUTH, None

    if oath_code is not None:
        # use oath
        if len(user_info['oath_secret']) == 0:
            return TPE_OATH_MISMATCH, None

        if not tp_oath_verify_code(user_info['oath_secret'], oath_code):
            err, is_locked = update_fail_count(handler, user_info)
            if is_locked:
                err_msg = '，用户已被临时锁定！'
            syslog.sys_log(user_info, handler.request.remote_ip, TPE_OATH_MISMATCH,
                           "登录失败，身份验证器动态验证码错误{}".format(err_msg))
            return TPE_OATH_MISMATCH, None

    del user_info['password']
    del user_info['oath_secret']

    if len(user_info['surname']) == 0:
        user_info['surname'] = user_info['username']
    return TPE_OK, user_info


def get_users(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude):
    dbtp = get_db().table_prefix
    s = SQL(get_db())
    s.select_from('user', ['id', 'type', 'auth_type', 'username', 'surname', 'role_id', 'state', 'email', 'last_login'],
                  alt_name='u')
    s.left_join('role', ['name', 'privilege'], join_on='r.id=u.role_id', alt_name='r', out_map={'name': 'role'})

    _where = list()

    if len(sql_restrict) > 0:
        for k in sql_restrict:
            if k == 'group_id':
                _sql = 'u.id IN (SELECT mid FROM {dbtp}group_map WHERE type={gtype} AND gid={gid})'
                _where.append(_sql.format(dbtp=dbtp, gtype=TP_GROUP_USER, gid=sql_restrict[k]))
            else:
                log.w('unknown restrict field: {}\n'.format(k))

    if len(sql_exclude) > 0:
        for k in sql_exclude:
            if k == 'group_id':
                _where.append(
                    'u.id NOT IN ('
                    'SELECT mid FROM {dbtp}group_map WHERE type={gtype} AND gid={gid})'
                    ''.format(dbtp=dbtp, gtype=TP_GROUP_USER, gid=sql_exclude[k]))
            elif k == 'ops_policy_id':
                _where.append(
                    'u.id NOT IN (SELECT rid FROM {dbtp}ops_auz WHERE policy_id={pid} AND rtype={rtype})'
                    ''.format(dbtp=dbtp, pid=sql_exclude[k], rtype=TP_USER))
            elif k == 'auditor_policy_id':
                _where.append(
                    'u.id NOT IN ('
                    'SELECT rid FROM {dbtp}audit_auz WHERE policy_id={pid} '
                    'AND `type`={ptype} AND rtype={rtype}'
                    ')'.format(dbtp=dbtp, pid=sql_exclude[k], ptype=TP_POLICY_OPERATOR, rtype=TP_USER))
            elif k == 'auditee_policy_id':
                _where.append(
                    'u.id NOT IN ('
                    'SELECT rid FROM {dbtp}audit_auz WHERE policy_id={pid} '
                    'AND `type`={ptype} AND rtype={rtype}'
                    ')'.format(dbtp=dbtp, pid=sql_exclude[k], ptype=TP_POLICY_ASSET, rtype=TP_USER))
            else:
                log.w('unknown exclude field: {}\n'.format(k))

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'role':
                _where.append('u.role_id={filter}'.format(filter=sql_filter[k]))
            elif k == 'type':
                _where.append('u.type={filter}'.format(filter=sql_filter[k]))
            elif k == 'state':
                _where.append('u.state={filter}'.format(filter=sql_filter[k]))
            elif k == 'search':
                _where.append('('
                              'u.username LIKE "%{filter}%" '
                              'OR u.surname LIKE "%{filter}%" '
                              'OR u.email LIKE "%{filter}%" '
                              'OR u.desc LIKE "%{filter}%"'
                              ')'.format(filter=sql_filter[k]))

    if len(_where) > 0:
        s.where('( {} )'.format(' AND '.join(_where)))

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'username' == sql_order['name']:
            s.order_by('u.username', _sort)
        elif 'surname' == sql_order['name']:
            s.order_by('u.surname', _sort)
        elif 'role_id' == sql_order['name']:
            s.order_by('u.role_id', _sort)
        elif 'state' == sql_order['name']:
            s.order_by('u.state', _sort)
        elif 'type' == sql_order['name']:
            s.order_by('u.type', _sort)
        else:
            log.e('unknown order field: {}\n'.format(sql_order['name']))
            return TPE_PARAM, 0, 0, {}

    if len(sql_limit) > 0:
        s.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = s.query()
    return err, s.total_count, s.page_index, s.recorder


def get_users_by_type(_type):
    s = SQL(get_db())
    err = s.select_from('user', ['id', 'type', 'ldap_dn'], alt_name='u').where('u.type={}'.format(_type)).query()
    if err != TPE_OK:
        return None
    if len(s.recorder) == 0:
        return None
    return s.recorder


def create_users(handler, user_list, success, failed):
    """
    批量创建用户
    """
    db = get_db()
    _time_now = tp_timestamp_utc_now()

    operator = handler.get_current_user()
    name_list = list()

    s = SQL(db)

    for i in range(len(user_list)):
        user = user_list[i]
        if 'type' not in user:
            user['type'] = TP_USER_TYPE_LOCAL
        if 'ldap_dn' not in user:
            user['ldap_dn'] = ''

        err = s.reset().select_from('user', ['id']).where('user.username="{}"'.format(user['username'])).query()
        if err != TPE_OK:
            failed.append({'line': user['_line'], 'error': '数据库查询失败'})
        if len(s.recorder) > 0:
            failed.append({'line': user['_line'], 'error': '账号 `{}` 已经存在'.format(user['username'])})
            continue

        if user['type'] == TP_USER_TYPE_LOCAL:
            _password = tp_password_generate_secret(user['password'])
        else:
            _password = ''

        sql = 'INSERT INTO `{}user` (' \
              '`role_id`, `username`, `surname`, `type`, `ldap_dn`, `auth_type`, `password`, ' \
              '`state`, `email`, `creator_id`, `create_time`, `last_login`, `last_chpass`, `desc`' \
              ') VALUES (' \
              '0, "{username}", "{surname}", {user_type}, "{ldap_dn}", 0, "{password}", ' \
              '{state}, "{email}", {creator_id}, {create_time}, {last_login}, {last_chpass}, "{desc}");' \
              ''.format(db.table_prefix, username=user['username'], surname=user['surname'], user_type=user['type'],
                        ldap_dn=user['ldap_dn'], password=_password, state=TP_STATE_NORMAL, email=user['email'],
                        creator_id=operator['id'], create_time=_time_now, last_login=0, last_chpass=_time_now,
                        desc=user['desc'])
        db_ret = db.exec(sql)
        if not db_ret:
            failed.append({'line': user['_line'], 'error': '写入数据库时发生错误'})
            continue

        success.append(user['username'])
        name_list.append(user['username'])
        user['_id'] = db.last_insert_id()

    if len(name_list) > 0:
        syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "批量导入方式创建用户：{}".format('，'.join(name_list)))
        # tp_stats().user_counter_change(len(name_list))

    # calc count of users.
    err, cnt = s.reset().count('user')
    if err == TPE_OK:
        tp_stats().user_counter_change(cnt)


def create_user(handler, user):
    """
    创建一个用户账号
    """
    db = get_db()
    _time_now = tp_timestamp_utc_now()
    operator = handler.get_current_user()

    if 'type' not in user:
        user['type'] = TP_USER_TYPE_LOCAL
    if 'ldap_dn' not in user:
        user['ldap_dn'] = ''

    # 1. 判断此账号是否已经存在了
    s = SQL(db)
    err = s.reset().select_from('user', ['id']).where('user.username="{}"'.format(user['username'])).query()
    if err != TPE_OK:
        return err, 0
    if len(s.recorder) > 0:
        return TPE_EXISTS, 0

    # _password = tp_password_generate_secret(user['password'])
    if user['type'] == TP_USER_TYPE_LOCAL:
        _password = tp_password_generate_secret(user['password'])
    else:
        _password = ''

    sql = 'INSERT INTO `{}user` (' \
          '`role_id`, `username`, `surname`, `type`, `ldap_dn`, `auth_type`, `password`, `state`, ' \
          '`email`, `creator_id`, `create_time`, `last_login`, `last_chpass`, `desc`' \
          ') VALUES (' \
          '{role}, "{username}", "{surname}", {user_type}, "{ldap_dn}", {auth_type}, "{password}", {state}, ' \
          '"{email}", {creator_id}, {create_time}, {last_login}, {last_chpass}, "{desc}");' \
          ''.format(db.table_prefix, role=user['role'], username=user['username'], surname=user['surname'],
                    user_type=user['type'], ldap_dn=user['ldap_dn'], auth_type=user['auth_type'], password=_password,
                    state=TP_STATE_NORMAL, email=user['email'], creator_id=operator['id'], create_time=_time_now,
                    last_login=0, last_chpass=_time_now, desc=user['desc'])
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, 0

    _id = db.last_insert_id()

    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "创建用户：{}".format(user['username']))

    # calc count of users.
    err, cnt = s.reset().count('user')
    if err == TPE_OK:
        tp_stats().user_counter_change(cnt)

    return TPE_OK, _id


def update_user(handler, args):
    """
    更新一个用户账号
    """
    db = get_db()

    # 1. 判断此账号是否已经存在
    sql = 'SELECT `username` FROM {dbtp}user WHERE `id`={dbph};'.format(dbtp=db.table_prefix, dbph=db.place_holder)
    db_ret = db.query(sql, (args['id'],))
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS

    old_username = db_ret[0][0]
    if old_username != args['username']:
        # 如果要更新用户登录名，则需要判断是否已经存在了
        sql = 'SELECT `id` FROM {dbtp}user WHERE `username`={dbph};'.format(dbtp=db.table_prefix, dbph=db.place_holder)
        db_ret = db.query(sql, (args['username'],))
        if db_ret is not None and len(db_ret) > 0:
            return TPE_EXISTS

    sql = 'UPDATE `{}user` SET ' \
          '`username`="{username}", `surname`="{surname}", `auth_type`={auth_type}, ' \
          '`role_id`={role}, `email`="{email}", `mobile`="{mobile}", `qq`="{qq}", ' \
          '`wechat`="{wechat}", `desc`="{desc}" WHERE `id`={user_id};' \
          ''.format(db.table_prefix,
                    username=args['username'], surname=args['surname'], auth_type=args['auth_type'], role=args['role'],
                    email=args['email'],
                    mobile=args['mobile'], qq=args['qq'], wechat=args['wechat'], desc=args['desc'],
                    user_id=args['id']
                    )
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    # 同步更新授权表和权限映射表
    _uname = args['username']
    if len(args['surname']) > 0:
        _uname += '（' + args['surname'] + '）'
    sql_list = []
    # 运维授权
    sql = 'UPDATE `{}ops_auz` SET `name`="{uname}" WHERE (`rtype`={rtype} AND `rid`={rid});' \
          ''.format(db.table_prefix, uname=_uname, rtype=TP_USER, rid=args['id'])
    sql_list.append(sql)
    sql = 'UPDATE `{}ops_map` SET `u_name`="{uname}", `u_surname`="{surname}" WHERE (u_id={uid});'.format(
        db.table_prefix, uname=args['username'], surname=args['surname'], uid=args['id'])
    sql_list.append(sql)
    # 审计授权
    sql = 'UPDATE `{}audit_auz` SET `name`="{uname}" WHERE (`rtype`={rtype} AND `rid`={rid});' \
          ''.format(db.table_prefix, uname=_uname, rtype=TP_USER, rid=args['id'])
    sql_list.append(sql)
    sql = 'UPDATE `{}audit_map` SET `u_name`="{uname}", `u_surname`="{surname}" WHERE (u_id={uid});'.format(
        db.table_prefix, uname=args['username'], surname=args['surname'], uid=args['id'])
    sql_list.append(sql)

    if not db.transaction(sql_list):
        return TPE_DATABASE

    operator = handler.get_current_user()
    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "更新用户信息：{}".format(args['username']))

    return TPE_OK


def set_role_for_users(handler, users, role_id):
    db = get_db()

    ids = [str(uid) for uid in users]
    where = 'id IN ({})'.format(','.join(ids))

    sql = 'UPDATE `{}user` SET role_id={role_id} WHERE {where};' \
          ''.format(db.table_prefix,
                    role_id=role_id, where=where
                    )
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    return TPE_OK


def set_password(handler, user_id, password):
    db = get_db()

    operator = handler.get_current_user()
    # print('----------', operator)

    # 1. get user info (user name)
    s = SQL(db)
    err = s.reset().select_from('user', ['username', 'surname']).where('user.id={}'.format(user_id)).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    name = s.recorder[0]['username']
    surname = s.recorder[0]['surname']
    if len(surname) == 0:
        surname = name

    sql = 'UPDATE `{}user` SET password="{password}" WHERE id={user_id};' \
          ''.format(db.table_prefix, password=password, user_id=user_id)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    if operator['id'] == 0:
        syslog.sys_log({'username': name, 'surname': surname}, handler.request.remote_ip, TPE_OK,
                       "用户 {} 通过邮件方式重置了密码".format(name))
    else:
        syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "为用户 {} 手动重置了密码".format(name))

    return TPE_OK


def generate_reset_password_token(handler, user_id):
    db = get_db()
    operator = handler.get_current_user()
    s = SQL(db)
    _time_now = tp_timestamp_utc_now()

    # 0. query user's email by user_id
    err = s.select_from('user', ['email'], alt_name='u').where('u.id={user_id}'.format(user_id=user_id)).query()
    if err != TPE_OK:
        return err, None, None
    if len(s.recorder) == 0:
        return TPE_DATABASE, None, None

    email = s.recorder[0].email

    # 1. clean all timed out tokens.
    s.reset().delete_from('user_rpt').where('create_time<{}'.format(_time_now - 24 * 60 * 60)).exec()

    # 2. find out if this user already have a token.
    err = s.reset().select_from('user_rpt', ['id'], alt_name='u').where('u.user_id={}'.format(user_id)).query()
    if err != TPE_OK:
        return err, None, None

    token = tp_generate_random(16)

    if len(s.recorder) == 0:
        sql = 'INSERT INTO `{dbtp}user_rpt` (user_id, token, create_time) VALUES ' \
              '({user_id}, "{token}", {create_time});' \
              ''.format(dbtp=db.table_prefix, user_id=user_id, token=token, create_time=_time_now)
        db_ret = db.exec(sql)
        if not db_ret:
            return TPE_DATABASE, None, None
    else:
        sql = 'UPDATE `{dbtp}user_rpt` SET token="{token}", create_time={create_time} WHERE user_id={user_id};' \
              ''.format(dbtp=db.table_prefix, token=token, create_time=_time_now, user_id=user_id)
        db_ret = db.exec(sql)
        if not db_ret:
            return TPE_DATABASE, None, None

    # syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "为用户 {} 手动重置了密码".format(name))

    return TPE_OK, email, token


def check_reset_token(token):
    db = get_db()
    # s = SQL(db)
    _time_now = tp_timestamp_utc_now()

    # 0. remove expired token (after 3 days)
    sql = 'DELETE FROM `{dbtp}user_rpt` WHERE create_time<{dbph};'.format(dbtp=db.table_prefix, dbph=db.place_holder)
    db.exec(sql, (_time_now - 3 * 24 * 60 * 60,))

    # 1. query user's id
    sql = 'SELECT user_id, create_time FROM `{dbtp}user_rpt` WHERE token={dbph};'.format(dbtp=db.table_prefix,
                                                                                         dbph=db.place_holder)
    db_ret = db.query(sql, (token,))
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS, 0

    user_id = db_ret[0][0]
    create_time = db_ret[0][1]

    if _time_now - create_time > 24 * 60 * 60:
        return TPE_EXPIRED, user_id
    else:
        return TPE_OK, user_id


def remove_reset_token(token):
    db = get_db()
    sql = 'DELETE FROM `{dbtp}user_rpt` WHERE token={dbph};'.format(dbtp=db.table_prefix, dbph=db.place_holder)
    err = db.exec(sql, (token,))
    return TPE_OK if err else TPE_DATABASE


def update_login_info(handler, user_id):
    db = get_db()
    _time_now = tp_timestamp_utc_now()

    sql = 'UPDATE `{}user` SET ' \
          'fail_count=0, last_login=login_time, last_ip=login_ip, login_time={login_time},' \
          ' login_ip="{ip}" WHERE id={user_id};' \
          ''.format(db.table_prefix,
                    login_time=_time_now, ip=handler.request.remote_ip, user_id=user_id
                    )
    if db.exec(sql):
        return TPE_OK
    else:
        return TPE_DATABASE


def update_oath_secret(handler, user_id, oath_secret):
    db = get_db()

    s = SQL(db)
    err = s.select_from('user', ['username', 'surname'], alt_name='u').where(
        'u.id={user_id}'.format(user_id=user_id)).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    username = s.recorder[0].username
    surname = s.recorder[0].surname

    sql = 'UPDATE `{dbtp}user` SET oath_secret="{secret}" WHERE id={user_id}' \
          ''.format(dbtp=db.table_prefix, secret=oath_secret, user_id=user_id)
    if db.exec(sql):
        syslog.sys_log({'username': username, 'surname': surname}, handler.request.remote_ip, TPE_OK,
                       "用户 {} 绑定了身份认证器".format(username))
        return TPE_OK
    else:
        return TPE_DATABASE


def update_users_state(handler, user_ids, state):
    db = get_db()

    user_ids = ','.join([str(i) for i in user_ids])

    sql_list = []

    sql = 'UPDATE `{}user` SET state={state} WHERE id IN ({ids});' \
          ''.format(db.table_prefix, state=state, ids=user_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}ops_auz` SET state={state} WHERE rtype={rtype} AND rid IN ({rid});' \
          ''.format(db.table_prefix, state=state, rtype=TP_USER, rid=user_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}ops_map` SET u_state={state} WHERE u_id IN ({ids});' \
          ''.format(db.table_prefix, state=state, ids=user_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}audit_auz` SET state={state} WHERE rtype={rtype} AND rid IN ({rid});' \
          ''.format(db.table_prefix, state=state, rtype=TP_USER, rid=user_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}audit_map` SET u_state={state} WHERE u_id IN ({ids});' \
          ''.format(db.table_prefix, state=state, ids=user_ids)
    sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


def update_fail_count(handler, user_info):
    db = get_db()
    sys_cfg = tp_cfg().sys
    sql_list = []
    is_locked = False
    fail_count = user_info.fail_count + 1

    sql = 'UPDATE `{}user` SET fail_count={count} WHERE id={uid};' \
          ''.format(db.table_prefix, count=fail_count, uid=user_info.id)
    sql_list.append(sql)

    if sys_cfg.login.retry != 0 and fail_count >= sys_cfg.login.retry:
        is_locked = True
        sql = 'UPDATE `{}user` SET state={state}, lock_time={lock_time} WHERE id={uid};' \
              ''.format(db.table_prefix, state=TP_STATE_LOCKED, lock_time=tp_timestamp_utc_now(), uid=user_info.id)
        sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK, is_locked
    else:
        return TPE_DATABASE, is_locked


def remove_users(handler, users):
    db = get_db()
    s = SQL(db)

    str_users = ','.join([str(i) for i in users])

    # 1. 获取用户名称，用于记录系统日志
    where = 'u.id IN ({})'.format(str_users)
    err = s.select_from('user', ['username'], alt_name='u').where(where).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    str_names = '，'.join([n['username'] for n in s.recorder])

    sql_list = []

    # 将用户从所在组中移除
    sql = 'DELETE FROM `{tpdp}group_map` WHERE type={t} AND mid IN ({ids});' \
          ''.format(tpdp=db.table_prefix, t=TP_GROUP_USER, ids=str_users)
    sql_list.append(sql)
    # 删除用户
    sql = 'DELETE FROM `{tpdp}user` WHERE id IN ({ids});'.format(tpdp=db.table_prefix, ids=str_users)
    sql_list.append(sql)
    # 将用户从运维授权中移除
    sql = 'DELETE FROM `{}ops_auz` WHERE rtype={rtype} AND rid IN ({ids});' \
          ''.format(db.table_prefix, rtype=TP_USER, ids=str_users)
    sql_list.append(sql)
    sql = 'DELETE FROM `{}ops_map` WHERE u_id IN ({ids});'.format(db.table_prefix, ids=str_users)
    sql_list.append(sql)
    # 将用户从审计授权中移除
    sql = 'DELETE FROM `{}audit_auz` WHERE rtype={rtype} AND rid IN ({ids});' \
          ''.format(db.table_prefix, rtype=TP_USER, ids=str_users)
    sql_list.append(sql)
    sql = 'DELETE FROM `{}audit_map` WHERE u_id IN ({ids});'.format(db.table_prefix, ids=str_users)
    sql_list.append(sql)

    if not db.transaction(sql_list):
        return TPE_DATABASE

    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "删除用户：{}".format(str_names))

    # calc count of users.
    err, cnt = s.reset().count('user')
    if err == TPE_OK:
        tp_stats().user_counter_change(cnt)

    return TPE_OK


def get_group_with_member(sql_filter, sql_order, sql_limit):
    """
    获取用户组列表，以及每个组的总成员数以及不超过5个的成员
    """
    # 首先获取要查询的组的信息
    sg = SQL(get_db())
    sg.select_from('group', ['id', 'state', 'name', 'desc'], alt_name='g')

    _where = list()
    _where.append('g.type={}'.format(TP_GROUP_USER))

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'search':
                _where.append('(g.name LIKE "%{filter}%" OR g.desc LIKE "%{filter}%")'.format(filter=sql_filter[k]))
            elif k == 'state':
                _where.append('(g.state={filter})'.format(filter=sql_filter[k]))

    if len(_where) > 0:
        sg.where('( {} )'.format(' AND '.join(_where)))

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'name' == sql_order['name']:
            sg.order_by('g.name', _sort)
        elif 'state' == sql_order['name']:
            sg.order_by('g.state', _sort)
        else:
            log.e('unknown order field.\n')
            return TPE_PARAM, sg.total_count, sg.recorder

    if len(sql_limit) > 0:
        sg.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = sg.query()
    if err != TPE_OK or len(sg.recorder) == 0:
        return err, sg.total_count, sg.recorder

    for g in sg.recorder:
        g['member_count'] = 0
        g['members'] = []
        g['_mid'] = []  # 临时使用，构建此组的前5个成员的id

    # 对于本次要返回的用户组，取其中每一个组内成员的基本信息（id/用户名/真实名称等）
    groups = [g['id'] for g in sg.recorder]
    sgm = SQL(get_db())
    sgm.select_from('group_map', ['gid', 'mid'], alt_name='gm')
    # sgm.limit(0, 5)

    _where = list()
    # _where.append('({})'.format(' OR '.join(['gm.gid={}'.format(gid) for gid in groups])))
    _where.append('gm.type={}'.format(TP_GROUP_USER))
    _where.append('gm.gid IN ({})'.format(','.join([str(gid) for gid in groups])))
    str_where = '( {} )'.format(' AND '.join(_where))
    sgm.where(str_where)
    err = sgm.query()
    if err != TPE_OK or len(sgm.recorder) == 0:
        return err, sg.total_count, sg.recorder

    for g in sg.recorder:
        for gm in sgm.recorder:
            if gm['gid'] == g['id']:
                g['member_count'] += 1
                if len(g['_mid']) < 5:
                    g['_mid'].append(gm['mid'])

    # 将得到的用户id合并到列表中并去重，然后获取这些用户的信息
    users = []
    for g in sg.recorder:
        users.extend(g['_mid'])
    users = list(set(users))

    su = SQL(get_db())
    su.select_from('user', ['id', 'username', 'surname', 'email'], alt_name='u')

    su.where('u.id IN ({})'.format(','.join([str(uid) for uid in users])))
    su.order_by('u.username')
    err = su.query()
    if err != TPE_OK or len(su.recorder) == 0:
        return err, sg.total_count, sg.recorder

    # 现在可以将具体的用户信息追加到组信息中了
    for g in sg.recorder:
        for u in su.recorder:
            for m in g['_mid']:
                if u['id'] == m:
                    g['members'].append(u)

    return err, sg.total_count, sg.recorder


def get_role_list():
    s = SQL(get_db())
    s.select_from('role', ['id', 'name', 'privilege'], alt_name='r')

    err = s.query()
    return err, s.recorder
