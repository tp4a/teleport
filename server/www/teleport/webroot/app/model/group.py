# -*- coding: utf-8 -*-

from app.const import *
from app.base.logger import log
from app.base.db import get_db, SQL
from app.base.utils import tp_timestamp_utc_now
from app.model import syslog
from app.model import policy


def create(handler, gtype, name, desc):
    if gtype not in TP_GROUP_TYPES:
        return TPE_PARAM, 0

    db = get_db()
    _time_now = tp_timestamp_utc_now()

    # 1. 判断是否已经存在了
    sql = 'SELECT id FROM {dbtp}group WHERE type={gtype} AND name="{gname}";'.format(dbtp=db.table_prefix, gtype=gtype, gname=name)
    db_ret = db.query(sql)
    if db_ret is not None and len(db_ret) > 0:
        return TPE_EXISTS, 0

    operator = handler.get_current_user()

    # 2. 插入记录
    sql = 'INSERT INTO `{dbtp}group` (`type`, `name`, `creator_id`, `create_time`, `desc`) VALUES ' \
          '({gtype}, "{gname}", {creator_id}, {create_time}, "{desc}");' \
          ''.format(dbtp=db.table_prefix,
                    gtype=gtype, gname=name, creator_id=operator['id'],
                    create_time=_time_now, desc=desc)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, 0

    _id = db.last_insert_id()

    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "创建{gtype}：{gname}".format(gtype=TP_GROUP_TYPES[gtype], gname=name))

    return TPE_OK, _id


def update_groups_state(handler, gtype, glist, state):
    if gtype not in TP_GROUP_TYPES:
        return TPE_PARAM

    if gtype == TP_GROUP_USER:
        gname = 'gu'
    elif gtype == TP_GROUP_HOST:
        gname = 'gh'
    elif gtype == TP_GROUP_ACCOUNT:
        gname = 'ga'
    else:
        return TPE_PARAM

    group_list = ','.join([str(i) for i in glist])

    db = get_db()
    sql_list = []

    # 2. 更新记录
    sql = 'UPDATE `{}ops_auz` SET state={state} WHERE rtype={rtype} AND rid={rid};' \
          ''.format(db.table_prefix, state=state, rtype=gtype, rid=group_list)
    sql_list.append(sql)

    sql = 'UPDATE `{}ops_map` SET {gname}_state={state} WHERE {gname}_id IN ({gids});' \
          ''.format(db.table_prefix, state=state, gname=gname, gids=group_list)
    sql_list.append(sql)

    sql = 'UPDATE `{dbtp}group` SET state={state} WHERE id IN ({gids});' \
          ''.format(dbtp=db.table_prefix, state=state, gids=group_list)
    sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


def remove(handler, gtype, glist):
    if gtype not in TP_GROUP_TYPES:
        return TPE_PARAM

    group_ids = ','.join([str(i) for i in glist])

    # 1. 获取组的名称，用于记录系统日志
    where = 'g.type={gtype} AND g.id IN ({gids})'.format(gtype=gtype, gids=group_ids)

    db = get_db()
    s = SQL(db)
    err = s.select_from('group', ['name'], alt_name='g').where(where).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    name_list = [n['name'] for n in s.recorder]

    sql_list = []

    # 删除组与成员的映射关系
    sql = 'DELETE FROM `{tpdp}group_map` WHERE `type`={t} AND `gid` IN ({ids});'.format(tpdp=db.table_prefix, t=gtype, ids=group_ids)
    sql_list.append(sql)

    # where = 'type={} AND gid IN ({})'.format(gtype, ','.join(group_list))
    # err = s.reset().delete_from('group_map').where(where).exec()
    # if err != TPE_OK:
    #     return err

    # 删除组
    sql = 'DELETE FROM `{tpdp}group` WHERE `type`={t} AND `id` IN ({ids});'.format(tpdp=db.table_prefix, t=gtype, ids=group_ids)
    sql_list.append(sql)
    # where = 'type={gtype} AND id IN ({gids})'.format(gtype=gtype, gids=','.join(group_list))
    # err = s.reset().delete_from('group').where(where).exec()
    # if err != TPE_OK:
    #     return err

    if gtype == TP_GROUP_USER:
        gname = 'gu'
    elif gtype == TP_GROUP_HOST:
        gname = 'gh'
    elif gtype == TP_GROUP_ACCOUNT:
        gname = 'ga'
    else:
        return TPE_PARAM

    # 将组从运维授权中移除
    sql = 'DELETE FROM `{}ops_auz` WHERE `rtype`={rtype} AND `rid` IN ({ids});'.format(db.table_prefix, rtype=gtype, ids=group_ids)
    sql_list.append(sql)
    sql = 'DELETE FROM `{}ops_map` WHERE `{gname}_id` IN ({ids});'.format(db.table_prefix, gname=gname, ids=group_ids)
    sql_list.append(sql)
    # 将组从审计授权中移除
    sql = 'DELETE FROM `{}audit_auz` WHERE `rtype`={rtype} AND `rid` IN ({ids});'.format(db.table_prefix, rtype=gtype, ids=group_ids)
    sql_list.append(sql)
    # 注意，审计授权映射表中，没有远程账号相关信息，所以如果是远程账号组，则忽略
    if gtype != TP_GROUP_ACCOUNT:
        sql = 'DELETE FROM `{}audit_map` WHERE `{gname}_id` IN ({ids});'.format(db.table_prefix, gname=gname, ids=group_ids)
        sql_list.append(sql)

    if not db.transaction(sql_list):
        return TPE_DATABASE

    # 记录系统日志
    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "删除{gtype}：{gname}".format(gtype=TP_GROUP_TYPES[gtype], gname='，'.join(name_list)))

    return TPE_OK


def get_by_id(gtype, gid):
    # 获取要查询的组的信息
    s = SQL(get_db())
    s.select_from('group', ['id', 'state', 'name', 'desc'], alt_name='g')
    s.where('g.type={} AND g.id={}'.format(gtype, gid))
    err = s.query()
    if err != TPE_OK:
        return err, {}
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS, {}
    return TPE_OK, s.recorder[0]


def get_list(gtype):
    s = SQL(get_db())
    s.select_from('group', ['id', 'name'], alt_name='g')
    s.where('g.type={}'.format(gtype))

    err = s.query()
    return err, s.recorder


def update(handler, gid, name, desc):
    db = get_db()

    # 1. 判断是否已经存在
    sql = 'SELECT `id`, `type` FROM `{}group` WHERE `id`={};'.format(db.table_prefix, gid)
    db_ret = db.query(sql)
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS

    gtype = db_ret[0][1]
    sql_list = []

    # 2. 更新记录
    sql = 'UPDATE `{}group` SET `name`="{name}", `desc`="{desc}" WHERE id={gid};' \
          ''.format(db.table_prefix, name=name, desc=desc, gid=gid)
    sql_list.append(sql)

    # 3. 同步更新授权表和权限映射表
    # 运维授权
    sql = 'UPDATE `{}ops_auz` SET `name`="{name}" WHERE (`rtype`={rtype} AND `rid`={rid});'.format(db.table_prefix, name=name, rtype=gtype, rid=gid)
    sql_list.append(sql)
    # 审计授权
    sql = 'UPDATE `{}audit_auz` SET `name`="{name}" WHERE (`rtype`={rtype} AND `rid`={rid});'.format(db.table_prefix, name=name, rtype=gtype, rid=gid)
    sql_list.append(sql)

    if not db.transaction(sql_list):
        return TPE_DATABASE

    return TPE_OK


def add_members(gtype, gid, members):
    # 向指定组中增加成员，同时根据授权策略，更新授权映射表
    db = get_db()

    sql = []
    for uid in members:
        sql.append('INSERT INTO `{}group_map` (`type`, `gid`, `mid`) VALUES ({}, {}, {});'.format(db.table_prefix, gtype, gid, uid))
    if db.transaction(sql):
        return policy.rebuild_auz_map()
    else:
        return TPE_DATABASE


def remove_members(gtype, gid, members):
    db = get_db()

    if gtype == TP_GROUP_USER:
        name = 'u'
        gname = 'gu'
    elif gtype == TP_GROUP_HOST:
        name = 'h'
        gname = 'gh'
    elif gtype == TP_GROUP_ACCOUNT:
        name = 'a'
        gname = 'ga'
    else:
        return TPE_PARAM

    mids = ','.join([str(uid) for uid in members])

    sql_list = []

    _where = 'WHERE (type={gtype} AND gid={gid} AND mid IN ({mid}))'.format(gtype=gtype, gid=gid, mid=mids)
    sql = 'DELETE FROM `{dbtp}group_map` {where};'.format(dbtp=db.table_prefix, where=_where)
    sql_list.append(sql)
    sql = 'DELETE FROM `{}ops_map` WHERE {gname}_id={gid} AND {name}_id IN ({ids});'.format(db.table_prefix, gname=gname, name=name, gid=gid, ids=mids)
    sql_list.append(sql)
    if gtype != TP_GROUP_ACCOUNT:
        sql = 'DELETE FROM `{}audit_map` WHERE {gname}_id={gid} AND {name}_id IN ({ids});'.format(db.table_prefix, gname=gname, name=name, gid=gid, ids=mids)
        sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


def make_groups(handler, gtype, glist, failed):
    """
    根据传入的组列表，查询每个组的名称对应的id，如果没有，则创建之
    """
    db = get_db()
    _time_now = tp_timestamp_utc_now()

    operator = handler.get_current_user()
    name_list = list()

    for g in glist:
        sql = 'SELECT id FROM {dbtp}group WHERE type={gtype} AND name="{gname}";'.format(dbtp=db.table_prefix, gtype=gtype, gname=g)
        db_ret = db.query(sql)
        if db_ret is None or len(db_ret) == 0:
            # need create group.
            sql = 'INSERT INTO `{dbtp}group` (`type`, `name`, `creator_id`, `create_time`) VALUES ' \
                  '({gtype}, "{name}", {creator_id}, {create_time});' \
                  ''.format(dbtp=db.table_prefix,
                            gtype=gtype, name=g, creator_id=operator['id'], create_time=_time_now)

            db_ret = db.exec(sql)
            if not db_ret:
                failed.append({'line': 0, 'error': '创建{gtype} `{gname}` 失败，写入数据库时发生错误'.format(gtype=TP_GROUP_TYPES[gtype], gname=g)})
                continue

            glist[g] = db.last_insert_id()
            name_list.append(g)

        else:
            glist[g] = db_ret[0][0]

    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "创建{gtype}：{gname}".format(gtype=TP_GROUP_TYPES[gtype], gname='，'.join(name_list)))
    return TPE_OK


def make_group_map(gtype, gm):
    db = get_db()
    for item in gm:
        # 检查如果不存在，则插入
        sql = 'SELECT id FROM `{dbtp}group_map` WHERE type={gtype} AND gid={gid} AND mid={mid};'.format(dbtp=db.table_prefix, gtype=gtype, gid=item['gid'], mid=item['mid'])
        db_ret = db.query(sql)
        if db_ret is None or len(db_ret) == 0:
            sql = 'INSERT INTO `{dbtp}group_map` (`type`, `gid`, `mid`) VALUES ' \
                  '({gtype}, {gid}, {mid});' \
                  ''.format(dbtp=db.table_prefix, gtype=gtype, gid=item['gid'], mid=item['mid'])
            db_ret = db.exec(sql)


def get_groups(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude):
    dbtp = get_db().table_prefix
    s = SQL(get_db())
    s.select_from('group', ['id', 'state', 'name', 'desc'], alt_name='g')

    str_where = ''
    _where = list()

    # if len(sql_restrict) > 0:
    #     for k in sql_restrict:
    #         if k == 'ops_policy_id':
    #             _where.append('g.id NOT IN (SELECT rid FROM {dbtp}ops_auz WHERE policy_id={pid} AND rtype=2)'.format(dbtp=dbtp, pid=sql_exclude[k]))
    #         else:
    #             log.w('unknown restrict field: {}\n'.format(k))

    if len(sql_exclude) > 0:
        for k in sql_exclude:
            # if k == 'group_id':
            #     _where.append('u.id NOT IN (SELECT mid FROM {dbtp}group_map WHERE type={gtype} AND gid={gid})'.format(dbtp=dbtp, gtype=TP_GROUP_USER, gid=sql_exclude[k]))
            if k == 'ops_policy_id':
                pid = sql_exclude[k]['pid']
                gtype = sql_exclude[k]['gtype']
                _where.append('g.id NOT IN (SELECT rid FROM {dbtp}ops_auz WHERE policy_id={pid} AND rtype={rtype})'.format(dbtp=dbtp, pid=pid, rtype=gtype))
            elif k == 'auditor_policy_id':
                pid = sql_exclude[k]['pid']
                gtype = sql_exclude[k]['gtype']
                _where.append('g.id NOT IN (SELECT rid FROM {dbtp}audit_auz WHERE policy_id={pid} AND `type`={ptype} AND rtype={rtype})'.format(dbtp=dbtp, pid=pid, ptype=TP_POLICY_OPERATOR, rtype=gtype))
            elif k == 'auditee_policy_id':
                pid = sql_exclude[k]['pid']
                gtype = sql_exclude[k]['gtype']
                _where.append('g.id NOT IN (SELECT rid FROM {dbtp}audit_auz WHERE policy_id={pid} AND `type`={ptype} AND rtype={rtype})'.format(dbtp=dbtp, pid=pid, ptype=TP_POLICY_ASSET, rtype=gtype))
            else:
                log.w('unknown exclude field: {}\n'.format(k))

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'type':
                _where.append('g.type={filter}'.format(filter=sql_filter[k]))
            elif k == 'state':
                _where.append('g.state={filter}'.format(filter=sql_filter[k]))
            elif k == 'search':
                _where.append('(g.name LIKE "%{filter}%" OR g.desc LIKE "%{filter}%")'.format(filter=sql_filter[k]))
            else:
                log.e('unknown filter field: {}\n'.format(k))
                return TPE_PARAM, 0, 0, {}

    if len(_where) > 0:
        str_where = '( {} )'.format(' AND '.join(_where))

    s.where(str_where)

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'name' == sql_order['name']:
            s.order_by('g.name', _sort)
        elif 'state' == sql_order['name']:
            s.order_by('g.state', _sort)
        else:
            log.e('unknown order field: {}\n'.format(sql_order['name']))
            return TPE_PARAM, 0, 0, {}

    if len(sql_limit) > 0:
        s.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = s.query()
    return err, s.total_count, s.page_index, s.recorder


def get_host_groups_for_user(user_id, user_privilege):
    # get all host-groups for current logged in user.

    db = get_db()

    # step 0. return all host-groups if user have all host-group access privilege
    if (user_privilege & (TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_DELETE | TP_PRIVILEGE_ASSET_GROUP)) != 0:
        s = SQL(get_db())
        s.select_from('group', ['id', 'name'], alt_name='g')
        s.where('g.type={}'.format(TP_GROUP_HOST))
        s.order_by('g.name')
        err = s.query()

        return err, s.recorder

    # step 1. get all hosts which could be access by this user.
    sql = 'SELECT `h_id` FROM `{dbtp}ops_map` WHERE `u_id`={dbph} GROUP BY `h_id`;'.format(dbtp=db.table_prefix, dbph=db.place_holder)
    db_ret = db.query(sql, (user_id, ))
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS, None

    hosts = []
    for db_item in db_ret:
        hosts.append(str(db_item[0]))

    if len(hosts) == 0:
        return TPE_NOT_EXISTS, None

    # step 2. get groups which include those hosts.
    sql = 'SELECT `gid` FROM `{dbtp}group_map` WHERE (`type`={gtype} AND `mid` IN ({hids})) GROUP BY `gid`;'.format(dbtp=db.table_prefix, gtype=TP_GROUP_HOST, hids=','.join(hosts))
    db_ret = db.query(sql)

    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS, None

    groups = []
    for db_item in db_ret:
        groups.append(str(db_item[0]))

    # step 3. get those groups id and name.
    s = SQL(get_db())
    s.select_from('group', ['id', 'name'], alt_name='g')
    s.where('g.id IN ({})'.format(','.join(groups)))
    s.order_by('g.name')
    err = s.query()

    return err, s.recorder


def get_acc_groups_for_user(handler):
    # 获取当前用户能查看的远程账号分组列表
    pass
