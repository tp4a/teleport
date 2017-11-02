# -*- coding: utf-8 -*-

from app.const import *
from app.base.db import get_db, SQL
from app.base.logger import log
from app.base.utils import tp_timestamp_utc_now
from . import syslog


def save_mail_config(_server, _port, _ssl, _sender, _password):
    log.v('save mail config.\n')

    db = get_db()

    sql_list = list()
    sql_list.append('UPDATE `{}config` SET `value`="{}" WHERE `name`="smtp_server";'.format(db.table_prefix, _server))
    sql_list.append('UPDATE `{}config` SET `value`="{}" WHERE `name`="smtp_port";'.format(db.table_prefix, _port))
    sql_list.append('UPDATE `{}config` SET `value`="{}" WHERE `name`="smtp_ssl";'.format(db.table_prefix, _ssl))
    sql_list.append('UPDATE `{}config` SET `value`="{}" WHERE `name`="smtp_sender";'.format(db.table_prefix, _sender))
    sql_list.append('UPDATE `{}config` SET `value`="{}" WHERE `name`="smtp_password";'.format(db.table_prefix, _password))

    ret = db.transaction(sql_list)
    if ret:
        return TPE_OK, ''

    return TPE_FAILED, '数据库操作失败'


def add_role(handler, role_id, role_name, privilege):
    db = get_db()
    _time_now = tp_timestamp_utc_now()
    operator = handler.get_current_user()

    # 1. 判断是否已经存在了
    sql = 'SELECT id FROM {}role WHERE name="{name}";'.format(db.table_prefix, name=role_name)
    db_ret = db.query(sql)
    if db_ret is not None and len(db_ret) > 0:
        return TPE_EXISTS, 0

    sql = 'INSERT INTO `{}role` (name, privilege, creator_id, create_time) VALUES ' \
          '("{name}", {privilege}, {creator_id}, {create_time});' \
          ''.format(db.table_prefix,
                    name=role_name, privilege=privilege, creator_id=operator['id'], create_time=_time_now)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, 0

    _id = db.last_insert_id()

    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "创建角色：{}".format(role_name))

    return TPE_OK, _id


def update_role(handler, role_id, role_name, privilege):
    """
    更新一个远程账号
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

    sql_list = []

    sql = 'DELETE FROM `{}role` WHERE id={};'.format(db.table_prefix, role_id)
    sql_list.append(sql)

    # 更新此角色相关的用户信息
    sql = 'UPDATE `{}user` SET role_id=0 WHERE role_id={rid};'.format(db.table_prefix, rid=role_id)
    sql_list.append(sql)

    if not db.transaction(sql_list):
        return TPE_DATABASE

    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "删除角色：{}".format('，'.join(role_name)))

    return TPE_OK


# def get_config_list():
#     try:
#         from eom_app.module.common import get_db_con
#         from eom_app.module.common import DbItem
#         sql_exec = get_db_con()
#         field_a = ['name', 'value']
#         string_sql = 'SELECT {} FROM ts_config as a ;'.format(','.join(['a.{}'.format(i) for i in field_a]))
#         db_ret = sql_exec.ExecProcQuery(string_sql)
#         h = dict()
#         for item in db_ret:
#             x = DbItem()
#             x.load(item, ['a_{}'.format(i) for i in field_a])
#             h[x.a_name] = x.a_value
#
#         return h
#     except Exception as e:
#         return None
#
#
# def set_config(change_list):
#     from eom_app.module.common import get_db_con
#     sql_exec = get_db_con()
#     #
#     for item in change_list:
#         name = item['name']
#         value = item['value']
#         str_sql = 'UPDATE ts_config SET value = \'{}\' ' \
#                   '  WHERE name = \'{}\''.format(value, name)
#         ret = sql_exec.ExecProcNonQuery(str_sql)
#
#     return ret
#
# def get_config_list():
#     print(cfg.base)
#     return cfg.base
