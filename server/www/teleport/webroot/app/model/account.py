# -*- coding: utf-8 -*-

from app.const import *
from app.base.logger import log
from app.base.db import get_db, SQL
from . import syslog
from app.base.utils import tp_timestamp_utc_now
from app.base.stats import tp_stats


def get_account_info(acc_id):
    s = SQL(get_db())
    # s.select_from('acc', ['id', 'password', 'pri_key', 'state', 'host_ip', 'router_ip', 'router_port', 'protocol_type', 'protocol_port', 'auth_type', 'username'], alt_name='a')
    s.select_from('acc', ['id', 'password', 'pri_key', 'state', 'host_id', 'protocol_type', 'protocol_port', 'auth_type', 'username', 'username_prompt', 'password_prompt'], alt_name='a')
    s.where('a.id={}'.format(acc_id))
    err = s.query()
    if err != TPE_OK:
        return err, None
    if len(s.recorder) != 1:
        return TPE_DATABASE, None

    sh = SQL(get_db())
    sh.select_from('host', ['id', 'name', 'ip', 'router_ip', 'router_port', 'state'], alt_name='h')
    sh.where('h.id={}'.format(s.recorder[0].host_id))
    err = sh.query()
    if err != TPE_OK:
        return err, None
    if len(s.recorder) != 1:
        return TPE_DATABASE, None

    s.recorder[0]['_host'] = sh.recorder[0]

    return TPE_OK, s.recorder[0]


def get_host_accounts(host_id):
    # 获取指定主机的所有账号
    s = SQL(get_db())
    # s.select_from('acc', ['id', 'state', 'host_ip', 'router_ip', 'router_port', 'protocol_type', 'protocol_port', 'auth_type', 'username', 'pri_key'], alt_name='a')
    s.select_from('acc', ['id', 'state', 'protocol_type', 'protocol_port', 'auth_type', 'username', 'username_prompt', 'password_prompt'], alt_name='a')

    s.where('a.host_id={}'.format(host_id))
    s.order_by('a.username', True)

    err = s.query()
    return err, s.recorder


def get_group_with_member(sql_filter, sql_order, sql_limit):
    """
    获取用户组列表，以及每个组的总成员数以及不超过5个的成员
    """
    db = get_db()
    # 首先获取要查询的组的信息
    sg = SQL(db)
    sg.select_from('group', ['id', 'name', 'state', 'desc'], alt_name='g')

    _where = list()
    _where.append('g.type={}'.format(TP_GROUP_ACCOUNT))

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
            return TPE_PARAM, sg.total_count, 0, sg.recorder

    if len(sql_limit) > 0:
        sg.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = sg.query()
    if err != TPE_OK or len(sg.recorder) == 0:
        return err, sg.total_count, 0, sg.recorder

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
    _where.append('gm.type={}'.format(TP_GROUP_ACCOUNT))
    _where.append('gm.gid IN ({})'.format(','.join([str(gid) for gid in groups])))
    str_where = '( {} )'.format(' AND '.join(_where))
    sgm.where(str_where)
    err = sgm.query()
    if err != TPE_OK or len(sgm.recorder) == 0:
        return err, sg.total_count, 0, sg.recorder

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
    # su.select_from('acc', ['id', 'host_ip', 'router_ip', 'router_port', 'username', 'protocol_type'], alt_name='a')
    su.select_from('acc', ['id', 'host_id', 'username', 'protocol_type'], alt_name='a')

    su.where('a.id IN ({})'.format(','.join([str(uid) for uid in users])))
    su.order_by('a.username')
    err = su.query()
    if err != TPE_OK or len(su.recorder) == 0:
        return err, sg.total_count, 0, sg.recorder

    # 得到主机id列表，然后查询相关主机的详细信息
    host_ids = []
    for _acc in su.recorder:
        if _acc.host_id not in host_ids:
            host_ids.append(_acc.host_id)
    s_host = SQL(db)
    s_host.select_from('host', ['id', 'name', 'ip', 'router_ip', 'router_port', 'state'], alt_name='h')
    str_host_ids = ','.join([str(i) for i in host_ids])
    s_host.where('h.id IN ({ids})'.format(ids=str_host_ids))
    err = s_host.query()
    if err != TPE_OK:
        return err, sg.total_count, 0, sg.recorder
    hosts = {}
    for _host in s_host.recorder:
        if _host.id not in hosts:
            hosts[_host.id] = _host

    for _acc in su.recorder:
        _acc['_host'] = hosts[_acc.host_id]

    # 现在可以将具体的用户信息追加到组信息中了
    for g in sg.recorder:
        for u in su.recorder:
            for m in g['_mid']:
                if u['id'] == m:
                    g['members'].append(u)

    return err, sg.total_count, sg.page_index, sg.recorder


def get_accounts(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude):
    db = get_db()
    dbtp = db.table_prefix

    s = SQL(db)
    # s.select_from('acc', ['id', 'host_id', 'host_ip', 'router_ip', 'router_port', 'username', 'protocol_type', 'auth_type', 'state'], alt_name='a')
    s.select_from('acc', ['id', 'host_id', 'username', 'protocol_type', 'auth_type', 'state', 'username_prompt', 'password_prompt'], alt_name='a')

    str_where = ''
    _where = list()

    if len(sql_restrict) > 0:
        for k in sql_restrict:
            if k == 'group_id':
                _where.append('a.id IN (SELECT mid FROM {}group_map WHERE type={} AND gid={})'.format(dbtp, TP_GROUP_ACCOUNT, sql_restrict[k]))
            else:
                log.w('unknown restrict field: {}\n'.format(k))

    if len(sql_exclude) > 0:
        for k in sql_exclude:
            if k == 'group_id':
                _where.append('a.id NOT IN (SELECT mid FROM {}group_map WHERE type={} AND gid={})'.format(dbtp, TP_GROUP_ACCOUNT, sql_exclude[k]))
            elif k == 'ops_policy_id':
                _where.append('a.id NOT IN (SELECT rid FROM {dbtp}ops_auz WHERE policy_id={pid} AND rtype={rtype})'.format(dbtp=dbtp, pid=sql_exclude[k], rtype=TP_ACCOUNT))
            else:
                log.w('unknown exclude field: {}\n'.format(k))

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'search':
                _where.append('(a.username LIKE "%{filter}%" OR a.host_ip LIKE "%{filter}%" OR a.router_ip LIKE "%{filter}%")'.format(filter=sql_filter[k]))
                # _where.append('(a.username LIKE "%{filter}%")'.format(filter=sql_filter[k]))

    if len(_where) > 0:
        str_where = '( {} )'.format(' AND '.join(_where))

    s.where(str_where)

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'username' == sql_order['name']:
            s.order_by('a.username', _sort)
        elif 'protocol_type' == sql_order['name']:
            s.order_by('a.protocol_type', _sort)
        elif 'state' == sql_order['name']:
            s.order_by('a.state', _sort)
        else:
            log.e('unknown order field: {}\n'.format(sql_order['name']))
            return TPE_PARAM, s.total_count, 1, s.recorder

    if len(sql_limit) > 0:
        s.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = s.query()
    if err != TPE_OK:
        return err, 0, 1, None

    # 得到主机id列表，然后查询相关主机的详细信息
    host_ids = []
    for _acc in s.recorder:
        if _acc.host_id not in host_ids:
            host_ids.append(_acc.host_id)
    if len(host_ids) == 0:
        return TPE_OK, 0, 1, None
    s_host = SQL(db)
    s_host.select_from('host', ['id', 'name', 'ip', 'router_ip', 'router_port', 'state'], alt_name='h')
    str_host_ids = ','.join([str(i) for i in host_ids])
    s_host.where('h.id IN ({ids})'.format(ids=str_host_ids))
    err = s_host.query()
    if err != TPE_OK:
        return err, 0, None
    hosts = {}
    for _host in s_host.recorder:
        if _host.id not in hosts:
            hosts[_host.id] = _host

    for _acc in s.recorder:
        _acc['_host'] = hosts[_acc.host_id]

    return err, s.total_count, s.page_index, s.recorder


def add_account(handler, host_id, args):
    """
    添加一个远程账号
    """
    db = get_db()
    _time_now = tp_timestamp_utc_now()
    operator = handler.get_current_user()

    # 1. 判断是否已经存在了
    sql = 'SELECT id FROM {}acc WHERE host_id={} AND protocol_port={} AND username="{}" AND auth_type={};'.format(db.table_prefix, host_id, args['protocol_port'], args['username'], args['auth_type'])
    db_ret = db.query(sql)
    if db_ret is not None and len(db_ret) > 0:
        return TPE_EXISTS, 0

    sql = 'INSERT INTO `{}acc` (host_id, host_ip, router_ip, router_port, protocol_type, protocol_port, state, auth_type, username, username_prompt, password_prompt, password, pri_key, creator_id, create_time) VALUES ' \
          '({host_id}, "{host_ip}", "{router_ip}", {router_port}, {protocol_type}, {protocol_port}, {state}, {auth_type}, "{username}", "{username_prompt}", "{password_prompt}", "{password}", "{pri_key}", {creator_id}, {create_time});' \
          ''.format(db.table_prefix,
                    host_id=host_id, host_ip=args['host_ip'], router_ip=args['router_ip'], router_port=args['router_port'],
                    protocol_type=args['protocol_type'], protocol_port=args['protocol_port'], state=TP_STATE_NORMAL,
                    auth_type=args['auth_type'], username=args['username'], username_prompt=args['username_prompt'], password_prompt=args['password_prompt'],
                    password=args['password'], pri_key=args['pri_key'], creator_id=operator['id'], create_time=_time_now)

    # sql = 'INSERT INTO `{}acc` (host_id, protocol_type, protocol_port, state, auth_type, username, password, pri_key, creator_id, create_time) VALUES ' \
    #       '({host_id}, {protocol_type}, {protocol_port}, {state}, {auth_type}, "{username}", "{password}", "{pri_key}", {creator_id}, {create_time});' \
    #       ''.format(db.table_prefix,
    #                 host_id=host_id,
    #                 protocol_type=args['protocol_type'], protocol_port=args['protocol_port'], state=TP_STATE_NORMAL,
    #                 auth_type=args['auth_type'], username=args['username'], password=args['password'], pri_key=args['pri_key'],
    #                 creator_id=operator['id'], create_time=_time_now)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, 0

    _id = db.last_insert_id()

    acc_name = '{}@{}'.format(args['username'], args['host_ip'])
    if len(args['router_ip']) > 0:
        acc_name += '（由{}:{}路由）'.format(args['router_ip'], args['router_port'])
    syslog.sys_log(operator, handler.request.remote_ip, TPE_OK, "创建账号：{}".format(acc_name))

    # 更新主机相关账号数量
    sql = 'UPDATE `{}host` SET acc_count=acc_count+1 WHERE id={host_id};' \
          ''.format(db.table_prefix, host_id=host_id)
    db_ret = db.exec(sql)
    # if not db_ret:
    #     return TPE_DATABASE, 0

    tp_stats().acc_counter_change(1)

    return TPE_OK, _id


def update_account(handler, host_id, acc_id, args):
    """
    更新一个远程账号
    """
    db = get_db()

    # 1. 判断是否存在
    sql = 'SELECT `id`, `host_ip`, `router_ip`, `router_port` FROM `{}acc` WHERE `host_id`={host_id} AND `id`={acc_id};'.format(db.table_prefix, host_id=host_id, acc_id=acc_id)
    db_ret = db.query(sql)
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS

    _host_ip = db_ret[0][1]
    _router_ip = db_ret[0][2]
    _router_port = db_ret[0][3]

    sql_list = []

    sql = list()
    sql.append('UPDATE `{}acc` SET'.format(db.table_prefix))

    _set = list()
    _set.append('`protocol_type`={}'.format(args['protocol_type']))
    _set.append('`protocol_port`={}'.format(args['protocol_port']))
    _set.append('`auth_type`={}'.format(args['auth_type']))
    _set.append('`username`="{}"'.format(args['username']))
    _set.append('`username_prompt`="{}"'.format(args['username_prompt']))
    _set.append('`password_prompt`="{}"'.format(args['password_prompt']))

    if args['auth_type'] == TP_AUTH_TYPE_PASSWORD and len(args['password']) > 0:
        _set.append('`password`="{}"'.format(args['password']))
    elif args['auth_type'] == TP_AUTH_TYPE_PRIVATE_KEY and len(args['pri_key']) > 0:
        _set.append('`pri_key`="{}"'.format(args['pri_key']))

    sql.append(','.join(_set))
    sql.append('WHERE `id`={};'.format(acc_id))

    # db_ret = db.exec(' '.join(sql))
    # if not db_ret:
    #     return TPE_DATABASE
    sql_list.append(' '.join(sql))

    if len(_router_ip) == 0:
        _name = '{}@{}'.format(args['username'], _host_ip)
    else:
        _name = '{}@{} （由{}:{}路由）'.format(args['username'], _host_ip, _router_ip, _router_port)

    # 运维授权
    sql = 'UPDATE `{}ops_auz` SET `name`="{name}" WHERE (`rtype`={rtype} AND `rid`={rid});'.format(db.table_prefix, name=_name, rtype=TP_ACCOUNT, rid=acc_id)
    sql_list.append(sql)
    sql = 'UPDATE `{}ops_map` SET `a_name`="{name}", `protocol_type`={protocol_type}, `protocol_port`={protocol_port} ' \
          'WHERE (a_id={aid});'.format(db.table_prefix,
                                       name=args['username'], protocol_type=args['protocol_type'], protocol_port=args['protocol_port'],
                                       aid=acc_id)
    sql_list.append(sql)

    if not db.transaction(sql_list):
        return TPE_DATABASE

    return TPE_OK


def update_accounts_state(handler, host_id, acc_ids, state):
    db = get_db()
    acc_ids = ','.join([str(uid) for uid in acc_ids])

    # 1. 判断是否存在
    sql = 'SELECT id FROM {}acc WHERE host_id={host_id} AND id IN ({ids});'.format(db.table_prefix, host_id=host_id, ids=acc_ids)
    db_ret = db.query(sql)
    if db_ret is None or len(db_ret) == 0:
        return TPE_NOT_EXISTS

    sql_list = []

    sql = 'UPDATE `{}acc` SET state={state} WHERE id IN ({ids});' \
          ''.format(db.table_prefix, state=state, ids=acc_ids)
    sql_list.append(sql)

    # sync to update the ops-audit table.
    sql = 'UPDATE `{}ops_auz` SET state={state} WHERE rtype={rtype} AND rid IN ({rid});' \
          ''.format(db.table_prefix, state=state, rtype=TP_ACCOUNT, rid=acc_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}ops_map` SET a_state={state} WHERE a_id IN ({acc_id});' \
          ''.format(db.table_prefix, state=state, acc_id=acc_ids)
    sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


def remove_accounts(handler, host_id, acc_ids):
    """
    删除远程账号
    """
    db = get_db()
    acc_count = len(acc_ids)
    acc_ids = ','.join([str(uid) for uid in acc_ids])

    s = SQL(db)
    # 1. 判断是否存在
    s.select_from('host', ['name', 'ip', 'router_ip', 'router_port', 'acc_count'], alt_name='a')
    s.where('a.id={h_id}'.format(h_id=host_id, ids=acc_ids))
    err = s.query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS
    _h_name = s.recorder[0].name
    _h_ip = s.recorder[0].ip
    _h_router_ip = s.recorder[0].router_ip
    _h_router_port = s.recorder[0].router_port

    s.reset().select_from('acc', ['username'], alt_name='a')
    s.where('a.host_id={h_id} AND a.id IN ({ids}) '.format(h_id=host_id, ids=acc_ids))
    err = s.query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    acc_names = []
    for a in s.recorder:
        acc_name = '{}@{}'.format(a.username, _h_ip)
        if len(_h_router_ip) > 0:
            acc_name += '（由{}:{}路由）'.format(_h_router_ip, _h_router_port)
        acc_names.append(acc_name)

    sql_list = []

    sql = 'DELETE FROM `{}acc` WHERE host_id={} AND id IN ({});'.format(db.table_prefix, host_id, acc_ids)
    sql_list.append(sql)

    sql = 'DELETE FROM `{}group_map` WHERE type={} AND mid IN ({});'.format(db.table_prefix, TP_GROUP_ACCOUNT, acc_ids)
    sql_list.append(sql)

    # 更新主机相关账号数量
    sql = 'UPDATE `{}host` SET acc_count=acc_count-{acc_count} WHERE id={host_id};'.format(db.table_prefix, acc_count=acc_count, host_id=host_id)
    sql_list.append(sql)

    sql = 'DELETE FROM `{}ops_auz` WHERE rtype={rtype} AND rid IN ({rid});'.format(db.table_prefix, rtype=TP_ACCOUNT, rid=acc_ids)
    sql_list.append(sql)

    sql = 'DELETE FROM `{}ops_map` WHERE a_id IN ({acc_id});'.format(db.table_prefix, acc_id=acc_ids)
    sql_list.append(sql)

    if not db.transaction(sql_list):
        return TPE_DATABASE

    # s.reset().select_from('host', ['acc_count'], alt_name='a')
    # s.where('a.id={h_id}'.format(h_id=host_id, ids=acc_ids))
    # err = s.query()
    # if err != TPE_OK:
    #     return err
    # if len(s.recorder) == 0:
    #     return TPE_NOT_EXISTS

    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "删除账号：{}".format('，'.join(acc_names)))

    tp_stats().acc_counter_change(-1)

    return TPE_OK
