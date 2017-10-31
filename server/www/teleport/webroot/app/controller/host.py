# -*- coding: utf-8 -*-

import time
import csv
import os
import json
import ipaddress
import tornado.gen
import tornado.httpclient

from app.base.configs import get_cfg
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
        self.render('asset/host-list.mako')


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

        err, total_count, page_index, row_data = host.get_hosts(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude)
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
        每一行的数据格式：  操作系统类型,IP,名称,路由IP,路由端口,资产编号,协议类型,账号,认证类型,密码或私钥,账号提示,密码提示,分组,描述
        在导入时：
          0. 以“#”作为行注释。
          1. 首先必须是主机数据，随后可以跟多个账号数据（直到遇到下一个主机数据行之前，账号会与上一个主机关联）。
          2. 一个主机或账号属于多个组，可以用“|”将组分隔，如果某个组并不存在，则会创建这个组。
          3. 空行跳过，数据格式不正确的跳过。
        """
        ret = self.check_privilege(TP_PRIVILEGE_ASSET_CREATE | TP_PRIVILEGE_ASSET_GROUP | TP_PRIVILEGE_USER_CREATE | TP_PRIVILEGE_USER_GROUP)
        if ret != TPE_OK:
            return

        # success = list()
        failed = list()
        group_failed = list()

        ret = dict()
        ret['code'] = TPE_OK
        ret['message'] = ''
        csv_filename = ''

        try:
            upload_path = os.path.join(get_cfg().data_path, 'tmp')  # 文件的暂存路径
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)
            file_metas = self.request.files['csvfile']  # 提取表单中‘name’为‘file’的文件元数据
            for meta in file_metas:
                now = time.localtime(time.time())
                tmp_name = 'upload-{:04d}{:02d}{:02d}{:02d}{:02d}{:02d}.csv'.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
                csv_filename = os.path.join(upload_path, tmp_name)
                with open(csv_filename, 'wb') as f:
                    f.write(meta['body'])

            # file encode maybe utf8 or gbk... check it out.
            file_encode = None
            with open(csv_filename, encoding='gbk') as f:
                try:
                    f.readlines()
                    file_encode = 'gbk'
                except:
                    pass

            if file_encode is None:
                with open(csv_filename, encoding='utf8') as f:
                    try:
                        f.readlines()
                        file_encode = 'utf8'
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

                        if not ((len(_router_ip) == 0 and len(_router_port) == 0) or (len(_router_ip) > 0 and len(_router_port) > 0)):
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
                    failed.append({'line': 0, 'error': '增加主机{}失败，数据库操作失败。'.format(ip)})
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

                    err, acc_id = account.add_account(self, host_id, args)
                    if err != TPE_OK:
                        failed.append({'line': 0, 'error': '增加账号{}@{}失败，数据库操作失败。'.format(args['username'], ip)})
                        continue

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

        finally:
            if os.path.exists(csv_filename):
                os.remove(csv_filename)


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
            err = host.lock_hosts(self, host_ids)
            return self.write_json(err)
        elif action == 'unlock':
            err = host.unlock_hosts(self, host_ids)
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

# class UpdateHandler(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         if 'host_id' not in args or 'kv' not in args:
#             self.write_json(-2, '缺少必要参数')
#
#         _ret = host.update(args['host_id'], args['kv'])
#
#         if _ret:
#             self.write_json(0)
#         else:
#             self.write_json(-3, '数据库操作失败')
#
#

# class LockHost(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         host_id = args['host_id']
#         lock = args['lock']
#         try:
#             ret = host.lock_host(host_id, lock)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
#         except:
#             log.e('lock host failed.\n')
#             return self.write_json(-3, '发生异常')
#
#
# class DeleteHost(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         host_list = args['host_list']
#         try:
#             ret = host.delete_host(host_list)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
#         except:
#             log.e('delete host failed.\n')
#             return self.write_json(-3, '发生异常')
#
#
# class ExportHostHandler(TPBaseAdminAuthHandler):
#     def get(self):
#         self.set_header('Content-Type', 'application/octet-stream')
#         self.set_header('Content-Disposition', 'attachment; filename=teleport-host-export.csv')
#
#         order = dict()
#         order['name'] = 'host_id'
#         order['asc'] = True
#         limit = dict()
#         limit['page_index'] = 0
#         limit['per_page'] = 999999
#         _total, _hosts = host.get_all_host_info_list(dict(), order, limit, True)
#
#         self.write("分组ID, 操作系统, IP地址, 端口, 协议, 状态, 描述, 系统用户, 系统密码, 是否加密, 附加参数, 密钥ID, 认证类型\n".encode('gbk'))
#
#         try:
#
#             for h in _hosts:
#                 auth_list = h['auth_list']
#                 # 分组ID, 操作系统, IP地址, 端口, 协议, 状态, 描述, 系统用户, 系统密码, 是否加密,附加参数, 密钥ID, 认证类型
#                 for j in auth_list:
#                     row_string = ''
#                     # row_string = str(h['host_id'])
#                     # row_string += ','
#                     row_string += str(h['group_id'])
#                     row_string += ','
#                     row_string += str(h['host_sys_type'])
#                     row_string += ','
#                     row_string += h['host_ip']
#                     row_string += ','
#                     row_string += str(h['host_port'])
#                     row_string += ','
#                     row_string += str(h['protocol'])
#                     row_string += ','
#                     row_string += str(h['host_lock'])
#                     row_string += ','
#                     row_string += h['host_desc']
#                     row_string += ','
#
#                     # row_string += str(j['host_auth_id'])
#                     # row_string += ','
#                     row_string += j['user_name']
#                     row_string += ','
#                     row_string += j['user_pswd']
#                     row_string += ','
#                     row_string += '1'
#                     row_string += ','
#                     user_param = j['user_param']
#                     if len(user_param) > 0:
#                         user_param = user_param.replace('\n', '\\n')
#                         row_string += user_param
#                     row_string += ','
#                     row_string += str(j['cert_id'])
#                     row_string += ','
#                     row_string += str(j['auth_mode'])
#
#                     self.write(row_string.encode('gbk'))
#                     self.write('\n')
#
#         except IndexError:
#             self.write('**********************************************\n'.encode('gbk'))
#             self.write('！！错误！！\n'.encode('gbk'))
#             self.write('导出过程中发生了错误！！\n'.encode('gbk'))
#             self.write('**********************************************\n'.encode('gbk'))
#             log.e('')
#
#         self.finish()
#
#
# class GetCertList(TPBaseUserAuthJsonHandler):
#     def post(self):
#         _certs = host.get_cert_list()
#         if _certs is None or len(_certs) == 0:
#             return self.write_json(-1, '参数错误')
#         else:
#             return self.write_json(0, data=_certs)
#
#
# class AddCert(TPBaseUserAuthJsonHandler):
#     @tornado.gen.coroutine
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         cert_pub = args['cert_pub']
#         cert_pri = args['cert_pri']
#         cert_name = args['cert_name']
#
#         if len(cert_pri) == 0:
#             return self.write_json(-2, '参数错误，数据不完整')
#
#         _yr = async_enc(cert_pri)
#         return_data = yield _yr
#         if return_data is None:
#             return self.write_json(-3, '调用核心服务加密失败')
#
#         if 'code' not in return_data or return_data['code'] != 0:
#             return self.write_json(-4, '核心服务加密返回错误')
#
#         cert_pri = return_data['data']
#
#         try:
#             ret = host.add_cert(cert_pub, cert_pri, cert_name)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(-5, '数据库操作失败，errcode:{}'.format(ret))
#         except:
#             log.e('add cert failed.\n')
#             return self.write_json(-6, '发生异常')
#
#
# class DeleteCert(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         cert_id = args['cert_id']
#
#         try:
#             ret = host.delete_cert(cert_id)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 if ret == -2:
#                     return self.write_json(-2, '')
#                 else:
#                     return self.write_json(-3, '数据库操作失败，errcode:{}'.format(ret))
#         except:
#             log.e('add cert failed.\n')
#             return self.write_json(-4, '发生异常')
#
#
# class UpdateCert(TPBaseUserAuthJsonHandler):
#     @tornado.gen.coroutine
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         cert_id = args['cert_id']
#         cert_pub = args['cert_pub']
#         cert_pri = args['cert_pri']
#         cert_name = args['cert_name']
#
#         if len(cert_pri) > 0:
#             _yr = async_enc(cert_pri)
#             return_data = yield _yr
#             if return_data is None:
#                 return self.write_json(-2, '调用核心服务加密失败')
#
#             if 'code' not in return_data or return_data['code'] != 0:
#                 return self.write_json(-3, '核心服务加密返回错误')
#
#             cert_pri = return_data['data']
#
#         try:
#             ret = host.update_cert(cert_id, cert_pub, cert_pri, cert_name)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(-4, '数据库操作失败，errcode:{}'.format(ret))
#         except:
#             log.e('update cert failed.\n')
#             return self.write_json(-5, '发生异常')
#
#
# class AddGroup(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         group_name = args['group_name']
#         try:
#             ret = host.add_group(group_name)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
#         except:
#             log.e('add group failed.\n')
#             return self.write_json(-3, '发生异常')
#
#
# class UpdateGroup(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         group_id = args['group_id']
#         group_name = args['group_name']
#         try:
#             ret = host.update_group(group_id, group_name)
#             if ret:
#                 return self.write_json(0)
#             else:
#                 return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
#         except:
#             log.e('update group failed.\n')
#             return self.write_json(-3, '发生异常')
#
#
# class DeleteGroup(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         group_id = args['group_id']
#         try:
#             ret = host.delete_group(group_id)
#             if ret == 0:
#                 return self.write_json(0)
#             else:
#                 if ret == -2:
#                     return self.write_json(-2, '')
#                 else:
#                     return self.write_json(-3, '数据库操作失败，errcode:{}'.format(ret))
#         except:
#             log.e('delete group failed.\n')
#             return self.write_json(-4, '发生异常')
#
#
# class AddHostToGroup(TPBaseUserAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         host_list = args['host_list']
#         group_id = args['group_id']
#         try:
#             ret = host.add_host_to_group(host_list, group_id)
#             if ret:
#                 self.write_json(0)
#             else:
#                 return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
#             return
#         except:
#             log.e('add host to group failed.\n')
#             return self.write_json(-3, '发生异常')
#
#
# class GetSessionId(TPBaseUserAuthJsonHandler):
#     @tornado.gen.coroutine
#     def post(self, *args, **kwargs):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         if 'auth_id' not in args:
#             return self.write_json(-1, '参数缺失')
#
#         auth_id = args['auth_id']
#
#         req = {'method': 'request_session', 'param': {'authid': auth_id}}
#         _yr = async_post_http(req)
#         return_data = yield _yr
#         if return_data is None:
#             return self.write_json(-2, '调用核心服务获取会话ID失败')
#
#         if 'code' not in return_data:
#             return self.write_json(-3, '核心服务获取会话ID时返回错误数据')
#
#         _code = return_data['code']
#         if _code != 0:
#             return self.write_json(-4, '核心服务获取会话ID时返回错误 {}'.format(_code))
#
#         try:
#             session_id = return_data['data']['sid']
#         except IndexError:
#             return self.write_json(-5, '核心服务获取会话ID时返回错误数据')
#
#         data = dict()
#         data['session_id'] = session_id
#
#         return self.write_json(0, data=data)
#
#
# class AdminGetSessionId(TPBaseUserAuthJsonHandler):
#     @tornado.gen.coroutine
#     def post(self, *args, **kwargs):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         if 'host_auth_id' not in args:
#             return self.write_json(-1, '参数缺失')
#
#         _host_auth_id = int(args['host_auth_id'])
#
#         user = self.get_current_user()
#
#         # host_auth_id 对应的是 ts_auth_info 表中的某个条目，含有具体的认证数据，因为管理员无需授权即可访问所有远程主机，因此
#         # 直接给出 host_auth_id，且account直接指明是当前登录用户（其必然是管理员）
#
#         tmp_auth_info = host.get_host_auth_info(_host_auth_id)
#         if tmp_auth_info is None:
#             return self.write_json(-2, '指定数据不存在')
#
#         tmp_auth_info['account_lock'] = 0
#         tmp_auth_info['account_name'] = user['name']
#
#         with tmp_auth_id_lock:
#             global tmp_auth_id_base
#             tmp_auth_id_base -= 1
#             auth_id = tmp_auth_id_base
#
#         # 将这个临时认证信息放到session中备后续查找使用（10秒内有效）
#         session_manager().set('tmp-auth-info-{}'.format(auth_id), tmp_auth_info, 10)
#
#         req = {'method': 'request_session', 'param': {'authid': auth_id}}
#         _yr = async_post_http(req)
#         return_data = yield _yr
#         if return_data is None:
#             return self.write_json(-3, '调用核心服务获取会话ID失败')
#
#         if 'code' not in return_data:
#             return self.write_json(-4, '核心服务获取会话ID时返回错误数据')
#
#         _code = return_data['code']
#         if _code != 0:
#             return self.write_json(-5, '核心服务获取会话ID时返回错误 {}'.format(_code))
#
#         try:
#             session_id = return_data['data']['sid']
#         except IndexError:
#             return self.write_json(-5, '核心服务获取会话ID时返回错误数据')
#
#         data = dict()
#         data['session_id'] = session_id
#
#         return self.write_json(0, data=data)
#
#
# class AdminFastGetSessionId(TPBaseAdminAuthJsonHandler):
#     @tornado.gen.coroutine
#     def post(self, *args, **kwargs):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         user = self.get_current_user()
#
#         tmp_auth_info = dict()
#
#         try:
#             _host_auth_id = int(args['host_auth_id'])
#             _user_pswd = args['user_pswd']
#             _cert_id = int(args['cert_id'])
#
#             tmp_auth_info['host_ip'] = args['host_ip']
#             tmp_auth_info['host_port'] = int(args['host_port'])
#             tmp_auth_info['sys_type'] = int(args['sys_type'])
#             tmp_auth_info['protocol'] = int(args['protocol'])
#             tmp_auth_info['user_name'] = args['user_name']
#             tmp_auth_info['auth_mode'] = int(args['auth_mode'])
#             tmp_auth_info['user_param'] = args['user_param']
#             tmp_auth_info['encrypt'] = 1
#             tmp_auth_info['account_lock'] = 0
#             tmp_auth_info['account_name'] = user['name']
#         except IndexError:
#             return self.write_json(-2, '参数缺失')
#
#         if tmp_auth_info['auth_mode'] == 1:
#             if len(_user_pswd) == 0:  # 修改登录用户信息时可能不会修改密码，因此页面上可能不会传来密码，需要从数据库中直接读取
#                 h = host.get_host_auth_info(_host_auth_id)
#                 tmp_auth_info['user_auth'] = h['user_auth']
#             else:  # 如果页面上修改了密码或者新建账号时设定了密码，那么需要先交给core服务进行加密
#                 req = {'method': 'enc', 'param': {'p': _user_pswd}}
#                 _yr = async_post_http(req)
#                 return_data = yield _yr
#                 if return_data is None:
#                     return self.write_json(-3, '调用核心服务加密失败')
#                 if 'code' not in return_data or return_data['code'] != 0:
#                     return self.write_json(-3, '核心服务加密返回错误')
#
#                 tmp_auth_info['user_auth'] = return_data['data']['c']
#
#         elif tmp_auth_info['auth_mode'] == 2:
#             tmp_auth_info['user_auth'] = host.get_cert_info(_cert_id)
#             if tmp_auth_info['user_auth'] is None:
#                 self.write_json(-100, '指定私钥不存在')
#                 return
#         elif tmp_auth_info['auth_mode'] == 0:
#             tmp_auth_info['user_auth'] = ''
#         else:
#             self.write_json(-101, '认证类型未知')
#             return
#
#         with tmp_auth_id_lock:
#             global tmp_auth_id_base
#             tmp_auth_id_base -= 1
#             auth_id = tmp_auth_id_base
#
#         session_manager().set('tmp-auth-info-{}'.format(auth_id), tmp_auth_info, 10)
#
#         req = {'method': 'request_session', 'param': {'authid': auth_id}}
#         _yr = async_post_http(req)
#         return_data = yield _yr
#         if return_data is None:
#             return self.write_json(-3, '调用核心服务获取会话ID失败')
#
#         if 'code' not in return_data:
#             return self.write_json(-4, '核心服务获取会话ID时返回错误数据')
#
#         _code = return_data['code']
#         if _code != 0:
#             return self.write_json(-5, '核心服务获取会话ID时返回错误 {}'.format(_code))
#
#         try:
#             session_id = return_data['data']['sid']
#         except IndexError:
#             return self.write_json(-5, '核心服务获取会话ID时返回错误数据')
#
#         data = dict()
#         data['session_id'] = session_id
#
#         return self.write_json(0, data=data)
#
#
# class SysUserList(TPBaseUserAuthJsonHandler):
#     def post(self, *args, **kwargs):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         try:
#             host_id = args['host_id']
#         except:
#             return self.write_json(-1, '参数缺失')
#
#         data = host.sys_user_list(host_id)
#         return self.write_json(0, data=data)
#
#
# class SysUserAdd(TPBaseUserAuthJsonHandler):
#     @tornado.gen.coroutine
#     def post(self, *args, **kwargs):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         try:
#             auth_mode = args['auth_mode']
#             user_pswd = args['user_pswd']
#             cert_id = args['cert_id']
#         except:
#             return self.write_json(-1, '参数缺失')
#
#         if auth_mode == 1:
#             if 0 == len(args['user_pswd']):
#                 return self.write_json(-2, '参数缺失')
#
#             _yr = async_enc(user_pswd)
#             return_data = yield _yr
#             if return_data is None:
#                 return self.write_json(-3, '调用核心服务加密失败')
#
#             if 'code' not in return_data or return_data['code'] != 0:
#                 return self.write_json(-3, '核心服务加密返回错误')
#
#             args['user_pswd'] = return_data['data']
#
#         user_id = host.sys_user_add(args)
#         if user_id < 0:
#             if user_id == -100:
#                 return self.write_json(user_id, '同名账户已经存在！')
#             else:
#                 return self.write_json(user_id, '数据库操作失败！')
#
#         return self.write_json(0)
#
#
# class SysUserUpdate(TPBaseUserAuthJsonHandler):
#     @tornado.gen.coroutine
#     def post(self, *args, **kwargs):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         if 'host_auth_id' not in args or 'kv' not in args:
#             return self.write_json(-2, '参数缺失')
#
#         kv = args['kv']
#         if 'auth_mode' not in kv or 'user_pswd' not in kv or 'cert_id' not in kv:
#             return self.write_json(-3, '参数缺失')
#
#         auth_mode = kv['auth_mode']
#         if 'user_pswd' in kv:
#             user_pswd = kv['user_pswd']
#             if 0 == len(user_pswd):
#                 args['kv'].pop('user_pswd')
#                 user_pswd = None
#         else:
#             user_pswd = None
#
#         cert_id = kv['cert_id']
#         if auth_mode == 1 and user_pswd is not None:
#             _yr = async_enc(user_pswd)
#             return_data = yield _yr
#             if return_data is None:
#                 return self.write_json(-4, '调用核心服务加密失败')
#
#             if 'code' not in return_data or return_data['code'] != 0:
#                 return self.write_json(-5, '核心服务加密返回错误')
#
#             args['kv']['user_pswd'] = return_data['data']
#
#         if host.sys_user_update(args['host_auth_id'], args['kv']):
#             return self.write_json(0)
#
#         return self.write_json(-6, '数据库操作失败')
#
#
# class SysUserDelete(TPBaseUserAuthJsonHandler):
#     def post(self, *args, **kwargs):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         try:
#             host_auth_id = args['host_auth_id']
#         except IndexError:
#             return self.write_json(-2, '参数缺失')
#
#         if host.sys_user_delete(host_auth_id):
#             return self.write_json(0)
#
#         return self.write_json(-3, '数据库操作失败')
