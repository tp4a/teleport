# -*- coding: utf-8 -*-

import time
import csv
import os
import json
import codecs
import ipaddress
import tornado.gen
import tornado.httpclient

from app.base.configs import tp_cfg
from app.const import *
from app.model import host
from app.model import account
from app.model import group
from app.base.core_server import core_service_async_enc
from app.base.logger import *
from app.base.controller import TPBaseHandler, TPBaseJsonHandler


class HostListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_DELETE | TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return

        err, groups = group.get_host_groups_for_user(self.current_user['id'], self.current_user['privilege'])
        param = {
            'host_groups': groups
        }

        self.render('asset/host-list.mako', page_param=json.dumps(param))


class DoGetHostsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_DELETE | TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'id'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25
        sql_restrict = args['restrict'] if 'restrict' in args else {}
        sql_exclude = args['exclude'] if 'exclude' in args else {}

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                # if i == 'role' and _filter[i] == 0:
                #     tmp.append(i)
                #     continue
                if i == 'state' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'search':
                    _x = _filter[i].strip()
                    if len(_x) == 0:
                        tmp.append(i)
                    continue
                elif i == 'host_group':
                    if _filter[i] == -1:
                        tmp.append(i)
                    continue

            for i in tmp:
                del _filter[i]

            sql_filter.update(_filter)

            _limit = args['limit']
            if _limit['page_index'] < 0:
                _limit['page_index'] = 0
            if _limit['per_page'] < 10:
                _limit['per_page'] = 10
            if _limit['per_page'] > 100:
                _limit['per_page'] = 100

            sql_limit.update(_limit)

            _order = args['order']
            if _order is not None:
                sql_order['name'] = _order['k']
                sql_order['asc'] = _order['v']

        except:
            return self.write_json(TPE_PARAM)

        err, total_count, page_index, row_data = \
            host.get_hosts(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total_count
        ret['data'] = row_data
        self.write_json(err, data=ret)


class HostGroupListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return
        self.render('asset/host-group-list.mako')


class HostGroupInfoHandler(TPBaseHandler):
    def get(self, gid):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return
        gid = int(gid)
        err, groups = group.get_by_id(TP_GROUP_HOST, gid)
        if err == TPE_OK:
            param = {
                'group_id': gid,
                'group_name': groups['name'],
                'group_desc': groups['desc']
            }
        else:
            param = {
                'group_id': 0,
                'group_name': '',
                'group_desc': ''
            }

        self.render('asset/host-group-info.mako', page_param=json.dumps(param))


class DoImportHandler(TPBaseHandler):
    IDX_IP = 0
    IDX_OS = 1
    IDX_NAME = 2
    IDX_ROUTER_IP = 3
    IDX_ROUTER_PORT = 4
    IDX_IDC = 5
    IDX_USERNAME = 6
    IDX_PROTOCOL = 7
    IDX_PROTOCOL_PORT = 8
    IDX_AUTH = 9
    IDX_SECRET = 10
    IDX_USERNAME_PROMPT = 11
    IDX_PASSWORD_PROMPT = 12
    IDX_GROUP = 13
    IDX_DESC = 14

    @tornado.gen.coroutine
    def post(self):
        """
        csv导入规则：
        每一行的数据格式：
          主机IP,操作系统类型,名称,路由IP,路由端口,资产编号,账号,协议类型,协议端口,认证类型,密码或私钥,账号提示,密码提示,分组,描述
        在导入时：
          0. 以“#”作为行注释。
          1. 首先必须是主机数据，随后可以跟多个账号数据（直到遇到下一个主机数据行之前，账号会与上一个主机关联）。
          2. 一个主机或账号属于多个组，可以用“|”将组分隔，如果某个组并不存在，则会创建这个组。
          3. 空行跳过，数据格式不正确的跳过。
        """
        ret = dict()
        ret['code'] = TPE_OK
        ret['message'] = ''

        rv = self.check_privilege(
            TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_GROUP | TP_PRIVILEGE_USER_CREATE | TP_PRIVILEGE_USER_GROUP,
            need_process=False)
        if rv != TPE_OK:
            ret['code'] = rv
            if rv == TPE_NEED_LOGIN:
                ret['message'] = '需要登录！'
            elif rv == TPE_PRIVILEGE:
                ret['message'] = '权限不足！'
            else:
                ret['message'] = '未知错误！'
            return self.write(json.dumps(ret).encode('utf8'))

        # success = list()
        failed = list()
        group_failed = list()
        csv_filename = ''

        try:
            upload_path = os.path.join(tp_cfg().data_path, 'tmp')  # 文件的暂存路径
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)
            file_metas = self.request.files['csvfile']  # 提取表单中‘name’为‘file’的文件元数据
            for meta in file_metas:
                now = time.localtime(time.time())
                tmp_name = 'upload-{:04d}{:02d}{:02d}{:02d}{:02d}{:02d}.csv'.format(
                    now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
                csv_filename = os.path.join(upload_path, tmp_name)
                with open(csv_filename, 'wb') as f:
                    f.write(meta['body'])

            # file encode maybe utf8 or gbk... check it out.
            file_encode = None
            with codecs.open(csv_filename, 'r', encoding='gbk') as f:
                try:
                    f.readlines()
                    file_encode = 'gbk'
                except:
                    pass

            if file_encode is None:
                log.v('file `{}` is not gbk, try utf8\n'.format(csv_filename))
                with codecs.open(csv_filename, 'r', encoding='utf_8_sig') as f:
                    try:
                        f.readlines()
                        file_encode = 'utf_8_sig'
                    except:
                        pass

            if file_encode is None:
                os.remove(csv_filename)
                log.e('file `{}` unknown encode, neither GBK nor UTF8.\n'.format(csv_filename))
                ret['code'] = TPE_FAILED
                ret['message'] = '文件无法解码：不是GBK编码或者UTF8编码！'
                return self.write(json.dumps(ret).encode('utf8'))

            host_groups = dict()  # 解析出来的主机分组名称
            acc_groups = dict()  # 解析出来的账号分组名称
            hosts = dict()  # 解析出来的主机列表（其中包含对应的账号列表，是一个一对多的关系）

            # 解析csv文件
            with open(csv_filename, encoding=file_encode) as f:
                all_acc = []  # 用于检查是否有重复的账号被添加
                csv_reader = csv.reader(f)
                line = 0
                last_ip = None
                for csv_recorder in csv_reader:
                    line += 1

                    # 跳过空行和注释
                    if len(csv_recorder) == 0 or csv_recorder[0].strip().startswith('#'):
                        continue

                    # 格式错误则记录在案，然后继续
                    if len(csv_recorder) != 15:
                        failed.append({'line': line, 'error': '格式错误，字段数量不匹配。'})
                        continue

                    # check
                    _ip = csv_recorder[self.IDX_IP].strip()
                    _username = csv_recorder[self.IDX_USERNAME].strip()
                    if len(_ip) == 0 and len(_username) == 0:
                        failed.append({'line': line, 'error': '格式错误，需要IP或者账号。'})
                        continue

                    # 公用字段
                    _group = list()
                    for g in csv_recorder[self.IDX_GROUP].split('|'):
                        g = g.strip()
                        if len(g) > 0 and g not in _group:
                            _group.append(g)
                    _desc = csv_recorder[self.IDX_DESC].strip().replace("\\n", "\n")

                    if len(_ip) > 0:
                        last_ip = None

                        try:
                            ipaddress.ip_address(_ip)
                        except:
                            failed.append({'line': line, 'error': '格式错误，错误的主机IP地址。'})
                            continue

                        if _ip in hosts:
                            failed.append({'line': line, 'error': '主机重复。'})
                            continue

                        # 检查主机数据
                        _host_os = csv_recorder[self.IDX_OS].strip().upper()
                        if _host_os == 'WIN' or _host_os == 'WINDOWS':
                            _host_os = TP_OS_TYPE_WINDOWS
                        elif _host_os == 'LINUX':
                            _host_os = TP_OS_TYPE_LINUX
                        else:
                            failed.append({'line': line, 'error': '格式错误，错误的主机操作系统类型。'})
                            continue

                        _router_ip = csv_recorder[self.IDX_ROUTER_IP].strip()
                        _router_port = csv_recorder[self.IDX_ROUTER_PORT].strip()

                        if not (
                                (len(_router_ip) == 0 and len(_router_port) == 0)
                                or (len(_router_ip) > 0 and len(_router_port) > 0)
                        ):
                            failed.append({'line': line, 'error': '格式错误，错误的路由IP及端口的组合。'})
                            continue
                        if len(_router_ip) > 0:
                            try:
                                ipaddress.ip_address(_ip)
                            except:
                                failed.append({'line': line, 'error': '格式错误，错误的路由IP地址。'})
                                continue
                            try:
                                _router_port = int(_router_port)
                            except:
                                failed.append({'line': line, 'error': '格式错误，错误的路由端口。'})
                                continue
                            if _router_port < 0 or _router_port > 65535:
                                failed.append({'line': line, 'error': '格式错误，错误的路由端口。'})
                                continue
                        else:
                            _router_port = 0

                        _host = dict()
                        _host['_line'] = line
                        _host['ip'] = _ip
                        _host['os'] = _host_os
                        _host['name'] = csv_recorder[self.IDX_NAME].strip()
                        _host['router_ip'] = _router_ip
                        _host['router_port'] = _router_port
                        _host['cid'] = csv_recorder[self.IDX_IDC].strip()
                        _host['group'] = _group
                        _host['desc'] = _desc
                        _host['acc'] = list()

                        hosts[_ip] = _host

                        last_ip = _ip

                    else:
                        # account
                        if last_ip is None:
                            failed.append({'line': line, 'error': '无对应主机信息，跳过。'})
                            continue

                        _protocol = csv_recorder[self.IDX_PROTOCOL].strip().upper()
                        if _protocol == 'RDP':
                            _protocol = TP_PROTOCOL_TYPE_RDP
                        elif _protocol == 'SSH':
                            _protocol = TP_PROTOCOL_TYPE_SSH
                        elif _protocol == 'TELNET':
                            _protocol = TP_PROTOCOL_TYPE_TELNET
                        else:
                            failed.append({'line': line, 'error': '格式错误，错误的远程协议类型。'})
                            continue

                        _protocol_port = csv_recorder[self.IDX_PROTOCOL_PORT].strip()
                        if hosts[last_ip]['router_port'] == 0:
                            if len(_protocol_port) == 0:
                                failed.append({'line': line, 'error': '格式错误，需要填写远程协议端口。'})
                                continue
                            try:
                                _protocol_port = int(_protocol_port)
                            except:
                                failed.append({'line': line, 'error': '格式错误，远程协议端口应该是数字。'})
                                continue
                        else:
                            _protocol_port = 0

                        _auth = csv_recorder[self.IDX_AUTH].strip().upper()
                        if _auth == 'NO':
                            _auth = TP_AUTH_TYPE_NONE
                        elif _auth == 'PW':
                            _auth = TP_AUTH_TYPE_PASSWORD
                        elif _auth == 'KEY':
                            _auth = TP_AUTH_TYPE_PRIVATE_KEY
                        else:
                            failed.append({'line': line, 'error': '格式错误，错误的认证类型。'})
                            continue

                        _secret = csv_recorder[self.IDX_SECRET].strip()
                        if _auth != TP_AUTH_TYPE_NONE and len(_secret) == 0:
                            failed.append({'line': line, 'error': '格式错误，密码或私钥必须填写。'})
                            continue

                        _username_prompt = csv_recorder[self.IDX_USERNAME_PROMPT].strip()
                        _password_prompt = csv_recorder[self.IDX_PASSWORD_PROMPT].strip()
                        if _protocol != TP_PROTOCOL_TYPE_TELNET:
                            _username_prompt = ''
                            _password_prompt = ''

                        _acc_info = '{}-{}-{}'.format(last_ip, _username, _auth)
                        if _acc_info in all_acc:
                            failed.append({'line': line, 'error': '账号重复。'})
                            continue
                        all_acc.append(_acc_info)

                        _acc = dict()
                        _acc['_line'] = line
                        _acc['username'] = _username
                        _acc['protocol_type'] = _protocol
                        _acc['protocol_port'] = _protocol_port
                        _acc['auth_type'] = _auth
                        _acc['secret'] = _secret
                        _acc['username_prompt'] = _username_prompt
                        _acc['password_prompt'] = _password_prompt
                        _acc['group'] = _group
                        _acc['desc'] = _desc

                        hosts[last_ip]['acc'].append(_acc)

            if os.path.exists(csv_filename):
                os.remove(csv_filename)

            # 如果解析过程中发生问题，则不再继续
            if len(failed) > 0:
                ret['code'] = TPE_FAILED
                ret['message'] = '文件解析错误，请修改文件后重新上传！'
                ret['data'] = failed
                return self.write(json.dumps(ret).encode('utf8'))

            if len(hosts) == 0:
                ret['code'] = TPE_FAILED
                ret['message'] = '上传的 csv 文件中没有可用于导入的数据！'
                ret['data'] = failed
                return self.write(json.dumps(ret).encode('utf8'))

            # 对密码或私钥进行加密（需要连接到核心服务）
            for ip in hosts:
                for i in range(len(hosts[ip]['acc'])):
                    if len(hosts[ip]['acc'][i]['secret']) == 0:
                        continue
                    code, ret_data = yield core_service_async_enc(hosts[ip]['acc'][i]['secret'])
                    if code != TPE_OK:
                        ret['code'] = code
                        ret['message'] = '无法对密码或私钥加密。'
                        if code == TPE_NO_CORE_SERVER:
                            ret['message'] += '可能核心服务尚未启动。'
                        ret['data'] = failed
                        return self.write(json.dumps(ret).encode('utf8'))
                    hosts[ip]['acc'][i]['secret'] = ret_data

            # 分析要创建的主机分组和账号分组
            for ip in hosts:
                for g in hosts[ip]['group']:
                    if g not in host_groups:
                        host_groups[g] = 0
                for i in range(len(hosts[ip]['acc'])):
                    for g in hosts[ip]['acc'][i]['group']:
                        if g not in acc_groups:
                            acc_groups[g] = 0

            # 已经有了用户组列表，查询组数据库，有则更新用户组列表中组对应的id，无则创建组
            if len(host_groups) > 0:
                err = group.make_groups(self, TP_GROUP_HOST, host_groups, group_failed)
                if len(group_failed) > 0:
                    ret['code'] = TPE_FAILED
                    ret['message'] += '无法创建主机组 {}。'.format('，'.join(group_failed))
                    return self.write(json.dumps(ret).encode('utf8'))

            if len(acc_groups) > 0:
                err = group.make_groups(self, TP_GROUP_ACCOUNT, acc_groups, group_failed)
                if len(group_failed) > 0:
                    ret['code'] = TPE_FAILED
                    ret['message'] += '无法创建账号组 {}。'.format('，'.join(group_failed))
                    return self.write(json.dumps(ret).encode('utf8'))

            # 创建主机和账号
            for ip in hosts:
                # router_addr = ''
                # if hosts[ip]['router_port'] > 0:
                #     router_addr = '{}:{}'.format(hosts[ip]['router_ip'], hosts[ip]['router_port'])

                args = dict()
                args['ip'] = ip
                args['router_ip'] = hosts[ip]['router_ip']
                args['router_port'] = hosts[ip]['router_port']
                args['os_type'] = hosts[ip]['os']
                args['name'] = hosts[ip]['name']
                args['cid'] = hosts[ip]['cid']
                args['desc'] = hosts[ip]['desc']
                err, host_id = host.add_host(self, args)
                if err != TPE_OK:
                    hosts[ip]['host_id'] = 0
                    if err == TPE_EXISTS:
                        failed.append({'line': hosts[ip]['_line'], 'error': '增加主机{}失败，此主机已经存在。'.format(ip)})
                    else:
                        failed.append({'line': hosts[ip]['_line'], 'error': '增加主机{}失败，数据库操作失败。'.format(ip)})
                    continue
                hosts[ip]['host_id'] = host_id

                for i in range(len(hosts[ip]['acc'])):
                    args = dict()
                    args['host_ip'] = ip
                    args['router_ip'] = hosts[ip]['router_ip']
                    args['router_port'] = hosts[ip]['router_port']
                    # args['host_router_addr'] = router_addr
                    args['host_id'] = host_id
                    args['protocol_type'] = hosts[ip]['acc'][i]['protocol_type']
                    args['protocol_port'] = hosts[ip]['acc'][i]['protocol_port']
                    args['auth_type'] = hosts[ip]['acc'][i]['auth_type']
                    args['username'] = hosts[ip]['acc'][i]['username']
                    args['password'] = ''
                    args['pri_key'] = ''
                    if args['auth_type'] == TP_AUTH_TYPE_PASSWORD:
                        args['password'] = hosts[ip]['acc'][i]['secret']
                    elif args['auth_type'] == TP_AUTH_TYPE_PRIVATE_KEY:
                        args['pri_key'] = hosts[ip]['acc'][i]['secret']

                    args['username_prompt'] = _acc['username_prompt']
                    args['password_prompt'] = _acc['password_prompt']

                    err, acc_id = account.add_account(self, host_id, args)
                    if err == TPE_EXISTS:
                        failed.append({
                            'line': hosts[ip]['acc']['_line'],
                            'error': '增加账号{}@{}失败，账号已经存在。'.format(args['username'], ip)
                        })
                        continue
                    elif err != TPE_OK:
                        failed.append({
                            'line': hosts[ip]['acc']['_line'],
                            'error': '增加账号{}@{}失败，数据库操作失败。'.format(args['username'], ip)
                        })

                    hosts[ip]['acc'][i]['acc_id'] = acc_id

            # 没毛病，那就创建组和成员的映射关系
            for ip in hosts:
                if hosts[ip]['host_id'] == 0:
                    continue

                gm = list()
                for hg in hosts[ip]['group']:
                    for g in host_groups:
                        if host_groups[g] == 0 or hg != g:
                            continue
                        gm.append({'type': 2, 'gid': host_groups[g], 'mid': hosts[ip]['host_id']})

                group.make_group_map(TP_GROUP_HOST, gm)

                for i in range(len(hosts[ip]['acc'])):
                    if hosts[ip]['acc'][i]['acc_id'] == 0:
                        continue

                    gm = list()
                    for ag in hosts[ip]['acc'][i]['group']:
                        for g in acc_groups:
                            if acc_groups[g] == 0 or ag != g:
                                continue
                            gm.append({'type': 3, 'gid': acc_groups[g], 'mid': hosts[ip]['acc'][i]['acc_id']})

                    group.make_group_map(TP_GROUP_ACCOUNT, gm)

            # ret['code'] = TPE_FAILED
            # ret['message'] = '-----------！'
            # ret['data'] = failed
            # return self.write(json.dumps(ret).encode('utf8'))

            #
            # # 对创建成功的用户，在用户组映射表中设定其对应关系
            # gm = list()
            # for u in user_list:
            #     if u['_id'] == 0:
            #         continue
            #     for ug in u['_group']:
            #         for g in group_list:
            #             if group_list[g] == 0 or ug != g:
            #                 continue
            #             gm.append({'type': 1, 'gid': group_list[g], 'mid': u['_id']})
            #
            # user.make_user_group_map(gm)
            #
            if len(failed) == 0:
                ret['code'] = TPE_OK
                # ret['message'] = '所有 {} 个用户账号均已导入！'.format(len(success))
                ret['message'] = '导入操作已成功结束！'
                return self.write(json.dumps(ret).encode('utf8'))
            else:
                ret['code'] = TPE_FAILED
                # if len(success) > 0:
                #     ret['message'] = '{} 个用户账号导入成功，'.format(len(success))
                ret['message'] = '部分主机和账号导入成功，'
                ret['message'] += '{} 个主机和账号未能导入！'.format(len(failed))

                ret['data'] = failed
                return self.write(json.dumps(ret).encode('utf8'))
        except:
            log.e('got exception when import host and account.\n')
            ret['code'] = TPE_FAILED
            # if len(success) > 0:
            #     ret['message'] += '{} 个用户账号导入后发生异常！'.format(len(success))
            # else:
            #     ret['message'] = '发生异常！'
            ret['message'] = '发生异常！'
            if len(failed) > 0:
                ret['data'] = failed
            return self.write(json.dumps(ret).encode('utf8'))


class DoUpdateHostHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_DELETE | TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            args['id'] = int(args['id'])
            args['os_type'] = int(args['os_type'])
            args['ip'] = args['ip'].strip()
            args['router_ip'] = args['router_ip']
            args['router_port'] = int(args['router_port'])
            args['name'] = args['name'].strip()
            args['cid'] = args['cid'].strip()
            args['desc'] = args['desc'].strip()
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if len(args['ip']) == 0:
            return self.write_json(TPE_PARAM)

        if args['id'] == -1:
            err, info = host.add_host(self, args)
        else:
            err = host.update_host(self, args)
            info = {}
        self.write_json(err, data=info)


class DoUpdateHostsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_DELETE)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            action = args['action']
            host_ids = args['hosts']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if len(host_ids) == 0:
            return self.write_json(TPE_PARAM)

        if action == 'lock':
            err = host.update_hosts_state(self, host_ids, TP_STATE_DISABLED)
            return self.write_json(err)
        elif action == 'unlock':
            err = host.update_hosts_state(self, host_ids, TP_STATE_NORMAL)
            return self.write_json(err)
        elif action == 'remove':
            err = host.remove_hosts(self, host_ids)
            return self.write_json(err)
        else:
            return self.write_json(TPE_PARAM)


class DoGetHostGroupWithMemberHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_GROUP)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'id'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                if i == 'search':
                    _x = _filter[i].strip()
                    if len(_x) == 0:
                        tmp.append(i)
                    continue

            for i in tmp:
                del _filter[i]

            sql_filter.update(_filter)

            _limit = args['limit']
            if _limit['page_index'] < 0:
                _limit['page_index'] = 0
            if _limit['per_page'] < 10:
                _limit['per_page'] = 10
            if _limit['per_page'] > 100:
                _limit['per_page'] = 100

            sql_limit.update(_limit)

            _order = args['order']
            if _order is not None:
                sql_order['name'] = _order['k']
                sql_order['asc'] = _order['v']

        except:
            return self.write_json(TPE_PARAM)

        err, total_count, row_data = host.get_group_with_member(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = sql_limit['page_index']
        ret['total'] = total_count
        ret['data'] = row_data
        self.write_json(err, data=ret)
