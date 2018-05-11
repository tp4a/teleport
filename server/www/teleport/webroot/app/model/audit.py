# -*- coding: utf-8 -*-

from app.const import *
from app.base.logger import log
from app.base.db import get_db, SQL
from app.model import syslog
from app.model import policy
from app.base.utils import AttrDict, tp_timestamp_utc_now


def get_by_id(pid):
    s = SQL(get_db())
    s.select_from('audit_policy', ['id', 'name', 'desc'], alt_name='p')
    s.where('p.id={}'.format(pid))
    err = s.query()
    if err != TPE_OK:
        return err, {}

    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS, {}

    return TPE_OK, s.recorder[0]


def get_policies(sql_filter, sql_order, sql_limit):
    dbtp = get_db().table_prefix
    s = SQL(get_db())
    s.select_from('audit_policy', ['id', 'rank', 'name', 'desc', 'state'], alt_name='p')

    str_where = ''
    _where = list()

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'search':
                _where.append('(p.name LIKE "%{filter}%" OR p.desc LIKE "%{filter}%")'.format(filter=sql_filter[k]))
            if k == 'state':
                _where.append('p.state={}'.format(sql_filter[k]))
            else:
                log.e('unknown filter field: {}\n'.format(k))
                return TPE_PARAM, s.total_count, 0, s.recorder

    if len(_where) > 0:
        str_where = '( {} )'.format(' AND '.join(_where))

    s.where(str_where)

    s.order_by('p.rank', True)

    if len(sql_limit) > 0:
        s.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = s.query()
    return err, s.total_count, s.page_index, s.recorder


def create_policy(handler, args):
    """
    创建一个授权策略
    """
    db = get_db()
    _time_now = tp_timestamp_utc_now()

    # 1. 判断此账号是否已经存在了
    s = SQL(db)
    err = s.reset().select_from('audit_policy', ['id']).where('audit_policy.name="{}"'.format(args['name'])).query()
    if err != TPE_OK:
        return err, 0
    if len(s.recorder) > 0:
        return TPE_EXISTS, 0

    # 2. get total count
    sql = 'SELECT COUNT(*) FROM {}audit_policy'.format(db.table_prefix)
    db_ret = db.query(sql)
    if not db_ret or len(db_ret) == 0:
        return TPE_DATABASE, 0
    rank = db_ret[0][0] + 1

    sql = 'INSERT INTO `{}audit_policy` (`rank`, `name`, `desc`, `creator_id`, `create_time`) VALUES ' \
          '({rank}, "{name}", "{desc}", {creator_id}, {create_time});' \
          ''.format(db.table_prefix,
                    rank=rank, name=args['name'], desc=args['desc'],
                    creator_id=handler.get_current_user()['id'],
                    create_time=_time_now)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, 0

    _id = db.last_insert_id()

    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "创建审计授权策略：{}".format(args['name']))

    return TPE_OK, _id


def update_policy(handler, args):
    db = get_db()

    # 1. 判断此账号是否已经存在
    s = SQL(db)
    err = s.reset().select_from('audit_policy', ['id']).where('audit_policy.id={}'.format(args['id'])).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    sql = 'UPDATE `{}audit_policy` SET `name`="{name}", `desc`="{desc}" WHERE `id`={p_id};' \
          ''.format(db.table_prefix,
                    name=args['name'], desc=args['desc'], p_id=args['id']
                    )
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    return TPE_OK


def update_policies_state(handler, p_ids, state):
    db = get_db()

    p_ids = ','.join([str(i) for i in p_ids])

    sql_list = []

    sql = 'UPDATE `{}audit_policy` SET `state`={state} WHERE `id` IN ({p_ids});'.format(db.table_prefix, state=state, p_ids=p_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}audit_auz` SET `state`={state} WHERE `policy_id` IN ({p_ids});'.format(db.table_prefix, state=state, p_ids=p_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}audit_map` SET `p_state`={state} WHERE `p_id` IN ({p_ids});'.format(db.table_prefix, state=state, p_ids=p_ids)
    sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


def remove_policies(handler, p_ids):
    db = get_db()

    p_ids = ','.join([str(i) for i in p_ids])

    sql_list = []

    sql = 'DELETE FROM `{}audit_policy` WHERE `id` IN ({p_ids});'.format(db.table_prefix, p_ids=p_ids)
    sql_list.append(sql)

    sql = 'DELETE FROM `{}audit_auz` WHERE `policy_id` IN ({p_ids});'.format(db.table_prefix, p_ids=p_ids)
    sql_list.append(sql)

    sql = 'DELETE FROM `{}audit_map` WHERE `p_id` IN ({p_ids});'.format(db.table_prefix, p_ids=p_ids)
    sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


def add_members(handler, policy_id, policy_type, ref_type, members):
    # step 1: select exists rid.
    s = SQL(get_db())
    s.select_from('audit_auz', ['rid'], alt_name='p')
    _where = list()
    _where.append('p.policy_id={}'.format(policy_id))
    _where.append('p.type={}'.format(policy_type))
    _where.append('p.rtype={}'.format(ref_type))
    s.where('( {} )'.format(' AND '.join(_where)))
    err = s.query()
    if err != TPE_OK:
        return err
    exists_ids = [r['rid'] for r in s.recorder]

    operator = handler.get_current_user()

    db = get_db()
    _time_now = tp_timestamp_utc_now()

    sql = []
    # for uid in members:
    #     sql.append('INSERT INTO `{}group_map` (type, gid, mid) VALUES ({}, {}, {});'.format(db.table_prefix, gtype, gid, uid))
    # print(args['members'])
    for m in members:
        if m['id'] in exists_ids:
            continue
        str_sql = 'INSERT INTO `{}audit_auz` (policy_id, type, rtype, rid, `name`, creator_id, create_time) VALUES ' \
                  '({pid}, {t}, {rtype}, {rid}, "{name}", {creator_id}, {create_time});' \
                  ''.format(db.table_prefix,
                            pid=policy_id, t=policy_type, rtype=ref_type,
                            rid=m['id'], name=m['name'],
                            creator_id=operator['id'], create_time=_time_now)
        sql.append(str_sql)

    if db.transaction(sql):
        # return TPE_OK
        return policy.rebuild_audit_auz_map()
    else:
        return TPE_DATABASE


def remove_members(handler, policy_id, policy_type, ids):
    s = SQL(get_db())

    auz_ids = [str(i) for i in ids]

    # 将用户从所在组中移除
    where = 'policy_id={} AND type={} AND id IN ({})'.format(policy_id, policy_type, ','.join(auz_ids))
    err = s.reset().delete_from('audit_auz').where(where).exec()
    if err != TPE_OK:
        return err

    # return TPE_OK
    return policy.rebuild_audit_auz_map()


def get_auditors(sql_filter, sql_order, sql_limit):
    ss = SQL(get_db())
    ss.select_from('audit_auz', ['id', 'policy_id', 'rtype', 'rid', 'name'], alt_name='p')

    _where = list()
    _where.append('p.type=0')
    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'policy_id':
                # _where.append('(p.name LIKE "%{filter}%" OR p.desc LIKE "%{filter}%")'.format(filter=sql_filter[k]))
                _where.append('p.policy_id={}'.format(sql_filter[k]))
            elif k == 'search':
                _where.append('(p.name LIKE "%{filter}%")'.format(filter=sql_filter[k]))
            else:
                log.e('unknown filter field: {}\n'.format(k))
                return TPE_PARAM, 0, 0, {}
    if len(_where) > 0:
        ss.where('( {} )'.format(' AND '.join(_where)))

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'name' == sql_order['name']:
            ss.order_by('p.name', _sort)
        elif 'rtype' == sql_order['name']:
            ss.order_by('p.rtype', _sort)
        else:
            log.e('unknown order field: {}\n'.format(sql_order['name']))
            return TPE_PARAM, ss.total_count, 0, ss.recorder

    if len(sql_limit) > 0:
        ss.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = ss.query()
    if err != TPE_OK:
        return err, 0, 0, {}

    # print(ss.recorder)
    return TPE_OK, ss.total_count, ss.page_index, ss.recorder


def get_auditees(sql_filter, sql_order, sql_limit):
    ss = SQL(get_db())
    ss.select_from('audit_auz', ['id', 'policy_id', 'rtype', 'rid', 'name'], alt_name='p')

    _where = list()
    _where.append('p.type=1')
    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'policy_id':
                # _where.append('(p.name LIKE "%{filter}%" OR p.desc LIKE "%{filter}%")'.format(filter=sql_filter[k]))
                _where.append('p.policy_id={}'.format(sql_filter[k]))
            elif k == 'search':
                _where.append('(p.name LIKE "%{filter}%")'.format(filter=sql_filter[k]))
            else:
                log.e('unknown filter field: {}\n'.format(k))
                return TPE_PARAM, 0, 0, {}
    if len(_where) > 0:
        ss.where('( {} )'.format(' AND '.join(_where)))

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'name' == sql_order['name']:
            ss.order_by('p.name', _sort)
        elif 'rtype' == sql_order['name']:
            ss.order_by('p.rtype', _sort)
        else:
            log.e('unknown order field: {}\n'.format(sql_order['name']))
            return TPE_PARAM, ss.total_count, 0, ss.recorder

    if len(sql_limit) > 0:
        ss.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = ss.query()
    if err != TPE_OK:
        return err, 0, 0, {}

    # print(ss.recorder)
    return TPE_OK, ss.total_count, ss.page_index, ss.recorder


def rank_reorder(handler, pid, new_rank, start_rank, end_rank, direct):
    db = get_db()

    # 调节顺序：
    # 由pid获取被移动的策略，得到其rank，即，p_rank
    #  p_rank > new_rank，向前移动
    #    所有 new_rank <= rank < p_rank 的条目，其rank+1
    #  p_rank < new_rank，向后移动
    #    所有 new_rank >= rank > p_rank 的条目，其rank-1
    # 最后令pid条目的rank为new_rank

    # 1. 判断此账号是否已经存在
    s = SQL(db)
    err = s.select_from('audit_policy', ['id', 'name', 'rank']).where('audit_policy.id={}'.format(pid)).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    p_name = s.recorder[0]['name']
    p_rank = s.recorder[0]['rank']

    sql = 'UPDATE `{dbtp}audit_policy` SET rank=rank{direct} WHERE (rank>={start_rank} AND rank<={end_rank});' \
          ''.format(dbtp=db.table_prefix, direct=direct, start_rank=start_rank, end_rank=end_rank)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    sql = 'UPDATE `{dbtp}audit_policy` SET rank={new_rank} WHERE id={pid};' \
          ''.format(dbtp=db.table_prefix, new_rank=new_rank, pid=pid)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "调整审计授权策略顺序：{}，从{}到{}".format(p_name, p_rank, new_rank))

    # return TPE_OK
    return policy.rebuild_audit_auz_map()


def get_auth(auth_id):
    db = get_db()
    s = SQL(db)
    err = s.select_from('audit_map', ['id', 'h_id', 'u_id', 'a_id']).where('audit_map.uni_id="{}"'.format(auth_id)).query()
    if err != TPE_OK:
        return None, err
    if len(s.recorder) == 0:
        return None, TPE_NOT_EXISTS

    if len(s.recorder) != 1:
        return None, TPE_FAILED

    # log.v(s.recorder[0])
    return s.recorder[0], TPE_OK


def build_auz_map():
    _users = {}
    _hosts = {}
    # _accs = {}
    _gusers = {}
    _ghosts = {}
    # _gaccs = {}
    _groups = {}
    _policies = {}

    _p_users = {}
    _p_assets = {}

    _map = []

    db = get_db()
    dbtp = db.table_prefix
    db.exec('DELETE FROM {}audit_map'.format(dbtp))

    s = SQL(get_db())

    # 加载所有策略
    err = s.reset().select_from('audit_policy', ['id', 'rank', 'state'], alt_name='p').query()
    if err != TPE_OK:
        return err
    if 0 == len(s.recorder):
        return TPE_OK
    for i in s.recorder:
        _policies[i.id] = i

    # 加载所有的用户
    err = s.reset().select_from('user', ['id', 'username', 'surname', 'state'], alt_name='u').query()
    if err != TPE_OK:
        return err
    if 0 == len(s.recorder):
        return TPE_OK
    for i in s.recorder:
        _users[i.id] = i

    # 加载所有的主机
    err = s.reset().select_from('host', ['id', 'name', 'ip', 'router_ip', 'router_port', 'state'], alt_name='h').query()
    if err != TPE_OK:
        return err
    if 0 == len(s.recorder):
        return TPE_OK
    for i in s.recorder:
        _hosts[i.id] = i

    # # 加载所有的账号
    # err = s.reset().select_from('acc', ['id', 'host_id', 'username', 'protocol_type', 'protocol_port', 'auth_type', 'state'], alt_name='a').query()
    # if err != TPE_OK:
    #     return err
    # if 0 == len(s.recorder):
    #     return TPE_OK
    # for i in s.recorder:
    #     _accs[i.id] = i

    # 加载所有的组
    err = s.reset().select_from('group', ['id', 'type', 'state'], alt_name='g').query()
    if err != TPE_OK:
        return err
    for i in s.recorder:
        _groups[i.id] = i
        if i.type == TP_GROUP_USER:
            _gusers[i.id] = []
        elif i.type == TP_GROUP_HOST:
            _ghosts[i.id] = []
            # elif i.type == TP_GROUP_ACCOUNT:
            #     _gaccs[i.id] = []

    # 加载所有的组
    err = s.reset().select_from('group_map', ['id', 'type', 'gid', 'mid'], alt_name='g').query()
    if err != TPE_OK:
        return err
    for g in s.recorder:
        if g.type == TP_GROUP_USER:
            # if g.gid not in _gusers:
            #     _gusers[g.gid] = []
            _gusers[g.gid].append(_users[g.mid])
        elif g.type == TP_GROUP_HOST:
            # if g.gid not in _ghosts:
            #     _ghosts[g.gid] = []
            _ghosts[g.gid].append(_hosts[g.mid])
            # elif g.type == TP_GROUP_ACCOUNT:
            #     # if g.gid not in _gaccs:
            #     #     _gaccs[g.gid] = []
            #     _gaccs[g.gid].append(_accs[g.mid])

    # 加载所有策略明细
    err = s.reset().select_from('audit_auz', ['id', 'policy_id', 'type', 'rtype', 'rid'], alt_name='o').query()
    if err != TPE_OK:
        return err
    if 0 == len(s.recorder):
        return TPE_OK

    # 分解各个策略中操作者和被操作资产的信息
    for i in s.recorder:
        if i.type == TP_POLICY_OPERATOR:

            if i.policy_id not in _p_users:
                _p_users[i.policy_id] = []

            if i.rtype == TP_USER:
                u = _users[i.rid]
                _p_users[i.policy_id].append({
                    'u_id': i.rid,
                    'u_state': u.state,
                    'gu_id': 0,
                    'gu_state': 0,
                    'u_name': u.username,
                    'u_surname': u.surname,
                    'auth_from_': 'USER'
                })
            elif i.rtype == TP_GROUP_USER:
                for u in _gusers[i.rid]:
                    _p_users[i.policy_id].append({
                        'u_id': u.id,
                        'u_state': u.state,
                        'gu_id': i.rid,
                        'gu_state': _groups[i.rid].state,
                        'u_name': u.username,
                        'u_surname': u.surname,
                        'auth_from_': 'gUSER'
                    })
            else:
                log.e('invalid operator type.\n')
                return TPE_FAILED

        elif i.type == TP_POLICY_ASSET:

            if i.policy_id not in _p_assets:
                _p_assets[i.policy_id] = []

            # if i.rtype == TP_ACCOUNT:
            #     a = _accs[i.rid]
            #     h = _hosts[a.host_id]
            #     _p_assets[i.policy_id].append({
            #         'a_id': i.rid,
            #         'a_state': a.state,
            #         'ga_id': 0,
            #         'ga_state': 0,
            #         'h_id': h.id,
            #         'h_state': h.state,
            #         'gh_id': 0,
            #         'gh_state': 0,
            #         'a_name': a.username,
            #         'protocol_type': a.protocol_type,
            #         'protocol_port': a.protocol_port,
            #         'h_name': h.name,
            #         'ip': h.ip,
            #         'router_ip': h.router_ip,
            #         'router_port': h.router_port,
            #         'auth_to_': 'ACC'
            #     })
            # elif i.rtype == TP_GROUP_ACCOUNT:
            #     for a in _gaccs[i.rid]:
            #         h = _hosts[a.host_id]
            #         _p_assets[i.policy_id].append({
            #             'a_id': a.id,
            #             'a_state': a.state,
            #             'ga_id': i.rid,
            #             'ga_state': _groups[i.rid].state,
            #             'h_id': h.id,
            #             'h_state': h.state,
            #             'gh_id': 0,
            #             'gh_state': 0,
            #             'a_name': a.username,
            #             'protocol_type': a.protocol_type,
            #             'protocol_port': a.protocol_port,
            #             'h_name': h.name,
            #             'ip': h.ip,
            #             'router_ip': h.router_ip,
            #             'router_port': h.router_port,
            #             'auth_to_': 'gACC'
            #         })
            # el
            if i.rtype == TP_HOST:
                # for aid in _accs:
                #     if _accs[aid].host_id == i.rid:
                #         a = _accs[aid]
                h = _hosts[i.rid]
                _p_assets[i.policy_id].append({
                    # 'a_id': aid,
                    # 'a_state': a.state,
                    # 'ga_id': 0,
                    # 'ga_state': 0,
                    'h_id': h.id,
                    # 'h_state': h.state,
                    'gh_id': 0,
                    # 'gh_state': 0,
                    # 'a_name': a.username,
                    # 'protocol_type': h.protocol_type,
                    # 'protocol_port': h.protocol_port,
                    'h_name': h.name,
                    'ip': h.ip,
                    'router_ip': h.router_ip,
                    'router_port': h.router_port,
                    'auth_to_': 'HOST'
                })
            elif i.rtype == TP_GROUP_HOST:
                for h in _ghosts[i.rid]:
                    # for aid in _accs:
                    #     if _accs[aid].host_id == h.id:
                    #         a = _accs[aid]
                    _p_assets[i.policy_id].append({
                        # 'a_id': aid,
                        # 'a_state': a.state,
                        'ga_id': 0,
                        'ga_state': 0,
                        'h_id': h.id,
                        # 'h_state': h.state,
                        'gh_id': i.rid,
                        # 'gh_state': _groups[i.rid].state,
                        # 'a_name': a.username,
                        # 'protocol_type': a.protocol_type,
                        # 'protocol_port': a.protocol_port,
                        'h_name': h.name,
                        'ip': h.ip,
                        'router_ip': h.router_ip,
                        'router_port': h.router_port,
                        'auth_to_': 'gHOST'
                    })
            else:
                log.e('invalid asset type.\n')
                return TPE_FAILED

        else:
            return TPE_FAILED

    # 3. 建立所有一一对应的映射关系
    for pid in _policies:
        if pid not in _p_users:
            continue
        for u in _p_users[pid]:
            if pid not in _p_assets:
                continue
            for a in _p_assets[pid]:
                x = AttrDict()
                x.update({
                    'p_id': pid,
                    'p_rank': _policies[pid].rank,
                    'p_state': _policies[pid].state
                })
                x.update(u)
                x.update(a)

                x.uni_id = '{}-{}-{}-{}-{}'.format(x.p_id, x.gu_id, x.u_id, x.gh_id, x.h_id)
                x.uh_id = 'u{}-h{}'.format(x.u_id, x.h_id)

                x.policy_auth_type = TP_POLICY_AUTH_UNKNOWN
                # if u['auth_from_'] == 'USER' and a['auth_to_'] == 'ACC':
                #     x.policy_auth_type = TP_POLICY_AUTH_USER_ACC
                # elif u['auth_from_'] == 'USER' and a['auth_to_'] == 'gACC':
                #     x.policy_auth_type = TP_POLICY_AUTH_USER_gACC
                # el
                if u['auth_from_'] == 'USER' and a['auth_to_'] == 'HOST':
                    x.policy_auth_type = TP_POLICY_AUTH_USER_HOST
                elif u['auth_from_'] == 'USER' and a['auth_to_'] == 'gHOST':
                    x.policy_auth_type = TP_POLICY_AUTH_USER_gHOST
                # elif u['auth_from_'] == 'gUSER' and a['auth_to_'] == 'ACC':
                #     x.policy_auth_type = TP_POLICY_AUTH_gUSER_ACC
                # elif u['auth_from_'] == 'gUSER' and a['auth_to_'] == 'gACC':
                #     x.policy_auth_type = TP_POLICY_AUTH_gUSER_gACC
                elif u['auth_from_'] == 'gUSER' and a['auth_to_'] == 'HOST':
                    x.policy_auth_type = TP_POLICY_AUTH_gUSER_HOST
                elif u['auth_from_'] == 'gUSER' and a['auth_to_'] == 'gHOST':
                    x.policy_auth_type = TP_POLICY_AUTH_gUSER_gHOST
                else:
                    log.w('invalid policy data.\n')
                    continue

                _map.append(x)

    if len(_map) == 0:
        return TPE_OK

    values = []
    for i in _map:
        v = '("{uni_id}","{uh_id}",{p_id},{p_rank},{p_state},{policy_auth_type},{u_id},{u_state},{gu_id},{gu_state},{h_id},{gh_id},' \
            '"{u_name}","{u_surname}","{h_name}","{ip}","{router_ip}",{router_port})' \
            ''.format(uni_id=i.uni_id, uh_id=i.uh_id, p_id=i.p_id, p_rank=i.p_rank, p_state=i.p_state, policy_auth_type=i.policy_auth_type,
                      u_id=i.u_id, u_state=i.u_state, gu_id=i.gu_id, gu_state=i.gu_state, h_id=i.h_id,gh_id=i.gh_id,
                      u_name=i.u_name, u_surname=i.u_surname, h_name=i.h_name, ip=i.ip, router_ip=i.router_ip, router_port=i.router_port)
        values.append(v)

    sql = 'INSERT INTO `{dbtp}audit_map` (uni_id,uh_id,p_id,p_rank,p_state,policy_auth_type,u_id,u_state,gu_id,gu_state,h_id,gh_id,' \
          'u_name,u_surname,h_name,ip,router_ip,router_port) VALUES \n{values};' \
          ''.format(dbtp=dbtp, values=',\n'.join(values))

    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    return TPE_OK
