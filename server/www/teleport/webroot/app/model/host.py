# -*- coding: utf-8 -*-

# import json
# import time

from app.const import *
from app.base.logger import log
from app.base.db import get_db, SQL
from . import syslog
from app.base.stats import tp_stats
from app.base.utils import tp_timestamp_utc_now


def get_host_info(host_id):
    s = SQL(get_db())
    s.select_from('host', ['id', 'type', 'ip', 'router_ip', 'router_port', 'state'], alt_name='h')
    s.where('h.id={}'.format(host_id))
    err = s.query()
    if err != TPE_OK:
        return err, None
    if len(s.recorder) != 1:
        return TPE_DATABASE, None

    return TPE_OK, s.recorder[0]


def get_hosts(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude):
    s = SQL(get_db())
    s.select_from('host', ['id', 'type', 'os_type', 'os_ver', 'name', 'ip', 'router_ip', 'router_port', 'state', 'acc_count', 'cid', 'desc'], alt_name='h')

    str_where = ''
    _where = list()

    if len(sql_restrict) > 0:
        for k in sql_restrict:
            if k == 'group_id':
                _where.append('h.id IN (SELECT mid FROM {}group_map WHERE type={} AND gid={})'.format(get_db().table_prefix, TP_GROUP_HOST, sql_restrict[k]))
            else:
                log.w('unknown restrict field: {}\n'.format(k))

    if len(sql_exclude) > 0:
        for k in sql_exclude:
            if k == 'group_id':
                _where.append('h.id NOT IN (SELECT mid FROM {}group_map WHERE type={} AND gid={})'.format(get_db().table_prefix, TP_GROUP_HOST, sql_exclude[k]))
            elif k == 'ops_policy_id':
                _where.append('h.id NOT IN (SELECT rid FROM {dbtp}ops_auz WHERE policy_id={pid} AND rtype={rtype})'.format(dbtp=get_db().table_prefix, pid=sql_exclude[k], rtype=TP_HOST))
            elif k == 'auditee_policy_id':
                _where.append('h.id NOT IN (SELECT rid FROM {dbtp}audit_auz WHERE policy_id={pid} AND `type`={ptype} AND rtype={rtype})'.format(dbtp=get_db().table_prefix, pid=sql_exclude[k], ptype=TP_POLICY_ASSET, rtype=TP_HOST))
            else:
                log.w('unknown exclude field: {}\n'.format(k))

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'state':
                _where.append('h.state={}'.format(sql_filter[k]))
            elif k == 'search':
                _where.append('(h.name LIKE "%{filter}%" OR h.ip LIKE "%{filter}%" OR h.router_ip LIKE "%{filter}%" OR h.desc LIKE "%{filter}%" OR h.cid LIKE "%{filter}%")'.format(filter=sql_filter[k]))
            elif k == 'host_group':
                shg = SQL(get_db())
                shg.select_from('group_map', ['mid'], alt_name='g')
                shg.where('g.type={} AND g.gid={}'.format(TP_GROUP_HOST, sql_filter[k]))
                err = shg.query()
                if err != TPE_OK:
                    return err, 0, 1, []
                if len(shg.recorder) == 0:
                    return TPE_OK, 0, 1, []
                h_list = ','.join([str(i['mid']) for i in shg.recorder])
                _where.append('h.id IN ({})'.format(h_list))

    if len(_where) > 0:
        str_where = '( {} )'.format(' AND '.join(_where))

    s.where(str_where)

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'ip' == sql_order['name']:
            s.order_by('h.ip', _sort)
        elif 'name' == sql_order['name']:
            s.order_by('h.name', _sort)
        elif 'os_type' == sql_order['name']:
            s.order_by('h.os_type', _sort)
        elif 'cid' == sql_order['name']:
            s.order_by('h.cid', _sort)
        elif 'state' == sql_order['name']:
            s.order_by('h.state', _sort)
        else:
            log.e('unknown order field: {}\n'.format(sql_order['name']))
            return TPE_PARAM, s.total_count, s.page_index, s.recorder

    if len(sql_limit) > 0:
        s.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = s.query()
    return err, s.total_count, s.page_index, s.recorder


def add_host(handler, args):
    """
    添加一个远程主机
    """
    db = get_db()
    _time_now = tp_timestamp_utc_now()

    # 1. 判断此主机是否已经存在了
    if len(args['router_ip']) > 0:
        sql = 'SELECT id FROM {}host WHERE ip="{}" OR (router_ip="{}" AND router_port={});'.format(db.table_prefix, args['ip'], args['router_ip'], args['router_port'])
    else:
        sql = 'SELECT id FROM {}host WHERE ip="{}";'.format(db.table_prefix, args['ip'])
    db_ret = db.query(sql)
    if db_ret is not None and len(db_ret) > 0:
        return TPE_EXISTS, 0

    sql = 'INSERT INTO `{}host` (`type`, `os_type`, `name`, `ip`, `router_ip`, `router_port`, `state`, `creator_id`, `create_time`, `cid`, `desc`) VALUES ' \
          '(1, {os_type}, "{name}", "{ip}", "{router_ip}", {router_port}, {state}, {creator_id}, {create_time}, "{cid}", "{desc}");' \
          ''.format(db.table_prefix,
                    os_type=args['os_type'], name=args['name'], ip=args['ip'], router_ip=args['router_ip'], router_port=args['router_port'],
                    state=TP_STATE_NORMAL, creator_id=handler.get_current_user()['id'], create_time=_time_now,
                    cid=args['cid'], desc=args['desc'])
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, 0

    _id = db.last_insert_id()

    h_name = args['ip']
    if len(args['router_ip']) > 0:
        h_name += '（由{}:{}路由）'.format(args['router_ip'], args['router_port'])
    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "创建主机：{}".format(h_name))
    tp_stats().host_counter_change(1)

    return TPE_OK, _id


def remove_hosts(handler, hosts):
    db = get_db()

    host_ids = ','.join([str(i) for i in hosts])

    sql_list = []

    # step 1. 处理主机对应的账号

    # 1.1 获取账号列表
    s = SQL(db)
    s.select_from('acc', ['id', 'host_ip', 'router_ip', 'router_port', 'username'], alt_name='a')
    s.where('a.host_id IN ({})'.format(host_ids))
    err = s.query()
    if err != TPE_OK:
        return err

    accs = []
    acc_names = []
    for acc in s.recorder:
        if str(acc['id']) not in accs:
            accs.append(str(acc['id']))
        acc_name = '{}@{}'.format(acc['username'], acc['host_ip'])
        if len(acc['router_ip']) > 0:
            acc_name += '（由{}:{}路由）'.format(acc['router_ip'], acc['router_port'])
        if acc_name not in acc_names:
            acc_names.append(acc_name)

    acc_ids = ','.join([i for i in accs])
    if len(accs) > 0:
        # 1.2 将账号从所在组中移除
        where = 'mid IN ({})'.format(acc_ids)
        sql = 'DELETE FROM `{}group_map` WHERE (type={} AND {});'.format(db.table_prefix, TP_GROUP_ACCOUNT, where)
        sql_list.append(sql)
        # if not db.exec(sql):
        #     return TPE_DATABASE

        # 1.3 将账号删除
        where = 'id IN ({})'.format(acc_ids)
        sql = 'DELETE FROM `{}acc` WHERE {};'.format(db.table_prefix, where)
        sql_list.append(sql)
        # if not db.exec(sql):
        #     return TPE_DATABASE

        sql = 'DELETE FROM `{}ops_auz` WHERE rtype={rtype} AND rid IN ({rid});'.format(db.table_prefix, rtype=TP_ACCOUNT, rid=acc_ids)
        sql_list.append(sql)

        sql = 'DELETE FROM `{}ops_map` WHERE a_id IN ({acc_ids});'.format(db.table_prefix, acc_ids=acc_ids)
        sql_list.append(sql)

    # step 2. 处理主机
    s = SQL(db)
    s.select_from('host', ['ip', 'router_ip', 'router_port'], alt_name='h')
    s.where('h.id IN ({})'.format(host_ids))
    err = s.query()
    if err != TPE_OK:
        return err

    host_names = []
    for h in s.recorder:
        h_name = h['ip']
        if len(h['router_ip']) > 0:
            h_name += '（由{}:{}路由）'.format(h['router_ip'], h['router_port'])
        if h_name not in host_names:
            host_names.append(h_name)

    # 2.1 将主机从所在组中移除
    where = 'mid IN ({})'.format(host_ids)
    sql = 'DELETE FROM `{}group_map` WHERE (type={} AND {});'.format(db.table_prefix, TP_GROUP_HOST, where)
    sql_list.append(sql)

    # 2.2 将主机删除
    where = 'id IN ({})'.format(host_ids)
    sql = 'DELETE FROM `{}host` WHERE {};'.format(db.table_prefix, where)
    sql_list.append(sql)

    sql = 'DELETE FROM `{}ops_auz` WHERE rtype={rtype} AND rid IN ({rid});'.format(db.table_prefix, rtype=TP_HOST, rid=host_ids)
    sql_list.append(sql)
    sql = 'DELETE FROM `{}ops_map` WHERE h_id IN ({host_ids});'.format(db.table_prefix, host_ids=host_ids)
    sql_list.append(sql)

    if not db.transaction(sql_list):
        return TPE_DATABASE

    if len(acc_names) > 0:
        syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "删除账号：{}".format('，'.join(acc_names)))
        tp_stats().acc_counter_change(0 - len(acc_names))
    if len(host_names) > 0:
        syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "删除主机：{}".format('，'.join(host_names)))
        tp_stats().host_counter_change(0 - len(host_names))

    return TPE_OK


def update_host(handler, args):
    """
    更新一个远程主机
    """
    db = get_db()

    # 1. 判断是否存在
    sql = 'SELECT `id` FROM `{}host` WHERE `id`={};'.format(db.table_prefix, args['id'])
    db_ret = db.query(sql)
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS

    sql_list = []
    sql = 'UPDATE `{}host` SET `os_type`={os_type}, `name`="{name}", `ip`="{ip}", `router_ip`="{router_ip}", ' \
          '`router_port`={router_port}, `cid`="{cid}", `desc`="{desc}" WHERE `id`={host_id};' \
          ''.format(db.table_prefix,
                    os_type=args['os_type'], name=args['name'], ip=args['ip'], router_ip=args['router_ip'], router_port=args['router_port'],
                    cid=args['cid'], desc=args['desc'], host_id=args['id'])
    sql_list.append(sql)

    # 更新所有此主机相关的账号
    sql = 'UPDATE `{}acc` SET `host_ip`="{ip}", `router_ip`="{router_ip}", `router_port`={router_port} WHERE `host_id`={id};' \
          ''.format(db.table_prefix,
                    ip=args['ip'], router_ip=args['router_ip'], router_port=args['router_port'], id=args['id'])
    sql_list.append(sql)

    # 同步更新授权表和权限映射表
    _name = args['ip']
    if len(args['name']) > 0:
        _name = '{} [{}]'.format(args['name'], args['ip'])

    # 运维授权
    sql = 'UPDATE `{}ops_auz` SET `name`="{name}" WHERE (`rtype`={rtype} AND `rid`={rid});' \
          ''.format(db.table_prefix, name=_name, rtype=TP_HOST, rid=args['id'])
    sql_list.append(sql)
    sql = 'UPDATE `{}ops_map` SET `h_name`="{hname}", `ip`="{ip}", `router_ip`="{router_ip}", `router_port`={router_port} ' \
          'WHERE (h_id={hid});'.format(db.table_prefix,
                                       hname=args['name'], ip=args['ip'], hid=args['id'],
                                       router_ip=args['router_ip'], router_port=args['router_port'])
    sql_list.append(sql)
    # 审计授权
    sql = 'UPDATE `{}audit_auz` SET `name`="{name}" WHERE (`rtype`={rtype} AND `rid`={rid});'.format(db.table_prefix, name=_name, rtype=TP_HOST, rid=args['id'])
    sql_list.append(sql)
    sql = 'UPDATE `{}audit_map` SET `h_name`="{hname}", `ip`="{ip}", `router_ip`="{router_ip}", `router_port`={router_port} ' \
          'WHERE (h_id={hid});'.format(db.table_prefix,
                                       hname=args['name'], ip=args['ip'], hid=args['id'],
                                       router_ip=args['router_ip'], router_port=args['router_port'])
    sql_list.append(sql)

    if not db.transaction(sql_list):
        return TPE_DATABASE

    operator = handler.get_current_user()
    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "更新主机信息：{}".format(_name))

    return TPE_OK


def update_hosts_state(handler, host_ids, state):
    db = get_db()

    host_ids = ','.join([str(i) for i in host_ids])

    sql_list = []

    sql = 'UPDATE `{}host` SET `state`={state} WHERE `id` IN ({host_ids});' \
          ''.format(db.table_prefix, state=state, host_ids=host_ids)
    sql_list.append(sql)

    # sync to update the ops-audit table.
    sql = 'UPDATE `{}ops_auz` SET `state`={state} WHERE `rtype`={rtype} AND `rid` IN ({rid});' \
          ''.format(db.table_prefix, state=state, rtype=TP_ACCOUNT, rid=host_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}ops_map` SET `h_state`={state} WHERE `h_id` IN ({host_ids});' \
          ''.format(db.table_prefix, state=state, host_ids=host_ids)
    sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


#
# def unlock_hosts(handler, host_ids):
#     db = get_db()
#
#     host_ids = ','.join([str(i) for i in host_ids])
#     sql_list = []
#
#     sql = 'UPDATE `{}host` SET state={state} WHERE id IN ({host_ids});' \
#           ''.format(db.table_prefix, state=TP_STATE_NORMAL, host_ids=host_ids)
#     sql_list.append(sql)
#     sql = 'UPDATE `{}ops_map` SET h_state={state} WHERE h_id IN ({host_ids});' \
#           ''.format(db.table_prefix, state=TP_STATE_NORMAL, host_ids=host_ids)
#     sql_list.append(sql)
#
#     if db.transaction(sql_list):
#         return TPE_OK
#     else:
#         return TPE_DATABASE


def get_group_with_member(sql_filter, sql_order, sql_limit):
    """
    获取主机组列表，以及每个组的总成员数以及不超过5个的成员
    """
    # 首先获取要查询的组的信息
    sg = SQL(get_db())
    sg.select_from('group', ['id', 'state', 'name', 'desc'], alt_name='g')

    _where = list()
    _where.append('g.type={}'.format(TP_GROUP_HOST))

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'search':
                _where.append('(g.name LIKE "%{}%" OR g.desc LIKE "%{}%")'.format(sql_filter[k], sql_filter[k]))
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
    _where.append('gm.type={}'.format(TP_GROUP_HOST))
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

    # 将得到的账号id合并到列表中并去重，然后获取这些账号的信息
    users = []
    for g in sg.recorder:
        users.extend(g['_mid'])
    users = list(set(users))

    su = SQL(get_db())
    su.select_from('host', ['id', 'os_type', 'name', 'ip', 'router_ip', 'router_port', 'cid'], alt_name='h')

    su.where('h.id IN ({})'.format(','.join([str(uid) for uid in users])))
    su.order_by('h.ip')
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
