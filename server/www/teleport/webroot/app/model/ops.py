# -*- coding: utf-8 -*-

import json

from app.const import *
from app.base.logger import log
from app.base.db import get_db, SQL
from app.model import syslog
from app.model import policy
from app.base.utils import AttrDict, tp_timestamp_utc_now


def get_by_id(pid):
    s = SQL(get_db())
    s.select_from('ops_policy', ['id', 'name', 'desc', 'flag_record', 'flag_rdp', 'flag_ssh', 'flag_telnet'], alt_name='p')
    s.where('p.id={}'.format(pid))
    err = s.query()
    if err != TPE_OK:
        return err, {}

    # if len(s.recorder) == 0:
    #     return TPE_NOT_EXISTS, {}

    return TPE_OK, s.recorder[0]


def get_policies(sql_filter, sql_order, sql_limit):
    dbtp = get_db().table_prefix
    s = SQL(get_db())
    s.select_from('ops_policy', ['id', 'rank', 'name', 'desc', 'state'], alt_name='p')

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
    # if sql_order is not None:
    #     _sort = False if not sql_order['asc'] else True
    #     if 'rank' == sql_order['name']:
    #         s.order_by('p.rank', _sort)
    #     elif 'name' == sql_order['name']:
    #         s.order_by('p.name', _sort)
    #     elif 'state' == sql_order['name']:
    #         s.order_by('p.state', _sort)
    #     else:
    #         log.e('unknown order field: {}\n'.format(sql_order['name']))
    #         return TPE_PARAM, s.total_count, 0, s.recorder

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
    err = s.reset().select_from('ops_policy', ['id']).where('ops_policy.name="{}"'.format(args['name'])).query()
    if err != TPE_OK:
        return err, 0
    if len(s.recorder) > 0:
        return TPE_EXISTS, 0

    # 2. get total count
    sql = 'SELECT COUNT(*) FROM {}ops_policy'.format(db.table_prefix)
    db_ret = db.query(sql)
    if not db_ret or len(db_ret) == 0:
        return TPE_DATABASE, 0
    rank = db_ret[0][0] + 1

    sql = 'INSERT INTO `{}ops_policy` (`rank`, `name`, `desc`, `creator_id`, `create_time`) VALUES ' \
          '({rank}, "{name}", "{desc}", {creator_id}, {create_time});' \
          ''.format(db.table_prefix,
                    rank=rank, name=args['name'], desc=args['desc'],
                    creator_id=handler.get_current_user()['id'],
                    create_time=_time_now)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE, 0

    _id = db.last_insert_id()

    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "创建运维授权策略：{}".format(args['name']))

    return TPE_OK, _id


def update_policy(handler, args):
    db = get_db()

    # 1. 判断此账号是否已经存在
    s = SQL(db)
    err = s.reset().select_from('ops_policy', ['id']).where('ops_policy.id={}'.format(args['id'])).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    sql = 'UPDATE `{}ops_policy` SET `name`="{name}", `desc`="{desc}" WHERE `id`={p_id};' \
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

    sql = 'UPDATE `{}ops_policy` SET `state`={state} WHERE `id` IN ({p_ids});'.format(db.table_prefix, state=state, p_ids=p_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}ops_auz` SET `state`={state} WHERE `policy_id` IN ({p_ids});'.format(db.table_prefix, state=state, p_ids=p_ids)
    sql_list.append(sql)

    sql = 'UPDATE `{}ops_map` SET `p_state`={state} WHERE `p_id` IN ({p_ids});'.format(db.table_prefix, state=state, p_ids=p_ids)
    sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


def remove_policies(handler, p_ids):
    db = get_db()

    p_ids = ','.join([str(i) for i in p_ids])

    sql_list = []

    sql = 'DELETE FROM `{}ops_policy` WHERE `id` IN ({p_ids});'.format(db.table_prefix, p_ids=p_ids)
    sql_list.append(sql)

    sql = 'DELETE FROM `{}ops_auz` WHERE `policy_id` IN ({p_ids});'.format(db.table_prefix, p_ids=p_ids)
    sql_list.append(sql)

    sql = 'DELETE FROM `{}ops_map` WHERE `p_id` IN ({p_ids});'.format(db.table_prefix, p_ids=p_ids)
    sql_list.append(sql)

    if db.transaction(sql_list):
        return TPE_OK
    else:
        return TPE_DATABASE


def add_members(handler, policy_id, policy_type, ref_type, members):
    # step 1: select exists rid.
    s = SQL(get_db())
    s.select_from('ops_auz', ['rid'], alt_name='p')
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
    for m in members:
        if m['id'] in exists_ids:
            continue
        str_sql = 'INSERT INTO `{}ops_auz` (policy_id, type, rtype, rid, `name`, creator_id, create_time) VALUES ' \
                  '({pid}, {t}, {rtype}, {rid}, "{name}", {creator_id}, {create_time});' \
                  ''.format(db.table_prefix,
                            pid=policy_id, t=policy_type, rtype=ref_type,
                            rid=m['id'], name=m['name'],
                            creator_id=operator['id'], create_time=_time_now)
        sql.append(str_sql)

    if db.transaction(sql):
        # return TPE_OK
        return policy.rebuild_ops_auz_map()
    else:
        return TPE_DATABASE


def remove_members(handler, policy_id, policy_type, ids):
    s = SQL(get_db())

    auz_ids = [str(i) for i in ids]

    # 将用户从所在组中移除
    where = 'policy_id={} AND type={} AND id IN ({})'.format(policy_id, policy_type, ','.join(auz_ids))
    err = s.reset().delete_from('ops_auz').where(where).exec()
    if err != TPE_OK:
        return err

    #return TPE_OK
    return policy.rebuild_ops_auz_map()


def set_flags(self, policy_id, flag_record, flag_rdp, flag_ssh):
    db = get_db()

    # 1. 判断此账号是否已经存在
    s = SQL(db)
    err = s.select_from('ops_policy', ['id']).where('ops_policy.id={}'.format(policy_id)).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    sql = 'UPDATE `{}ops_policy` SET flag_record={flag_record}, flag_rdp={flag_rdp}, flag_ssh={flag_ssh} WHERE id={p_id};' \
          ''.format(db.table_prefix,
                    flag_record=flag_record, flag_rdp=flag_rdp, flag_ssh=flag_ssh, p_id=policy_id
                    )
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    return TPE_OK


def get_operators(sql_filter, sql_order, sql_limit):
    ss = SQL(get_db())
    ss.select_from('ops_auz', ['id', 'policy_id', 'rtype', 'rid', 'name'], alt_name='p')

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

    #
    #
    # # step 1： get necessary reference id.
    # s = SQL(get_db())
    # s.select_from('ops_auz', ['id', 'policy_id', 'rtype', 'rid'], alt_name='p')
    #
    # # str_where = ''
    # _where = list()
    # _where.append('p.type=0')
    #
    # if len(sql_filter) > 0:
    #     for k in sql_filter:
    #         if k == 'policy_id':
    #             # _where.append('(p.name LIKE "%{filter}%" OR p.desc LIKE "%{filter}%")'.format(filter=sql_filter[k]))
    #             _where.append('p.policy_id={}'.format(sql_filter[k]))
    #         else:
    #             log.e('unknown filter field: {}\n'.format(k))
    #             return TPE_PARAM, s.total_count, 0, s.recorder
    #
    # if len(_where) > 0:
    #     # str_where = '( {} )'.format(' AND '.join(_where))
    #     s.where('( {} )'.format(' AND '.join(_where)))
    #
    # if sql_order is not None:
    #     _sort = False if not sql_order['asc'] else True
    #     if 'id' == sql_order['name']:
    #         s.order_by('p.id', _sort)
    #     elif 'rtype' == sql_order['name']:
    #         s.order_by('p.rtype', _sort)
    #     else:
    #         log.e('unknown order field: {}\n'.format(sql_order['name']))
    #         return TPE_PARAM, s.total_count, 0, s.recorder
    #
    # if len(sql_limit) > 0:
    #     s.limit(sql_limit['page_index'], sql_limit['per_page'])
    #
    # err = s.query()
    # if err != TPE_OK:
    #     return err, 0, 0, {}
    #
    # # step 2:
    # user_ids = []
    # user_group_ids = []
    # for i in s.recorder:
    #     if i['rtype'] == 1:
    #         user_ids.append(str(i['rid']))
    #     elif i['rtype'] == 2:
    #         user_group_ids.append(str(i['rid']))
    #
    # # step 3: query user's name
    # su = SQL(get_db())
    # if len(user_ids) > 0:
    #     su.select_from('user', ['id', 'auth_type', 'username', 'surname', 'role_id', 'state'], alt_name='u')
    #     su.left_join('role', ['name'], join_on='r.id=u.id', alt_name='r', out_map={'name': 'role'})
    #     su.where('u.id IN ({})'.format(','.join(user_ids)))
    #     err = su.query()
    #     if err != TPE_OK:
    #         return err, 0, 0, {}
    #     if len(su.recorder) != len(user_ids):
    #         return TPE_FAILED, 0, 0, {}
    #
    # # step 4: query user group name
    # sg = SQL(get_db())
    # if len(user_group_ids) > 0:
    #     sg.select_from('group', ['id', 'name'], alt_name='g')
    #     sg.where('g.type={} AND g.id IN ({})'.format(TP_GROUP_USER, ','.join(user_group_ids)))
    #     err = sg.query()
    #     if err != TPE_OK:
    #         return err, 0, 0, {}
    #     if len(sg.recorder) != len(user_group_ids):
    #         return TPE_FAILED, 0, 0, {}
    #
    # # step 5: generate final result.
    # for i in range(len(s.recorder)):
    #     if s.recorder[i]['rtype'] == 1:
    #         for x in su.recorder:
    #             if s.recorder[i]['rid'] == x['id']:
    #                 s.recorder[i]['name'] = x['username']
    #                 break
    #     elif s.recorder[i]['rtype'] == 2:
    #         for x in sg.recorder:
    #             if s.recorder[i]['rid'] == x['id']:
    #                 s.recorder[i]['name'] = x['name']
    #                 break
    #
    # return err, s.total_count, s.page_index, s.recorder


def get_asset(sql_filter, sql_order, sql_limit):
    ss = SQL(get_db())
    ss.select_from('ops_auz', ['id', 'policy_id', 'rtype', 'rid', 'name'], alt_name='p')

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
    err = s.select_from('ops_policy', ['id', 'name', 'rank']).where('ops_policy.id={}'.format(pid)).query()
    if err != TPE_OK:
        return err
    if len(s.recorder) == 0:
        return TPE_NOT_EXISTS

    p_name = s.recorder[0]['name']
    p_rank = s.recorder[0]['rank']

    # if p_rank > new_rank:
    #     compare = '>'
    #     if insert_before:
    #         compare = '>='
    #     sql = 'UPDATE `{dbtp}ops_policy` SET rank=rank+1 WHERE (rank{compare}{new_rank} AND rank<{p_rank});' \
    #           ''.format(dbtp=db.table_prefix, compare=compare, new_rank=new_rank, p_rank=p_rank)
    # else:
    #     compare = '<'
    #     if insert_before:
    #         compare = '<='
    #     sql = 'UPDATE `{dbtp}ops_policy` SET rank=rank-1 WHERE (rank{compare}{new_rank} AND rank>{p_rank});' \
    #           ''.format(dbtp=db.table_prefix, compare=compare, new_rank=new_rank, p_rank=p_rank)
    sql = 'UPDATE `{dbtp}ops_policy` SET rank=rank{direct} WHERE (rank>={start_rank} AND rank<={end_rank});' \
          ''.format(dbtp=db.table_prefix, direct=direct, start_rank=start_rank, end_rank=end_rank)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    sql = 'UPDATE `{dbtp}ops_policy` SET rank={new_rank} WHERE id={pid};' \
          ''.format(dbtp=db.table_prefix, new_rank=new_rank, pid=pid)
    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    syslog.sys_log(handler.get_current_user(), handler.request.remote_ip, TPE_OK, "调整运维授权策略顺序：{}，从{}到{}".format(p_name, p_rank, new_rank))

    return policy.rebuild_ops_auz_map()
    # return TPE_OK


def get_auth(auth_id):
    db = get_db()
    s = SQL(db)
    err = s.select_from('ops_map', ['id', 'p_id', 'h_id', 'u_id', 'a_id']).where('ops_map.uni_id="{}"'.format(auth_id)).query()
    if err != TPE_OK:
        return None, err
    if len(s.recorder) == 0:
        return None, TPE_NOT_EXISTS

    # if len(s.recorder) != 1:
    #     return None, TPE_FAILED

    # log.v(s.recorder[0])
    return s.recorder[0], TPE_OK


def get_all_remotes(handler, sql_filter, sql_order, sql_limit):
    s = SQL(get_db())
    s.select_from('host', ['id', 'name', 'ip', 'router_ip', 'router_port', 'state'], alt_name='h')

    str_where = ''
    _where = list()

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'state':
                _where.append('h.state={}'.format(sql_filter[k]))
            elif k == 'search':
                _where.append('(h.name LIKE "%{k}%" OR h.ip LIKE "%{k}%" OR h.router_ip LIKE "%{k}%")'.format(k=sql_filter[k]))
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
        if 'id' == sql_order['name']:
            s.order_by('h.id', _sort)
        elif 'ip' == sql_order['name']:
            s.order_by('h.ip', _sort)
        elif 'name' == sql_order['name']:
            s.order_by('h.name', _sort)
        else:
            log.e('unknown order field: {}\n'.format(sql_order['name']))
            return TPE_PARAM, s.total_count, s.page_index, s.recorder

    if len(sql_limit) > 0:
        s.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = s.query()
    if err != TPE_OK:
        return err, 0, 1, []

    ret = s.recorder
    for h in ret:
        h['h_id'] = h.id
        h['h_state'] = TP_STATE_NORMAL
        h['gh_state'] = TP_STATE_NORMAL
        h['h_name'] = h.name
        del h['id']
        del h['name']
        h['accounts_'] = []

        sa = SQL(get_db())
        sa.select_from('acc', ['id', 'protocol_type', 'protocol_port', 'username'], alt_name='a')
        sa.where('a.host_id={}'.format(h.h_id))
        sa.order_by('a.username', True)
        err = sa.query()
        if err != TPE_OK:
            continue
        for a in sa.recorder:
            h['accounts_'].append({
                'a_name': a.username,
                'id': a.id,
                'a_id': a.id,
                'policy_auth_type': TP_POLICY_AUTH_USER_ACC,
                'uni_id': 'none',
                'a_state': TP_STATE_NORMAL,
                'ga_state': TP_STATE_NORMAL,
                'protocol_type': a.protocol_type,
                'h_id': h.h_id,
                'policy_': {
                    'flag_ssh': TP_FLAG_ALL,
                    'flag_rdp': TP_FLAG_ALL
                }
            })

    # print(json.dumps(s.recorder, indent='  '))
    return err, s.total_count, s.page_index, s.recorder


def get_remotes(handler, sql_filter, sql_order, sql_limit):
    """
    获取当前登录用户的可以远程登录的主机（及账号）
    远程连接列表的显示策略：
     1. 运维权限：可以使用被授权的远程账号进行远程连接；
     2. 运维授权权限：可以使用所有的远程账号进行远程连接。

    步骤：
      1. 查询满足条件的项（用户->账号），按授权策略顺序排序
      2. 在此基础上选出非重复的（用户->账号）关系项
      3. 继续在上一步基础上选出非重复的主机项
      4. 为每一个主机查询满足条件的账号项
    """
    operator = handler.get_current_user()
    if (operator['privilege'] & TP_PRIVILEGE_OPS_AUZ) != 0:
        return get_all_remotes(handler, sql_filter, sql_order, sql_limit)

    db = get_db()

    ######################################################
    # step 1.
    ######################################################
    s1 = []
    s1.append('SELECT * FROM {}ops_map'.format(db.table_prefix))
    s1_where = []
    s1_where.append('u_id={}'.format(operator.id))
    s1_where.append('p_state={state}'.format(state=TP_STATE_NORMAL))
    s1.append('WHERE ({})'.format(') AND ('.join(s1_where)))
    s1.append('ORDER BY p_rank DESC')
    sql_1 = ' '.join(s1)

    ######################################################
    # step 2.
    ######################################################
    sql_2 = 'SELECT * FROM ({}) AS s1 GROUP BY ua_id'.format(sql_1)

    _f = ['id', 'p_id', 'h_id', 'h_state', 'gh_state', 'h_name', 'ip', 'router_ip', 'router_port']

    ######################################################
    # step 3.
    ######################################################
    _where = list()
    if len(sql_filter) > 0:
        for k in sql_filter:
            # if k == 'state':
            #     _where.append('h.state={}'.format(sql_filter[k]))
            # el
            if k == 'search':
                ss = SQL(get_db())
                ss.select_from('host', ['id'], alt_name='h')
                ss.where('(h.name LIKE "%{k}%" OR h.ip LIKE "%{k}%" OR h.router_ip LIKE "%{k}%")'.format(k=sql_filter[k]))
                err = ss.query()
                if err != TPE_OK:
                    return err, 0, 1, []
                if len(ss.recorder) == 0:
                    return TPE_OK, 0, 1, []
                h_list = ','.join([str(i['id']) for i in ss.recorder])
                _where.append('(h_id IN ({}))'.format(h_list))
            elif k == 'host_group':
                shg = SQL(get_db())
                shg.select_from('group_map', ['mid'], alt_name='g')
                shg.where('g.type={} AND g.gid={}'.format(TP_GROUP_HOST, sql_filter[k]))
                err = shg.query()
                if err != TPE_OK:
                    return err, 0, 1, []
                if len(shg.recorder) == 0:
                    return TPE_NOT_EXISTS, 0, 1, []
                h_list = ','.join([str(i['mid']) for i in shg.recorder])
                _where.append('(h_id IN ({}))'.format(h_list))

    str_where = ''
    if len(_where) > 0:
        str_where = 'WHERE ( {} )'.format(' AND '.join(_where))

    sql_counter = []
    sql_counter.append('SELECT COUNT(*)')
    sql_counter.append('FROM')
    sql_counter.append('({}) AS s3'.format(sql_2))
    sql_counter.append(str_where)
    sql_counter.append('GROUP BY h_id')
    sql_counter.append(';')

    db_ret = db.query(' '.join(sql_counter))
    if db_ret is None or len(db_ret) == 0:
        return TPE_OK, 0, 1, []

    total = len(db_ret)
    if total == 0:
        return TPE_OK, 0, 1, []

    if total < sql_limit['page_index'] * sql_limit['per_page']:
        sql_limit['page_index'] = 0

    sql = []
    sql.append('SELECT {}'.format(','.join(_f)))
    sql.append('FROM')
    sql.append('({}) AS s2'.format(sql_2))
    sql.append(str_where)
    sql.append('GROUP BY h_id')
    sql.append('ORDER BY ip')
    sql.append('LIMIT {},{}'.format(sql_limit['page_index'] * sql_limit['per_page'], sql_limit['per_page']))
    sql.append(';')

    ret_recorder = []  # 用于构建最终返回的数据
    h_ids = []  # 涉及到的主机的ID列表

    db_ret = db.query(' '.join(sql))
    if db_ret is None:
        return TPE_OK, 0, 1, []

    for db_item in db_ret:
        item = AttrDict()
        for i in range(len(_f)):
            item[_f[i]] = db_item[i]

        item.accounts_ = []
        ret_recorder.append(item)
        h_ids.append(item.h_id)

    ######################################################
    # step 4.
    ######################################################
    host_ids = [str(i) for i in h_ids]
    s4 = []
    s4.append('SELECT * FROM {}ops_map'.format(db.table_prefix))
    s4_where = []
    s4_where.append('u_id={}'.format(operator.id))
    s4_where.append('p_state={state}'.format(state=TP_STATE_NORMAL))
    s4_where.append('h_id IN ({})'.format(','.join(host_ids)))
    s4.append('WHERE ({})'.format(') AND ('.join(s4_where)))
    s4.append('ORDER BY p_rank DESC')
    sql_4 = ' '.join(s4)

    sql = []
    _f = ['id', 'uni_id', 'policy_auth_type', 'p_id', 'h_id', 'a_id', 'a_state', 'ga_state', 'a_name', 'protocol_type']
    sql.append('SELECT {}'.format(','.join(_f)))
    sql.append('FROM')
    sql.append('({}) AS s4'.format(sql_4))
    sql.append('GROUP BY ua_id')
    sql.append(';')

    db_ret = db.query(' '.join(sql))
    if db_ret is None:
        return TPE_OK, 0, 1, []

    p_ids = []  # 涉及到的策略的ID列表

    for db_item in db_ret:
        item = AttrDict()
        for i in range(len(_f)):
            item[_f[i]] = db_item[i]

        if item.p_id not in p_ids:
            p_ids.append(item.p_id)

        for j in range(len(ret_recorder)):
            if ret_recorder[j].h_id == item.h_id:
                ret_recorder[j].accounts_.append(item)

    # 查询所有相关的授权策略的详细信息
    # print('p-ids:', p_ids)
    policy_ids = [str(i) for i in p_ids]
    _f = ['id', 'flag_rdp', 'flag_ssh']
    sql = []
    sql.append('SELECT {}'.format(','.join(_f)))
    sql.append('FROM {}ops_policy'.format(db.table_prefix))
    sql.append('WHERE id IN ({})'.format(','.join(policy_ids)))
    sql.append(';')
    db_ret = db.query(' '.join(sql))
    # print('', db_ret)
    for db_item in db_ret:
        item = AttrDict()
        for i in range(len(_f)):
            item[_f[i]] = db_item[i]

        for i in range(len(ret_recorder)):
            for j in range(len(ret_recorder[i].accounts_)):
                if ret_recorder[i].accounts_[j].p_id == item.id:
                    ret_recorder[i].accounts_[j].policy_ = item

    # print(json.dumps(ret_recorder, indent='  '))
    return TPE_OK, total, sql_limit['page_index'], ret_recorder


def build_auz_map():
    _users = {}
    _hosts = {}
    _accs = {}
    _gusers = {}
    _ghosts = {}
    _gaccs = {}
    _groups = {}
    _policies = {}

    _p_users = {}
    _p_assets = {}

    _map = []

    db = get_db()
    dbtp = db.table_prefix
    db.exec('DELETE FROM {}ops_map'.format(dbtp))

    s = SQL(get_db())

    # 加载所有策略
    err = s.reset().select_from('ops_policy', ['id', 'rank', 'state'], alt_name='p').query()
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

    # 加载所有的账号
    err = s.reset().select_from('acc', ['id', 'host_id', 'username', 'protocol_type', 'protocol_port', 'auth_type', 'state'], alt_name='a').query()
    if err != TPE_OK:
        return err
    if 0 == len(s.recorder):
        return TPE_OK
    for i in s.recorder:
        _accs[i.id] = i

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
        elif i.type == TP_GROUP_ACCOUNT:
            _gaccs[i.id] = []

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
        elif g.type == TP_GROUP_ACCOUNT:
            # if g.gid not in _gaccs:
            #     _gaccs[g.gid] = []
            _gaccs[g.gid].append(_accs[g.mid])

    # 加载所有策略明细
    err = s.reset().select_from('ops_auz', ['id', 'policy_id', 'type', 'rtype', 'rid'], alt_name='o').query()
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

            if i.rtype == TP_ACCOUNT:
                a = _accs[i.rid]
                h = _hosts[a.host_id]
                _p_assets[i.policy_id].append({
                    'a_id': i.rid,
                    'a_state': a.state,
                    'ga_id': 0,
                    'ga_state': 0,
                    'h_id': h.id,
                    'h_state': h.state,
                    'gh_id': 0,
                    'gh_state': 0,
                    'a_name': a.username,
                    'protocol_type': a.protocol_type,
                    'protocol_port': a.protocol_port,
                    'h_name': h.name,
                    'ip': h.ip,
                    'router_ip': h.router_ip,
                    'router_port': h.router_port,
                    'auth_to_': 'ACC'
                })
            elif i.rtype == TP_GROUP_ACCOUNT:
                for a in _gaccs[i.rid]:
                    h = _hosts[a.host_id]
                    _p_assets[i.policy_id].append({
                        'a_id': a.id,
                        'a_state': a.state,
                        'ga_id': i.rid,
                        'ga_state': _groups[i.rid].state,
                        'h_id': h.id,
                        'h_state': h.state,
                        'gh_id': 0,
                        'gh_state': 0,
                        'a_name': a.username,
                        'protocol_type': a.protocol_type,
                        'protocol_port': a.protocol_port,
                        'h_name': h.name,
                        'ip': h.ip,
                        'router_ip': h.router_ip,
                        'router_port': h.router_port,
                        'auth_to_': 'gACC'
                    })
            elif i.rtype == TP_HOST:
                for aid in _accs:
                    if _accs[aid].host_id == i.rid:
                        a = _accs[aid]
                        h = _hosts[i.rid]
                        _p_assets[i.policy_id].append({
                            'a_id': aid,
                            'a_state': a.state,
                            'ga_id': 0,
                            'ga_state': 0,
                            'h_id': h.id,
                            'h_state': h.state,
                            'gh_id': 0,
                            'gh_state': 0,
                            'a_name': a.username,
                            'protocol_type': a.protocol_type,
                            'protocol_port': a.protocol_port,
                            'h_name': h.name,
                            'ip': h.ip,
                            'router_ip': h.router_ip,
                            'router_port': h.router_port,
                            'auth_to_': 'HOST'
                        })
            elif i.rtype == TP_GROUP_HOST:
                for h in _ghosts[i.rid]:
                    for aid in _accs:
                        if _accs[aid].host_id == h.id:
                            a = _accs[aid]
                            _p_assets[i.policy_id].append({
                                'a_id': aid,
                                'a_state': a.state,
                                'ga_id': 0,
                                'ga_state': 0,
                                'h_id': h.id,
                                'h_state': h.state,
                                'gh_id': i.rid,
                                'gh_state': _groups[i.rid].state,
                                'a_name': a.username,
                                'protocol_type': a.protocol_type,
                                'protocol_port': a.protocol_port,
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

                x.uni_id = '{}-{}-{}-{}-{}-{}-{}'.format(x.p_id, x.gu_id, x.u_id, x.gh_id, x.h_id, x.ga_id, x.a_id)
                x.ua_id = 'u{}-a{}'.format(x.u_id, x.a_id)

                x.policy_auth_type = TP_POLICY_AUTH_UNKNOWN
                if u['auth_from_'] == 'USER' and a['auth_to_'] == 'ACC':
                    x.policy_auth_type = TP_POLICY_AUTH_USER_ACC
                elif u['auth_from_'] == 'USER' and a['auth_to_'] == 'gACC':
                    x.policy_auth_type = TP_POLICY_AUTH_USER_gACC
                elif u['auth_from_'] == 'USER' and a['auth_to_'] == 'HOST':
                    x.policy_auth_type = TP_POLICY_AUTH_USER_HOST
                elif u['auth_from_'] == 'USER' and a['auth_to_'] == 'gHOST':
                    x.policy_auth_type = TP_POLICY_AUTH_USER_gHOST
                elif u['auth_from_'] == 'gUSER' and a['auth_to_'] == 'ACC':
                    x.policy_auth_type = TP_POLICY_AUTH_gUSER_ACC
                elif u['auth_from_'] == 'gUSER' and a['auth_to_'] == 'gACC':
                    x.policy_auth_type = TP_POLICY_AUTH_gUSER_gACC
                elif u['auth_from_'] == 'gUSER' and a['auth_to_'] == 'HOST':
                    x.policy_auth_type = TP_POLICY_AUTH_gUSER_HOST
                elif u['auth_from_'] == 'gUSER' and a['auth_to_'] == 'gHOST':
                    x.policy_auth_type = TP_POLICY_AUTH_gUSER_gHOST

                _map.append(x)

    if len(_map) == 0:
        return TPE_OK

    values = []
    for i in _map:
        v = '("{uni_id}","{ua_id}",{p_id},{p_rank},{p_state},{policy_auth_type},{u_id},{u_state},{gu_id},{gu_state},{h_id},{h_state},{gh_id},{gh_state},{a_id},{a_state},{ga_id},{ga_state},' \
            '"{u_name}","{u_surname}","{h_name}","{ip}","{router_ip}",{router_port},"{a_name}",{protocol_type},{protocol_port})' \
            ''.format(uni_id=i.uni_id, ua_id=i.ua_id, p_id=i.p_id, p_rank=i.p_rank, p_state=i.p_state, policy_auth_type=i.policy_auth_type,
                      u_id=i.u_id, u_state=i.u_state, gu_id=i.gu_id, gu_state=i.gu_state, h_id=i.h_id, h_state=i.h_state,
                      gh_id=i.gh_id, gh_state=i.gh_state, a_id=i.a_id, a_state=i.a_state, ga_id=i.ga_id, ga_state=i.ga_state,
                      u_name=i.u_name, u_surname=i.u_surname, h_name=i.h_name, ip=i.ip, router_ip=i.router_ip, router_port=i.router_port,
                      a_name=i.a_name, protocol_type=i.protocol_type, protocol_port=i.protocol_port)
        values.append(v)

    sql = 'INSERT INTO `{dbtp}ops_map` (uni_id,ua_id,p_id,p_rank,p_state,policy_auth_type,u_id,u_state,gu_id,gu_state,h_id,h_state,gh_id,gh_state,a_id,a_state,ga_id,ga_state,' \
          'u_name,u_surname,h_name,ip,router_ip,router_port,a_name,protocol_type,protocol_port) VALUES \n{values};' \
          ''.format(dbtp=dbtp, values=',\n'.join(values))

    db_ret = db.exec(sql)
    if not db_ret:
        return TPE_DATABASE

    return TPE_OK
