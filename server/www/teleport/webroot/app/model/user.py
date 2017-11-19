# -*- coding: utf-8 -*-

# import hashlib

from app.base.configs import get_cfg
from app.base.db import get_db, SQL
from app.base.logger import log
from app.base.utils import tp_timestamp_utc_now, tp_generate_random
from app.const import *
from app.model import syslog
from app.logic.auth.password import tp_password_verify
from app.logic.auth.oath import tp_oath_verify_code


def get_user_info(user_id):
    """
    获取一个指定的用户的详细信息，包括关联的角色的详细信息、所属组的详细信息等等
    """
    s = SQL(get_db())
    s.select_from('user', ['id', 'type', 'auth_type', 'username', 'surname', 'password', 'oath_secret', 'role_id', 'state', 'email', 'create_time', 'last_login', 'last_ip', 'last_chpass', 'mobile', 'qq', 'wechat', 'desc'], alt_name='u')
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
    s.select_from('user', ['id', 'type', 'auth_type', 'username', 'surname', 'password', 'oath_secret', 'role_id', 'state', 'fail_count', 'lock_time', 'email', 'create_time', 'last_login', 'last_ip', 'last_chpass', 'mobile', 'qq', 'wechat', 'desc'], alt_name='u')
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


def login(handler, username, password=None, oath_code=None):
    sys_cfg = get_cfg().sys

    err, user_info = get_by_username(username)
    if err != TPE_OK:
        # if err == TPE_NOT_EXISTS:
        #     syslog.sys_log({'username': username, 'surname': username}, handler.request.remote_ip, TPE_NOT_EXISTS, '用户身份验证失败，用户`{}`不存在'.format(username))
        return err, None

    print(user_info)

    if user_info.privilege == 0:
        # 尚未为此用户设置角色
        return TPE_PRIVILEGE, None

    if user_info['state'] == TP_STATE_LOCKED:
        # 用户已经被锁定，如果系统配置为一定时间后自动解锁，则更新一下用户信息
        if sys_cfg.login.lock_timeout != 0:
            if tp_timestamp_utc_now() - user_info.lock_time > sys_cfg.login.lock_timeout * 60:
                user_info.fail_count = 0
                user_info.state = TP_STATE_NORMAL
        if user_info['state'] == TP_STATE_LOCKED:
            syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_LOCKED, '用户已被临时锁定')
            return TPE_USER_LOCKED, None
    elif user_info['state'] == TP_STATE_DISABLED:
        syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_DISABLED, '用户已被禁用')
        return TPE_USER_DISABLED, None
    elif user_info['state'] != TP_STATE_NORMAL:
        syslog.sys_log(user_info, handler.request.remote_ip, TPE_FAILED, '用户身份验证失败，系统内部错误')
        return TPE_FAILED, None

    err_msg = ''
    if password is not None:
        # 如果系统配置了密码有效期，则检查用户的密码是否失效
        if sys_cfg.password.timeout != 0:
            pass

        if not tp_password_verify(password, user_info['password']):
            err, is_locked = update_fail_count(handler, user_info)
            if is_locked:
                err_msg = '用户被临时锁定！'
            syslog.sys_log(user_info, handler.request.remote_ip, TPE_USER_AUTH, '登录失败，密码错误！{}'.format(err_msg))
            return TPE_USER_AUTH, None

    if oath_code is not None:
        # use oath
        if len(user_info['oath_secret']) == 0:
            return TPE_OATH_MISMATCH, None

        if not tp_oath_verify_code(user_info['oath_secret'], oath_code):
            err, is_locked = update_fail_count(handler, user_info)
            if is_locked:
                err_msg = '用户被临时锁定！'
            syslog.sys_log(user_info, handler.request.remote_ip, TPE_OATH_MISMATCH, "登录失败，身份验证器动态验证码错误！{}".format(err_msg))
            return TPE_OATH_MISMATCH, None

    del user_info['password']
    del user_info['oath_secret']
    return TPE_OK, user_info


def get_users(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude):
    dbtp = get_db().table_prefix
    s = SQL(get_db())
    s.select_from('user', ['id', 'type', 'auth_type', 'username', 'surname', 'role_id', 'state', 'email', 'last_login'], alt_name='u')
    s.left_join('role', ['name', 'privilege'], join_on='r.id=u.role_id', alt_name='r', out_map={'name': 'role'})

    _where = list()

    if len(sql_restrict) > 0:
        for k in sql_restrict:
            if k == 'group_id':
                _where.append('u.id IN (SELECT mid FROM {dbtp}group_map WHERE type={gtype} AND gid={gid})'.format(dbtp=dbtp, gtype=TP_GROUP_USER, gid=sql_restrict[k]))
            else:
                log.w('unknown restrict field: {}\n'.format(k))

    if len(sql_exclude) > 0:
        for k in sql_exclude:
            if k == 'group_id':
                _where.append('u.id NOT IN (SELECT mid FROM {dbtp}group_map WHERE type={gtype} AND gid={gid})'.format(dbtp=dbtp, gtype=TP_GROUP_USER, gid=sql_exclude[k]))
            elif k == 'ops_policy_id':
                _where.append('u.id NOT IN (SELECT rid FROM {dbtp}ops_auz WHERE policy_id={pid} AND rtype={rtype})'.format(dbtp=dbtp, pid=sql_exclude[k], rtype=TP_USER))
            else:
                log.w('unknown exclude field: {}\n'.format(k))

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'role':
                _where.append('u.role_id={filter}'.format(filter=sql_filter[k]))
            elif k == 'state':
                _where.append('u.state={filter}'.format(filter=sql_filter[k]))
            elif k == 'search':
                _where.append('(u.username LIKE "%{filter}%" OR u.surname LIKE "%{filter}%" OR u.email LIKE "%{filter}%" OR u.desc LIKE "%{filter}%")'.format(filter=sql_filter[k]))

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
        else:
            log.e('unknown order field: {}\n'.format(sql_order['name']))
            return TPE_PARAM, 0, 0, {}

    if len(sql_limit) > 0:
        s.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = s.query()
    return err, s.total_count, s.page_index, s.recorder


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

        err = s.reset().select_from('user', ['id']).where('user.username="{}"'.format(user['username'])).query()
        if err != TPE_OK:
            failed.append({'line': user['_line'], 'error': '数据库查询失败'})
        if len(s.recorder) > 0:
            failed.append({'line': user['_line'], 'error': '账号 `{}` 已经存在'.format(user['username'])})
            continue

        sql = 'INSERT INTO `{}user` (`type`, `auth_type`, `username`, `surname`, `role_id`, `state`, `email`, `creator_id`, `create_time`, `last_login`, `last_chpass`, `desc`) VALUES ' \
              '(1, 0, "{username}", "{surname}", 0, {state}, "{email}", {creator_id}, {create_time}, {last_login}, {last_chpass}, "{desc}");' \
              ''.format(db.table_prefix,
                        username=user['username'], surname=user['surname'], state=TP_STATE_NORMAL, email=user['email'],
                        creator_id=operator['id'], create_time=_time_now, last_login=0, last_chpass=0, desc=user['desc'])
        db_ret = db.exec(sql)
        if not db_ret:
            failed.append({'line': user['_line'], 'error': '写入数据库时发生错误'})
            continue

        success.append(user['username'])
        name_list.append(user['username'])
        user['_id'] = db.last_insert_id()

    if len(name_list) > 0:
        syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "创建用户：{}".format('，'.join(name_list)))


def create_user(handler, args):
    """
    创建一个用户账号
    """
    db = get_db()
    _time_now = tp_timestamp_utc_now()
    operator = handler.get_current_user()

    # 1. 判断此账号是否已经存在了
    s = SQL(db)
    err = s.reset().select_from('user', ['id']).where('user.username="{}"'.format(args['username'])).query()
    if err != TPE_OK:
        return err, 0
    if len(s.recorder) > 0:
        return TPE_EXISTS, 0

    # sql = 'SELECT id FROM {}user WHERE account="{}";'.format(db.table_prefix, args['account'])
    # db_ret = db.query(sql)
    # if db_ret is not None and len(db_ret) > 0:
    #     return TPE_EXISTS, 0

    sql = 'INSERT INTO `{}user` (`type`, `auth_type`, `username`, `surname`, `role_id`, `state`, `email`, `creator_id`, `create_time`, `last_login`, `last_chpass`, `desc`) VALUES ' \
          '(1, {auth_type}, "{username}", "{surname}", {role}, {state}, "{email}", {creator_id}, {create_time}, {last_login}, {last_chpass}, "{desc}");' \
          ''.format(db.table_prefix, auth_type=args['auth_type'],
                    username=args['username'], surname=args['surname'], role=args['role'], state=TP_STATE_NORMAL, email=args['email'],
                    creator_id=operator['id'],
                    create_time=_time_now, last_login=0, last_chpass=0, desc=args['desc'])
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, 0

    _id = db.last_insert_id()

    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "创建用户：{}".format(args['username']))

    return TPE_OK, _id


def update_user(handler, args):
    """
    更新一个用户账号
    """
    db = get_db()

    # 1. 判断此账号是否已经存在
    sql = 'SELECT id FROM {}user WHERE id="{}";'.format(db.table_prefix, args['id'])
    db_ret = db.query(sql)
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS

    sql = 'UPDATE `{}user` SET surname="{surname}", auth_type={auth_type}, role_id={role}, email="{email}", mobile="{mobile}", qq="{qq}", wechat="{wechat}", `desc`="{desc}" WHERE id={user_id};' \
          ''.format(db.table_prefix,
                    surname=args['surname'], auth_type=args['auth_type'], role=args['role'], email=args['email'],
                    mobile=args['mobile'], qq=args['qq'], wechat=args['wechat'], desc=args['desc'],
                    user_id=args['id']
                    )
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

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
    print('----------', operator)

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
        syslog.sys_log({'username': name, 'surname': surname}, handler.request.remote_ip, TPE_OK, "用户 {} 通过邮件方式重置了密码".format(name))
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
    sql = 'DELETE FROM  `{dbtp}user_rpt` WHERE create_time<{dbph};'.format(dbtp=db.table_prefix, dbph=db.place_holder)
    db.query(sql, (_time_now - 3 * 24 * 60 * 60,))

    # 1. query user's id
    sql = 'SELECT user_id, create_time FROM `{dbtp}user_rpt` WHERE token={dbph};'.format(dbtp=db.table_prefix, dbph=db.place_holder)
    db_ret = db.query(sql, (token,))
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS, 0

    user_id = db_ret[0][0]
    create_time = db_ret[0][1]

    # err = s.select_from('user', ['email'], alt_name='u').where('u.id="{user_id}"'.format(user_id=user_id)).query()
    # if err != TPE_OK:
    #     return err
    # if len(s.recorder) == 0:
    #     return TPE_DATABASE
    # email = s.recorder[0].email

    if _time_now - create_time > 24 * 60 * 60:
        return TPE_EXPIRED, user_id
    else:
        return TPE_OK, user_id


def update_login_info(handler, user_id):
    db = get_db()
    _time_now = tp_timestamp_utc_now()

    sql = 'UPDATE `{}user` SET fail_count=0, last_login=login_time, last_ip=login_ip, login_time={login_time}, login_ip="{ip}" WHERE id={user_id};' \
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
    err = s.select_from('user', ['username', 'surname'], alt_name='u').where('u.id={user_id}'.format(user_id=user_id)).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    username = s.recorder[0].username
    surname = s.recorder[0].surname

    sql = 'UPDATE `{dbtp}user` SET oath_secret="{secret}" WHERE id={user_id}'.format(dbtp=db.table_prefix, secret=oath_secret, user_id=user_id)
    if db.exec(sql):
        syslog.sys_log({'username': username, 'surname': surname}, handler.request.remote_ip, TPE_OK, "用户 {} 绑定了身份认证器".format(username))
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

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


def update_fail_count(handler, user_info):
    db = get_db()
    sys_cfg = get_cfg().sys
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
    s = SQL(get_db())

    user_list = [str(i) for i in users]

    # 1. 获取用户名称，用于记录系统日志
    where = 'u.id IN ({})'.format(','.join(user_list))
    err = s.select_from('user', ['username'], alt_name='u').where(where).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    name_list = [n['username'] for n in s.recorder]

    # 将用户从所在组中移除
    where = 'type={} AND mid IN ({})'.format(TP_GROUP_USER, ','.join(user_list))
    err = s.reset().delete_from('group_map').where(where).exec()
    if err != TPE_OK:
        return err

    # sql = 'DELETE FROM `{}group_map` WHERE (type=1 AND ({}));'.format(db.table_prefix, where)
    # if not db.exec(sql):
    #     return TPE_DATABASE

    where = 'id IN ({})'.format(','.join(user_list))
    err = s.reset().delete_from('user').where(where).exec()
    if err != TPE_OK:
        return err
    # sql = 'DELETE FROM `{}user` WHERE {};'.format(db.table_prefix, where)
    # if not db.exec(sql):
    #     return TPE_DATABASE

    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "删除用户：{}".format('，'.join(name_list)))

    return TPE_OK


# def verify_oath(user_id, oath_code):
#     db = get_db()
#
#     sql = 'SELECT `oath_secret` FROM `{}account` WHERE `account_id`={};'.format(db.table_prefix, user_id)
#     db_ret = db.query(sql)
#     if db_ret is None:
#         return False
#
#     if len(db_ret) != 1:
#         return False
#
#     oath_secret = str(db_ret[0][0]).strip()
#     if 0 == len(oath_secret):
#         return False
#
#     return tp_oath_verify_code(oath_secret, oath_code)

#
# def modify_pwd(old_pwd, new_pwd, user_id):
#     db = get_db()
#     sql = 'SELECT `account_pwd` FROM `{}account` WHERE `account_id`={};'.format(db.table_prefix, int(user_id))
#     db_ret = db.query(sql)
#     if db_ret is None or len(db_ret) != 1:
#         return -100
#
#     if not tp_password_verify(old_pwd, db_ret[0][0]):
#         # 按新方法验证密码失败，可能是旧版本的密码散列格式，再尝试一下
#         if db_ret[0][0] != hashlib.sha256(old_pwd.encode()).hexdigest():
#             return -101
#
#     _new_sec_password = tp_password_generate_secret(new_pwd)
#     sql = 'UPDATE `{}account` SET `account_pwd`="{}" WHERE `account_id`={}'.format(db.table_prefix, _new_sec_password, int(user_id))
#     db_ret = db.exec(sql)
#     if db_ret:
#         return 0
#     else:
#         return -102
#
#
# def get_user_list(with_admin=False):
#     db = get_db()
#     ret = list()
#
#     field_a = ['account_id', 'account_type', 'account_name', 'account_status', 'account_lock', 'account_desc']
#
#     if with_admin:
#         where = ''
#     else:
#         where = 'WHERE `a`.`account_type`<100'
#
#     sql = 'SELECT {} FROM `{}account` as a {} ORDER BY `account_name`;'.format(','.join(['`a`.`{}`'.format(i) for i in field_a]), db.table_prefix, where)
#     db_ret = db.query(sql)
#     if db_ret is None:
#         return ret
#
#     for item in db_ret:
#         x = DbItem()
#         x.load(item, ['a_{}'.format(i) for i in field_a])
#         h = dict()
#         h['user_id'] = x.a_account_id
#         h['user_type'] = x.a_account_type
#         h['user_name'] = x.a_account_name
#         h['user_status'] = x.a_account_status
#         h['user_lock'] = x.a_account_lock
#         h['user_desc'] = x.a_account_desc
#         ret.append(h)
#     return ret

#
# def delete_user(user_id):
#     db = get_db()
#     sql = 'DELETE FROM `{}account` WHERE `account_id`={};'.format(db.table_prefix, int(user_id))
#     return db.exec(sql)
#
#
# def lock_user(user_id, lock_status):
#     db = get_db()
#     sql = 'UPDATE `{}account` SET `account_lock`={} WHERE `account_id`={};'.format(db.table_prefix, lock_status, int(user_id))
#     return db.exec(sql)
#
#
# def reset_user(user_id):
#     db = get_db()
#     _new_sec_password = tp_password_generate_secret('123456')
#     sql = 'UPDATE `{}account` SET `account_pwd`="{}" WHERE `account_id`={};'.format(db.table_prefix, _new_sec_password, int(user_id))
#     return db.exec(sql)
#
#
# def modify_user(user_id, user_desc):
#     db = get_db()
#     sql = 'UPDATE `{}account` SET `account_desc`="{}" WHERE `account_id`={};'.format(db.table_prefix, user_desc, int(user_id))
#     return db.exec(sql)
#
#
# def add_user(user_name, user_pwd, user_desc):
#     db = get_db()
#     sql = 'SELECT `account_id` FROM `{}account` WHERE `account_name`="{}";'.format(db.table_prefix, user_name)
#     db_ret = db.query(sql)
#     if db_ret is None or len(db_ret) != 0:
#         return -100
#
#     sec_password = tp_password_generate_secret(user_pwd)
#     sql = 'INSERT INTO `{}account` (`account_type`, `account_name`, `account_pwd`, `account_status`,' \
#           '`account_lock`,`account_desc`) VALUES (1,"{}","{}",0,0,"{}")'.format(db.table_prefix, user_name, sec_password, user_desc)
#     ret = db.exec(sql)
#     if ret:
#         return 0
#     return -101

#
# def alloc_host(user_name, host_list):
#     db = get_db()
#     field_a = ['host_id']
#     sql = 'SELECT {} FROM `{}auth` AS a WHERE `account_name`="{}";'.format(','.join(['`a`.`{}`'.format(i) for i in field_a]), db.table_prefix, user_name)
#     db_ret = db.query(sql)
#     ret = dict()
#     for item in db_ret:
#         x = DbItem()
#         x.load(item, ['a_{}'.format(i) for i in field_a])
#         host_id = int(x.a_host_id)
#         ret[host_id] = host_id
#
#     a_list = list()
#     for item in host_list:
#         if item in ret:
#             pass
#         else:
#             a_list.append(item)
#     try:
#         for item in a_list:
#             host_id = int(item)
#             sql = 'INSERT INTO `{}auth` (`account_name`, `host_id`) VALUES ("{}", {});'.format(db.table_prefix, user_name, host_id)
#             ret = db.exec(sql)
#             if not ret:
#                 return False
#         return True
#     except:
#         return False

#
# def alloc_host_user(user_name, host_auth_dict):
#     db = get_db()
#     field_a = ['host_id', 'host_auth_id']
#     sql = 'SELECT {} FROM `{}auth` AS a WHERE `account_name`="{}";'.format(','.join(['`a`.`{}`'.format(i) for i in field_a]), db.table_prefix, user_name)
#     db_ret = db.query(sql)
#     ret = dict()
#     for item in db_ret:
#         x = DbItem()
#         x.load(item, ['a_{}'.format(i) for i in field_a])
#         host_id = int(x.a_host_id)
#         host_auth_id = int(x.a_host_auth_id)
#         if host_id not in ret:
#             ret[host_id] = dict()
#
#         temp = ret[host_id]
#         temp[host_auth_id] = host_id
#         ret[host_id] = temp
#
#     add_dict = dict()
#     for k, v in host_auth_dict.items():
#         host_id = int(k)
#         auth_id_list = v
#         for item in auth_id_list:
#             host_auth_id = int(item)
#             if host_id not in ret:
#                 add_dict[host_auth_id] = host_id
#                 continue
#             temp = ret[host_id]
#             if host_auth_id not in temp:
#                 add_dict[host_auth_id] = host_id
#                 continue
#
#     try:
#         for k, v in add_dict.items():
#             host_auth_id = int(k)
#             host_id = int(v)
#             sql = 'INSERT INTO `{}auth` (`account_name`, `host_id`, `host_auth_id`) VALUES ("{}", {}, {});'.format(db.table_prefix, user_name, host_id, host_auth_id)
#             ret = db.exec(sql)
#             if not ret:
#                 return False
#         return True
#     except:
#         return False
#
#
# def delete_host(user_name, host_list):
#     db = get_db()
#     try:
#         for item in host_list:
#             host_id = int(item)
#             sql = 'DELETE FROM `{}auth` WHERE `account_name`="{}" AND `host_id`={};'.format(db.table_prefix, user_name, host_id)
#             ret = db.exec(sql)
#             if not ret:
#                 return False
#         return True
#     except:
#         return False
#
#
# def delete_host_user(user_name, auth_id_list):
#     db = get_db()
#     try:
#         for item in auth_id_list:
#             auth_id = int(item)
#             sql = 'DELETE FROM `{}auth` WHERE `account_name`="{}" AND `auth_id`={};'.format(db.table_prefix, user_name, auth_id)
#             ret = db.exec(sql)
#             if not ret:
#                 return False
#         return True
#     except:
#         return False


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
