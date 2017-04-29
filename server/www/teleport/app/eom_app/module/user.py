# -*- coding: utf-8 -*-

import hashlib

from eom_app.app.configs import app_cfg
from eom_app.app.const import *
from eom_app.app.db import get_db, DbItem
from eom_app.app.util import sec_generate_password, sec_verify_password


def verify_user(name, password):
    cfg = app_cfg()
    db = get_db()

    sql = 'SELECT `account_id`, `account_type`, `account_name`, `account_pwd`, `account_lock` FROM `{}account` WHERE `account_name`="{}";'.format(db.table_prefix, name)
    db_ret = db.query(sql)
    if db_ret is None:
        # 特别地，如果无法取得数据库连接，有可能是新安装的系统，尚未建立数据库，此时应该处于维护模式
        # 因此可以特别地处理用户验证：用户名admin，密码admin可以登录为管理员
        if cfg.app_mode == APP_MODE_MAINTENANCE:
            if name == 'admin' and password == 'admin':
                return 1, 100, 'admin', 0
        return 0, 0, '', 0

    if len(db_ret) != 1:
        return 0, 0, '', 0

    user_id = db_ret[0][0]
    account_type = db_ret[0][1]
    name = db_ret[0][2]
    locked = db_ret[0][4]
    if locked == 1:
        return 0, 0, '', locked

    if not sec_verify_password(password, db_ret[0][3]):
        # 按新方法验证密码失败，可能是旧版本的密码散列格式，再尝试一下
        if db_ret[0][3] != hashlib.sha256(password.encode()).hexdigest():
            return 0, 0, '', locked
        else:
            # 发现此用户的密码散列格式还是旧的，更新成新的吧！
            _new_sec_password = sec_generate_password(password)
            sql = 'UPDATE `{}account` SET `account_pwd`="{}" WHERE `account_id`={}'.format(db.table_prefix, _new_sec_password, int(user_id))
            db.exec(sql)

    return user_id, account_type, name, locked


def modify_pwd(old_pwd, new_pwd, user_id):
    db = get_db()
    sql = 'SELECT `account_pwd` FROM `{}account` WHERE `account_id`={};'.format(db.table_prefix, int(user_id))
    db_ret = db.query(sql)
    if db_ret is None or len(db_ret) != 1:
        return -100

    if not sec_verify_password(old_pwd, db_ret[0][0]):
        # 按新方法验证密码失败，可能是旧版本的密码散列格式，再尝试一下
        if db_ret[0][0] != hashlib.sha256(old_pwd.encode()).hexdigest():
            return -101

    _new_sec_password = sec_generate_password(new_pwd)
    sql = 'UPDATE `{}account` SET `account_pwd`="{}" WHERE `account_id`={}'.format(db.table_prefix, _new_sec_password, int(user_id))
    db_ret = db.exec(sql)
    if db_ret:
        return 0
    else:
        return -102


def get_user_list(with_admin=False):
    db = get_db()
    ret = list()

    field_a = ['account_id', 'account_type', 'account_name', 'account_status', 'account_lock', 'account_desc']

    if with_admin:
        where = ''
    else:
        where = 'WHERE `a`.`account_type`<100'

    sql = 'SELECT {} FROM `{}account` as a {} ORDER BY `account_name`;'.format(','.join(['`a`.`{}`'.format(i) for i in field_a]), db.table_prefix, where)
    db_ret = db.query(sql)
    if db_ret is None:
        return ret

    for item in db_ret:
        x = DbItem()
        x.load(item, ['a_{}'.format(i) for i in field_a])
        h = dict()
        h['user_id'] = x.a_account_id
        h['user_type'] = x.a_account_type
        h['user_name'] = x.a_account_name
        h['user_status'] = x.a_account_status
        h['user_lock'] = x.a_account_lock
        h['user_desc'] = x.a_account_desc
        ret.append(h)
    return ret


def delete_user(user_id):
    db = get_db()
    sql = 'DELETE FROM `{}account` WHERE `account_id`={};'.format(db.table_prefix, int(user_id))
    return db.exec(sql)


def lock_user(user_id, lock_status):
    db = get_db()
    sql = 'UPDATE `{}account` SET `account_lock`={} WHERE `account_id`={};'.format(db.table_prefix, lock_status, int(user_id))
    return db.exec(sql)


def reset_user(user_id):
    db = get_db()
    _new_sec_password = sec_generate_password('123456')
    sql = 'UPDATE `{}account` SET `account_pwd`="{}" WHERE `account_id`={};'.format(db.table_prefix, _new_sec_password, int(user_id))
    return db.exec(sql)


def modify_user(user_id, user_desc):
    db = get_db()
    sql = 'UPDATE `{}account` SET `account_desc`="{}" WHERE `account_id`={};'.format(db.table_prefix, user_desc, int(user_id))
    return db.exec(sql)


def add_user(user_name, user_pwd, user_desc):
    db = get_db()
    sql = 'SELECT `account_id` FROM `{}account` WHERE `account_name`="{}";'.format(db.table_prefix, user_name)
    db_ret = db.query(sql)
    if db_ret is None or len(db_ret) != 0:
        return -100

    sec_password = sec_generate_password(user_pwd)
    sql = 'INSERT INTO `{}account` (`account_type`, `account_name`, `account_pwd`, `account_status`,' \
          '`account_lock`,`account_desc`) VALUES (1,"{}","{}",0,0,"{}")'.format(db.table_prefix, user_name, sec_password, user_desc)
    ret = db.exec(sql)
    if ret:
        return 0
    return -101


def alloc_host(user_name, host_list):
    db = get_db()
    field_a = ['host_id']
    sql = 'SELECT {} FROM `{}auth` AS a WHERE `account_name`="{}";'.format(','.join(['`a`.`{}`'.format(i) for i in field_a]), db.table_prefix, user_name)
    db_ret = db.query(sql)
    ret = dict()
    for item in db_ret:
        x = DbItem()
        x.load(item, ['a_{}'.format(i) for i in field_a])
        host_id = int(x.a_host_id)
        ret[host_id] = host_id

    a_list = list()
    for item in host_list:
        if item in ret:
            pass
        else:
            a_list.append(item)
    try:
        for item in a_list:
            host_id = int(item)
            sql = 'INSERT INTO `{}auth` (`account_name`, `host_id`) VALUES ("{}", {});'.format(db.table_prefix, user_name, host_id)
            ret = db.exec(sql)
            if not ret:
                return False
        return True
    except:
        return False


def alloc_host_user(user_name, host_auth_dict):
    db = get_db()
    field_a = ['host_id', 'host_auth_id']
    sql = 'SELECT {} FROM `{}auth` AS a WHERE `account_name`="{}";'.format(','.join(['`a`.`{}`'.format(i) for i in field_a]), db.table_prefix, user_name)
    db_ret = db.query(sql)
    ret = dict()
    for item in db_ret:
        x = DbItem()
        x.load(item, ['a_{}'.format(i) for i in field_a])
        host_id = int(x.a_host_id)
        host_auth_id = int(x.a_host_auth_id)
        if host_id not in ret:
            ret[host_id] = dict()

        temp = ret[host_id]
        temp[host_auth_id] = host_id
        ret[host_id] = temp

    add_dict = dict()
    for k, v in host_auth_dict.items():
        host_id = int(k)
        auth_id_list = v
        for item in auth_id_list:
            host_auth_id = int(item)
            if host_id not in ret:
                add_dict[host_auth_id] = host_id
                continue
            temp = ret[host_id]
            if host_auth_id not in temp:
                add_dict[host_auth_id] = host_id
                continue

    try:
        for k, v in add_dict.items():
            host_auth_id = int(k)
            host_id = int(v)
            sql = 'INSERT INTO `{}auth` (`account_name`, `host_id`, `host_auth_id`) VALUES ("{}", {}, {});'.format(db.table_prefix, user_name, host_id, host_auth_id)
            ret = db.exec(sql)
            if not ret:
                return False
        return True
    except:
        return False


def delete_host(user_name, host_list):
    db = get_db()
    try:
        for item in host_list:
            host_id = int(item)
            sql = 'DELETE FROM `{}auth` WHERE `account_name`="{}" AND `host_id`={};'.format(db.table_prefix, user_name, host_id)
            ret = db.exec(sql)
            if not ret:
                return False
        return True
    except:
        return False


def delete_host_user(user_name, auth_id_list):
    db = get_db()
    try:
        for item in auth_id_list:
            auth_id = int(item)
            sql = 'DELETE FROM `{}auth` WHERE `account_name`="{}" AND `auth_id`={};'.format(db.table_prefix, user_name, auth_id)
            ret = db.exec(sql)
            if not ret:
                return False
        return True
    except:
        return False


def get_log_list(_filter, limit):
    db = get_db()

    _where = ''

    if len(_filter) > 0:
        _where = 'WHERE ( '

        need_and = False
        for k in _filter:
            if k == 'account_name':
                if need_and:
                    _where += ' AND'
                _where += ' `a`.`account_name`="{}"'.format(_filter[k])
                need_and = True

            if k == 'user_name':
                if need_and:
                    _where += ' AND'
                _where += ' `a`.`account_name`="{}"'.format(_filter[k])
                need_and = True

            elif k == 'search':
                # 查找，限于主机ID和IP地址，前者是数字，只能精确查找，后者可以模糊匹配
                # 因此，先判断搜索项能否转换为数字。

                if need_and:
                    _where += ' AND '

                _where += '('
                _where += '`a`.`host_ip` LIKE "%{}%" )'.format(_filter[k])
                need_and = True
        _where += ')'

    # http://www.jb51.net/article/46015.htm
    field_a = ['id', 'session_id', 'account_name', 'host_ip', 'host_port', 'auth_type', 'sys_type', 'user_name', 'ret_code',
               'begin_time', 'end_time', 'log_time', 'protocol']

    sql = 'SELECT COUNT(*) FROM `{}log` AS a {};'.format(db.table_prefix, _where)

    db_ret = db.query(sql)
    total_count = db_ret[0][0]
    # 修正分页数据
    _limit = ''
    if len(limit) > 0:
        _page_index = limit['page_index']
        _per_page = limit['per_page']
        _limit = 'LIMIT {},{}'.format(_page_index * _per_page, (_page_index + 1) * _per_page)

        if _page_index * _per_page >= total_count:
            _page_index = int(total_count / _per_page)
            _limit = 'LIMIT {},{}'.format(_page_index * _per_page, (_page_index + 1) * _per_page)

    sql = 'SELECT {} FROM `{}log` AS a {} ORDER BY `begin_time` DESC {};'.format(','.join(['a.{}'.format(i) for i in field_a]), db.table_prefix, _where, _limit)
    db_ret = db.query(sql)

    ret = list()
    for item in db_ret:
        x = DbItem()
        x.load(item, ['a_{}'.format(i) for i in field_a])
        h = dict()
        h['id'] = x.a_id
        h['session_id'] = x.a_session_id
        h['account_name'] = x.a_account_name
        h['host_ip'] = x.a_host_ip
        h['host_port'] = x.a_host_port
        h['auth_type'] = x.a_auth_type
        h['sys_type'] = x.a_sys_type
        h['user_name'] = x.a_user_name
        h['ret_code'] = x.a_ret_code
        cost_time = (x.a_end_time - x.a_begin_time)
        if cost_time < 0:
            cost_time = 0
        h['cost_time'] = cost_time
        h['begin_time'] = x.a_begin_time
        if x.a_protocol is not None:
            h['protocol'] = x.a_protocol
        else:
            if x.a_sys_type == 1:
                h['protocol'] = 1
            else:
                h['protocol'] = 2

        ret.append(h)

    return total_count, ret
