# -*- coding: utf-8 -*-

from app.const import *
from app.base.logger import log
from app.base.db import get_db, SQL
from app.model import syslog
from app.base.utils import AttrDict, tp_timestamp_utc_now


def rebuild_ops_auz_map():
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


def rebuild_audit_auz_map():
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


def rebuild_auz_map():
    ret = rebuild_ops_auz_map()
    if ret != TPE_OK:
        return ret
    return rebuild_audit_auz_map()

