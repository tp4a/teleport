# -*- coding: utf-8 -*-

import json
from app.const import *
from app.base.db import get_db, SQL
from app.base.logger import log
from app.base.utils import tp_timestamp_sec, tp_gen_password
from . import syslog


def save_config(handler, msg, name, value):
    db = get_db()

    str_val = json.dumps(value, separators=(',', ':'))

    sql = 'SELECT name FROM `{dbtp}config` WHERE name="{name}";'.format(dbtp=db.table_prefix, name=name)
    db_ret = db.query(sql)
    if db_ret is not None and len(db_ret) > 0:
        sql = 'UPDATE `{dbtp}config` SET value={dbph} WHERE name="{name}";'.format(dbtp=db.table_prefix, dbph=db.place_holder, name=name)
        db_ret = db.exec(sql, (str_val,))
    else:
        sql = 'INSERT INTO `{dbtp}config` (name, value) VALUES ({dbph}, {dbph});'.format(dbtp=db.table_prefix, dbph=db.place_holder)
        db_ret = db.exec(sql, (name, str_val))

    if not db_ret:
        return TPE_DATABASE

    operator = handler.get_current_user()
    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, msg)

    return TPE_OK


def add_role(handler, role_name, privilege):
    db = get_db()
    _time_now = tp_timestamp_sec()
    operator = handler.get_current_user()

    # 1. 判断是否已经存在了
    sql = 'SELECT id FROM {}role WHERE name="{name}";'.format(db.table_prefix, name=role_name)
    db_ret = db.query(sql)
    if db_ret is not None and len(db_ret) > 0:
        return TPE_EXISTS, 0

    sql = 'INSERT INTO `{}role` (name, privilege, creator_id, create_time) VALUES ' \
          '("{name}", {privilege}, {creator_id}, {create_time});' \
          ''.format(db.table_prefix, name=role_name, privilege=privilege, creator_id=operator['id'], create_time=_time_now)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, 0

    _id = db.last_insert_id()

    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "创建角色：{}".format(role_name))
    return TPE_OK, _id


def update_role(handler, role_id, role_name, privilege):
    """
    更新角色
    """
    db = get_db()

    # 1. 判断是否存在
    sql = 'SELECT id FROM {}role WHERE id={rid};'.format(db.table_prefix, rid=role_id)
    db_ret = db.query(sql)
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS

    sql = 'UPDATE `{}role` SET name="{name}", privilege={p} WHERE id={rid};' \
          ''.format(db.table_prefix, name=role_name, p=privilege, rid=role_id)

    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    operator = handler.get_current_user()
    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "更新角色：{}".format(role_name))
    return TPE_OK


def remove_role(handler, role_id):
    db = get_db()

    s = SQL(db)
    # 1. 判断是否存在
    s.select_from('role', ['name'], alt_name='r')
    s.where('r.id={rid}'.format(rid=role_id))
    err = s.query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    role_name = s.recorder[0].name

    sql_list = list()

    sql = 'DELETE FROM `{tp}role` WHERE `id`={ph};'.format(tp=db.table_prefix, ph=db.place_holder)
    sql_list.append({'s': sql, 'v': (role_id, )})

    # 更新此角色相关的用户信息
    sql = 'UPDATE `{tp}user` SET `role_id`=0 WHERE `role_id`={ph};'.format(tp=db.table_prefix, ph=db.place_holder)
    sql_list.append({'s': sql, 'v': (role_id, )})

    if not db.transaction(sql_list):
        return TPE_DATABASE

    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "删除角色：{}".format(role_name))

    return TPE_OK


def get_integration(with_acc_sec=False):
    s = SQL(get_db())
    fields = ['id', 'acc_key', 'name', 'comment']
    if with_acc_sec:
        fields.append('acc_sec')
    s.select_from('integration_auth', fields, alt_name='ia')
    s.left_join('role', ['id', 'name', 'privilege'], join_on='r.id=ia.role_id', alt_name='r', out_map={'id': 'role_id', 'name': 'role_name'})
    s.order_by('ia.name', True)

    err = s.query()
    return err, s.total_count, s.page_index, s.recorder


def create_integration(handler, role_id, name, comment):
    db = get_db()
    _time_now = tp_timestamp_sec()
    operator = handler.get_current_user()

    # 1. 随机生成一个access-key并判断是否已经存在了
    acc_key = ''
    acc_sec = tp_gen_password(32)
    for i in range(20):
        _acc_key = 'TP{}'.format(tp_gen_password(14))
        sql = 'SELECT `id` FROM {dbtp}integration_auth WHERE `acc_key`="{acc_key}";'.format(dbtp=db.table_prefix, acc_key=_acc_key)
        db_ret = db.query(sql)
        if db_ret is not None and len(db_ret) > 0:
            continue
        acc_key = _acc_key
        break
    if len(acc_key) == 0:
        return TPE_FAILED, None, None

    sql = 'INSERT INTO `{dbtp}integration_auth` (`acc_key`, `acc_sec`, `role_id`, `name`, `comment`, `creator_id`, `create_time`) VALUES ' \
          '("{acc_key}", "{acc_sec}", {role_id}, "{name}", "{comment}", {creator_id}, {create_time});' \
          ''.format(dbtp=db.table_prefix, acc_key=acc_key, acc_sec=acc_sec, role_id=role_id, name=name, comment=comment, creator_id=operator['id'], create_time=_time_now)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, None, None

    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "创建外部密钥 {}".format(name))
    return TPE_OK, acc_key, acc_sec


def update_integration(handler, _id, role_id, name, comment, acc_key, regenerate):
    db = get_db()
    _time_now = tp_timestamp_sec()
    operator = handler.get_current_user()

    acc_sec = None

    # 1. 检查 id, access-key 是否存在
    sql = 'SELECT `id` FROM {dbtp}integration_auth WHERE `id`={ph} AND `acc_key`={ph};'.format(dbtp=db.table_prefix, ph=db.place_holder)
    db_ret = db.query(sql, (_id, acc_key))
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS, None, None

    if regenerate:
        acc_sec = tp_gen_password(32)
        sql = 'UPDATE `{dbtp}integration_auth` SET `name`={ph}, `comment`={ph}, `role_id`={ph}, `acc_sec`={ph} WHERE `id`={ph};' \
              ''.format(dbtp=db.table_prefix, ph=db.place_holder)
        db_ret = db.exec(sql, (name, comment, role_id, acc_sec, _id,))
    else:
        sql = 'UPDATE `{dbtp}integration_auth` SET `name`={ph}, `comment`={ph}, `role_id`={ph} WHERE `id`={ph};' \
              ''.format(dbtp=db.table_prefix, ph=db.place_holder)
        db_ret = db.exec(sql, (name, comment, role_id, _id,))

    if not db_ret:
        return TPE_DATABASE, None, None

    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "更新外部密钥 {}{}".format(name, '，重新生成access-secret。' if regenerate else ''))
    return TPE_OK, acc_key, acc_sec


def remove_integration(handler, items):
    item_ids = ','.join([str(i) for i in items])

    # 1. 获取名称，用于记录系统日志
    where = 'i.id IN ({ids})'.format(ids=item_ids)

    db = get_db()
    s = SQL(db)
    err = s.select_from('integration_auth', ['name'], alt_name='i').where(where).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    name_list = [n['name'] for n in s.recorder]

    # 删除
    sql = 'DELETE FROM `{tp}integration_auth` WHERE `id` IN ({ids});'.format(tp=db.table_prefix, ids=item_ids)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    # 记录系统日志
    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "删除外部集成密钥：{names}".format(names='，'.join(name_list)))

    return TPE_OK

