# -*- coding: utf-8 -*-

import time
import csv
import os
import json
import threading
import tornado.gen
import tornado.httpclient

from eom_app.app.configs import app_cfg
from eom_app.app.util import *
from eom_app.module import host
from eom_common.eomcore.logger import *
from eom_app.app.session import web_session
from .base import TPBaseUserAuthHandler, TPBaseAdminAuthHandler, TPBaseUserAuthJsonHandler, TPBaseAdminAuthJsonHandler

cfg = app_cfg()

# 临时认证ID的基数，每次使用时均递减
tmp_auth_id_base = -1
tmp_auth_id_lock = threading.RLock()


class IndexHandler(TPBaseUserAuthHandler):
    def get(self):
        _user = self.get_session('user')
        if _user is None:
            return self.write(-1)

        param = dict()

        if cfg.core.detected:
            param['core'] = {
                'ssh_port': cfg.core.ssh.port,
                'rdp_port': cfg.core.rdp.port,
                'telnet_port': cfg.core.telnet.port
            }
        else:
            param['core'] = {
                'ssh_port': 0,
                'rdp_port': 0,
                'telnet_port': 0
            }

        param['group_list'] = host.get_group_list()

        if _user['type'] >= 100:
            param['cert_list'] = host.get_cert_list()
            self.render('host/admin_index.mako', page_param=json.dumps(param))
        else:
            self.render('host/user_index.mako', page_param=json.dumps(param))


class UploadAndImportHandler(TPBaseAdminAuthHandler):
    # TODO: 导入操作可能会比较耗时，应该分离导入和获取导入状态两个过程，在页面上可以呈现导入进度，并列出导出成功/失败的项

    @tornado.gen.coroutine
    def post(self):
        """
        csv导入规则：
        每一行的数据格式：  分组ID,操作系统,IP地址,端口,系统用户,系统密码,协议,密钥ID,状态,认证类型,描述
        因为主机的唯一性在于 `IP地址 + 端口`，且允许一个 `IP地址 + 端口` 对应多个系统用户，因此，每一行的数据几乎没有限制。
        在导入时：
          1. 对每一个第一次遇到的 `IP地址 + 端口` 组合，就在 ts_host_info 表中加一个条目，并在 ts_auth_info 表中加入一个用户。
          2. 对于非第一次遇到的 `IP地址 + 端口` 组合，则仅仅在 ts_auth_info 表中加一个用户，不更改 ts_host_info 表中的现有数据。
          3. `IP地址 + 端口 + 用户` 的组合不能重复。
          4. 空行跳过，数据格式不正确的跳过。
        """
        ret = dict()
        ret['code'] = 0
        ret['message'] = ''
        ret['data'] = {}
        ret['data']['msg'] = list()  # 记录跳过的行（格式不正确，或者数据重复等）
        csv_filename = ''

        try:
            upload_path = os.path.join(cfg.data_path, 'tmp')  # 文件的暂存路径
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
                ret['code'] = -2
                ret['message'] = 'upload csv file is neither gbk nor utf8 encode.'
                return self.write(json.dumps(ret).encode('utf8'))

            with open(csv_filename, encoding=file_encode) as f:
                csv_reader = csv.reader(f)
                is_first_line = True
                for csv_recorder in csv_reader:
                    # 跳过第一行，那是格式说明
                    if is_first_line:
                        is_first_line = False
                        continue

                    # 空行则忽略
                    if len(csv_recorder) <= 1:
                        continue

                    # 格式错误则记录在案，然后继续
                    if len(csv_recorder) != 13:
                        ret['msg'].append({'reason': '格式错误', 'line': ', '.join(csv_recorder)})
                        continue

                    host_args = dict()
                    user_args = dict()
                    # 分组ID, 操作系统, IP地址, 端口, 协议, 状态, 描述, 系统用户, 系统密码, 是否加密,附加参数,  密钥ID, 认证类型

                    host_args['group_id'] = int(csv_recorder[0])
                    host_args['host_sys_type'] = int(csv_recorder[1])
                    host_args['host_ip'] = csv_recorder[2]
                    host_args['host_port'] = csv_recorder[3]
                    host_args['protocol'] = csv_recorder[4]
                    host_args['host_lock'] = csv_recorder[5]
                    host_args['host_desc'] = csv_recorder[6]
                    # 加入一个主机（如果已经存在，则直接返回已存在的条目的host_id）
                    host_id = host.add_host(host_args, must_not_exists=False)
                    if host_id < 0:
                        ret['msg'].append({'reason': '添加主机失败，操作数据库失败', 'line': ', '.join(csv_recorder)})
                        continue

                    user_args['host_id'] = host_id
                    user_args['user_name'] = csv_recorder[7]
                    user_pswd = csv_recorder[8]
                    is_encrypt = int(csv_recorder[9])
                    user_args['user_param'] = csv_recorder[10].replace('\\n', '\n')
                    user_args['cert_id'] = int(csv_recorder[11])
                    auth_mode = int(csv_recorder[12])
                    user_args['auth_mode'] = auth_mode
                    user_args['user_pswd'] = ''
                    if auth_mode == 0:
                        pass
                    elif auth_mode == 1:
                        try:
                            if is_encrypt == 0:
                                _yr = async_enc(user_pswd)
                                return_data = yield _yr
                                if return_data is None:
                                    ret['code'] = -3
                                    ret['message'] = 'can not encrypt by core server.'
                                    return self.write(json.dumps(ret).encode('utf8'))

                                if 'code' not in return_data or return_data['code'] != 0:
                                    ret['code'] = -4
                                    ret['message'] = 'invalid result from encrypt by core server.'
                                    return self.write(json.dumps(ret).encode('utf8'))

                                tmp_pswd = return_data['data']

                            else:
                                tmp_pswd = user_pswd

                            user_args['user_pswd'] = tmp_pswd

                        except:
                            log.e('can not encrypt user password.\n')
                            ret['code'] = -5
                            ret['message'] = '发生异常'
                            return self.write(json.dumps(ret).encode('utf8'))

                    elif auth_mode == 2:
                        pass
                    else:
                        ret['data']['msg'].append({'reason': '未知的认证模式', 'line': ', '.join(csv_recorder)})
                        log.e('auth_mode unknown\n')
                        continue

                    uid = host.sys_user_add(user_args)
                    if uid < 0:
                        if uid == -100:
                            ret['data']['msg'].append({'reason': '添加登录账号失败，账号已存在', 'line': ', '.join(csv_recorder)})
                        else:
                            ret['data']['msg'].append({'reason': '添加登录账号失败，操作数据库失败', 'line': ', '.join(csv_recorder)})

            ret['code'] = 0
            return self.write(json.dumps(ret).encode('utf8'))
        except:
            log.e('error\n')
            ret['code'] = -6
            ret['message'] = '发生异常.'
            return self.write(json.dumps(ret).encode('utf8'))

        finally:
            if os.path.exists(csv_filename):
                os.remove(csv_filename)


class GetListHandler(TPBaseUserAuthJsonHandler):
    def post(self):
        _user = self.get_current_user()
        if _user is None:
            return self.write_json(-1, '尚未登录')

        filter = dict()
        order = dict()
        order['name'] = 'host_id'
        order['asc'] = True
        limit = dict()
        limit['page_index'] = 0
        limit['per_page'] = 25

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)

            tmp = list()
            _filter = args['filter']
            for i in _filter:
                if i == 'host_sys_type' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'host_group' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'search':
                    _x = _filter[i].strip()
                    if len(_x) == 0:
                        tmp.append(i)
                    continue

            for i in tmp:
                del _filter[i]

            filter.update(_filter)

            _limit = args['limit']
            if _limit['page_index'] < 0:
                _limit['page_index'] = 0
            if _limit['per_page'] < 10:
                _limit['per_page'] = 10
            if _limit['per_page'] > 100:
                _limit['per_page'] = 100

            limit.update(_limit)

            _order = args['order']
            if _order is not None:
                order['name'] = _order['k']
                order['asc'] = _order['v']
        if _user['type'] == 100:
            _total, _hosts = host.get_all_host_info_list(filter, order, limit)
        else:
            filter['account_name'] = _user['name']
            _total, _hosts = host.get_host_info_list_by_user(filter, order, limit)

        ret = dict()
        ret['page_index'] = limit['page_index']
        ret['total'] = _total
        ret['data'] = _hosts
        self.write_json(0, data=ret)


class GetGrouplist(TPBaseUserAuthJsonHandler):
    def post(self):
        group_list = host.get_group_list()
        self.write_json(0, data=group_list)


class UpdateHandler(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        if 'host_id' not in args or 'kv' not in args:
            self.write_json(-2, '缺少必要参数')

        _ret = host.update(args['host_id'], args['kv'])

        if _ret:
            self.write_json(0)
        else:
            self.write_json(-3, '数据库操作失败')


class AddHost(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        try:
            ret = host.add_host(args)
            if ret > 0:
                return self.write_json(0)
            else:
                if ret == -100:
                    return self.write_json(-100, '')
                else:
                    return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
        except:
            log.e('add host failed.\n')
            return self.write_json(-3, '发生异常')


class LockHost(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        host_id = args['host_id']
        lock = args['lock']
        try:
            ret = host.lock_host(host_id, lock)
            if ret:
                return self.write_json(0)
            else:
                return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
        except:
            log.e('lock host failed.\n')
            return self.write_json(-3, '发生异常')


class DeleteHost(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        host_list = args['host_list']
        try:
            ret = host.delete_host(host_list)
            if ret:
                return self.write_json(0)
            else:
                return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
        except:
            log.e('delete host failed.\n')
            return self.write_json(-3, '发生异常')


class ExportHostHandler(TPBaseAdminAuthHandler):
    def get(self):
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=teleport-host-export.csv')

        order = dict()
        order['name'] = 'host_id'
        order['asc'] = True
        limit = dict()
        limit['page_index'] = 0
        limit['per_page'] = 999999
        _total, _hosts = host.get_all_host_info_list(dict(), order, limit, True)

        self.write("分组ID, 操作系统, IP地址, 端口, 协议, 状态, 描述, 系统用户, 系统密码, 是否加密, 附加参数, 密钥ID, 认证类型\n".encode('gbk'))

        try:

            for h in _hosts:
                auth_list = h['auth_list']
                # 分组ID, 操作系统, IP地址, 端口, 协议, 状态, 描述, 系统用户, 系统密码, 是否加密,附加参数, 密钥ID, 认证类型
                for j in auth_list:
                    row_string = ''
                    # row_string = str(h['host_id'])
                    # row_string += ','
                    row_string += str(h['group_id'])
                    row_string += ','
                    row_string += str(h['host_sys_type'])
                    row_string += ','
                    row_string += h['host_ip']
                    row_string += ','
                    row_string += str(h['host_port'])
                    row_string += ','
                    row_string += str(h['protocol'])
                    row_string += ','
                    row_string += str(h['host_lock'])
                    row_string += ','
                    row_string += h['host_desc']
                    row_string += ','

                    # row_string += str(j['host_auth_id'])
                    # row_string += ','
                    row_string += j['user_name']
                    row_string += ','
                    row_string += j['user_pswd']
                    row_string += ','
                    row_string += '1'
                    row_string += ','
                    user_param = j['user_param']
                    if len(user_param) > 0:
                        user_param = user_param.replace('\n', '\\n')
                        row_string += user_param
                    row_string += ','
                    row_string += str(j['cert_id'])
                    row_string += ','
                    row_string += str(j['auth_mode'])

                    self.write(row_string.encode('gbk'))
                    self.write('\n')

        except IndexError:
            self.write('**********************************************\n'.encode('gbk'))
            self.write('！！错误！！\n'.encode('gbk'))
            self.write('导出过程中发生了错误！！\n'.encode('gbk'))
            self.write('**********************************************\n'.encode('gbk'))
            log.e('')

        self.finish()


class GetCertList(TPBaseUserAuthJsonHandler):
    def post(self):
        _certs = host.get_cert_list()
        if _certs is None or len(_certs) == 0:
            return self.write_json(-1, '参数错误')
        else:
            return self.write_json(0, data=_certs)


class AddCert(TPBaseUserAuthJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        cert_pub = args['cert_pub']
        cert_pri = args['cert_pri']
        cert_name = args['cert_name']

        if len(cert_pri) == 0:
            return self.write_json(-2, '参数错误，数据不完整')

        _yr = async_enc(cert_pri)
        return_data = yield _yr
        if return_data is None:
            return self.write_json(-3, '调用核心服务加密失败')

        if 'code' not in return_data or return_data['code'] != 0:
            return self.write_json(-4, '核心服务加密返回错误')

        cert_pri = return_data['data']

        try:
            ret = host.add_cert(cert_pub, cert_pri, cert_name)
            if ret:
                return self.write_json(0)
            else:
                return self.write_json(-5, '数据库操作失败，errcode:{}'.format(ret))
        except:
            log.e('add cert failed.\n')
            return self.write_json(-6, '发生异常')


class DeleteCert(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        cert_id = args['cert_id']

        try:
            ret = host.delete_cert(cert_id)
            if ret:
                return self.write_json(0)
            else:
                if ret == -2:
                    return self.write_json(-2, '')
                else:
                    return self.write_json(-3, '数据库操作失败，errcode:{}'.format(ret))
        except:
            log.e('add cert failed.\n')
            return self.write_json(-4, '发生异常')


class UpdateCert(TPBaseUserAuthJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        cert_id = args['cert_id']
        cert_pub = args['cert_pub']
        cert_pri = args['cert_pri']
        cert_name = args['cert_name']

        if len(cert_pri) > 0:
            _yr = async_enc(cert_pri)
            return_data = yield _yr
            if return_data is None:
                return self.write_json(-2, '调用核心服务加密失败')

            if 'code' not in return_data or return_data['code'] != 0:
                return self.write_json(-3, '核心服务加密返回错误')

            cert_pri = return_data['data']

        try:
            ret = host.update_cert(cert_id, cert_pub, cert_pri, cert_name)
            if ret:
                return self.write_json(0)
            else:
                return self.write_json(-4, '数据库操作失败，errcode:{}'.format(ret))
        except:
            log.e('update cert failed.\n')
            return self.write_json(-5, '发生异常')


class AddGroup(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        group_name = args['group_name']
        try:
            ret = host.add_group(group_name)
            if ret:
                return self.write_json(0)
            else:
                return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
        except:
            log.e('add group failed.\n')
            return self.write_json(-3, '发生异常')


class UpdateGroup(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        group_id = args['group_id']
        group_name = args['group_name']
        try:
            ret = host.update_group(group_id, group_name)
            if ret:
                return self.write_json(0)
            else:
                return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
        except:
            log.e('update group failed.\n')
            return self.write_json(-3, '发生异常')


class DeleteGroup(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        group_id = args['group_id']
        try:
            ret = host.delete_group(group_id)
            if ret == 0:
                return self.write_json(0)
            else:
                if ret == -2:
                    return self.write_json(-2, '')
                else:
                    return self.write_json(-3, '数据库操作失败，errcode:{}'.format(ret))
        except:
            log.e('delete group failed.\n')
            return self.write_json(-4, '发生异常')


class AddHostToGroup(TPBaseUserAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        host_list = args['host_list']
        group_id = args['group_id']
        try:
            ret = host.add_host_to_group(host_list, group_id)
            if ret:
                self.write_json(0)
            else:
                return self.write_json(-2, '数据库操作失败，errcode:{}'.format(ret))
            return
        except:
            log.e('add host to group failed.\n')
            return self.write_json(-3, '发生异常')


class GetSessionId(TPBaseUserAuthJsonHandler):
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        if 'auth_id' not in args:
            return self.write_json(-1, '参数缺失')

        auth_id = args['auth_id']

        req = {'method': 'request_session', 'param': {'authid': auth_id}}
        _yr = async_post_http(req)
        return_data = yield _yr
        if return_data is None:
            return self.write_json(-2, '调用核心服务获取会话ID失败')

        if 'code' not in return_data:
            return self.write_json(-3, '核心服务获取会话ID时返回错误数据')

        _code = return_data['code']
        if _code != 0:
            return self.write_json(-4, '核心服务获取会话ID时返回错误 {}'.format(_code))

        try:
            session_id = return_data['data']['sid']
        except IndexError:
            return self.write_json(-5, '核心服务获取会话ID时返回错误数据')

        data = dict()
        data['session_id'] = session_id

        return self.write_json(0, data=data)


class AdminGetSessionId(TPBaseUserAuthJsonHandler):
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        if 'host_auth_id' not in args:
            return self.write_json(-1, '参数缺失')

        _host_auth_id = int(args['host_auth_id'])

        user = self.get_current_user()

        # host_auth_id 对应的是 ts_auth_info 表中的某个条目，含有具体的认证数据，因为管理员无需授权即可访问所有远程主机，因此
        # 直接给出 host_auth_id，且account直接指明是当前登录用户（其必然是管理员）

        tmp_auth_info = host.get_host_auth_info(_host_auth_id)
        if tmp_auth_info is None:
            return self.write_json(-2, '指定数据不存在')

        tmp_auth_info['account_lock'] = 0
        tmp_auth_info['account_name'] = user['name']

        with tmp_auth_id_lock:
            global tmp_auth_id_base
            tmp_auth_id_base -= 1
            auth_id = tmp_auth_id_base

        # 将这个临时认证信息放到session中备后续查找使用（10秒内有效）
        web_session().set('tmp-auth-info-{}'.format(auth_id), tmp_auth_info, 10)

        req = {'method': 'request_session', 'param': {'authid': auth_id}}
        _yr = async_post_http(req)
        return_data = yield _yr
        if return_data is None:
            return self.write_json(-3, '调用核心服务获取会话ID失败')

        if 'code' not in return_data:
            return self.write_json(-4, '核心服务获取会话ID时返回错误数据')

        _code = return_data['code']
        if _code != 0:
            return self.write_json(-5, '核心服务获取会话ID时返回错误 {}'.format(_code))

        try:
            session_id = return_data['data']['sid']
        except IndexError:
            return self.write_json(-5, '核心服务获取会话ID时返回错误数据')

        data = dict()
        data['session_id'] = session_id

        return self.write_json(0, data=data)


class AdminFastGetSessionId(TPBaseAdminAuthJsonHandler):
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        user = self.get_current_user()

        tmp_auth_info = dict()

        try:
            _host_auth_id = int(args['host_auth_id'])
            _user_pswd = args['user_pswd']
            _cert_id = int(args['cert_id'])

            tmp_auth_info['host_ip'] = args['host_ip']
            tmp_auth_info['host_port'] = int(args['host_port'])
            tmp_auth_info['sys_type'] = int(args['sys_type'])
            tmp_auth_info['protocol'] = int(args['protocol'])
            tmp_auth_info['user_name'] = args['user_name']
            tmp_auth_info['auth_mode'] = int(args['auth_mode'])
            tmp_auth_info['user_param'] = args['user_param']
            tmp_auth_info['encrypt'] = 1
            tmp_auth_info['account_lock'] = 0
            tmp_auth_info['account_name'] = user['name']
        except IndexError:
            return self.write_json(-2, '参数缺失')

        if tmp_auth_info['auth_mode'] == 1:
            if len(_user_pswd) == 0:  # 修改登录用户信息时可能不会修改密码，因此页面上可能不会传来密码，需要从数据库中直接读取
                h = host.get_host_auth_info(_host_auth_id)
                tmp_auth_info['user_auth'] = h['user_auth']
            else:  # 如果页面上修改了密码或者新建账号时设定了密码，那么需要先交给core服务进行加密
                req = {'method': 'enc', 'param': {'p': _user_pswd}}
                _yr = async_post_http(req)
                return_data = yield _yr
                if return_data is None:
                    return self.write_json(-3, '调用核心服务加密失败')
                if 'code' not in return_data or return_data['code'] != 0:
                    return self.write_json(-3, '核心服务加密返回错误')

                tmp_auth_info['user_auth'] = return_data['data']['c']

        elif tmp_auth_info['auth_mode'] == 2:
            tmp_auth_info['user_auth'] = host.get_cert_info(_cert_id)
            if tmp_auth_info['user_auth'] is None:
                self.write_json(-100, '指定私钥不存在')
                return
        elif tmp_auth_info['auth_mode'] == 0:
            tmp_auth_info['user_auth'] = ''
        else:
            self.write_json(-101, '认证类型未知')
            return

        with tmp_auth_id_lock:
            global tmp_auth_id_base
            tmp_auth_id_base -= 1
            auth_id = tmp_auth_id_base

        web_session().set('tmp-auth-info-{}'.format(auth_id), tmp_auth_info, 10)

        req = {'method': 'request_session', 'param': {'authid': auth_id}}
        _yr = async_post_http(req)
        return_data = yield _yr
        if return_data is None:
            return self.write_json(-3, '调用核心服务获取会话ID失败')

        if 'code' not in return_data:
            return self.write_json(-4, '核心服务获取会话ID时返回错误数据')

        _code = return_data['code']
        if _code != 0:
            return self.write_json(-5, '核心服务获取会话ID时返回错误 {}'.format(_code))

        try:
            session_id = return_data['data']['sid']
        except IndexError:
            return self.write_json(-5, '核心服务获取会话ID时返回错误数据')

        data = dict()
        data['session_id'] = session_id

        return self.write_json(0, data=data)


class SysUserList(TPBaseUserAuthJsonHandler):
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        try:
            host_id = args['host_id']
        except:
            return self.write_json(-1, '参数缺失')

        data = host.sys_user_list(host_id)
        return self.write_json(0, data=data)


class SysUserAdd(TPBaseUserAuthJsonHandler):
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        try:
            auth_mode = args['auth_mode']
            user_pswd = args['user_pswd']
            cert_id = args['cert_id']
        except:
            return self.write_json(-1, '参数缺失')

        if auth_mode == 1:
            if 0 == len(args['user_pswd']):
                return self.write_json(-2, '参数缺失')

            _yr = async_enc(user_pswd)
            return_data = yield _yr
            if return_data is None:
                return self.write_json(-3, '调用核心服务加密失败')

            if 'code' not in return_data or return_data['code'] != 0:
                return self.write_json(-3, '核心服务加密返回错误')

            args['user_pswd'] = return_data['data']

        user_id = host.sys_user_add(args)
        if user_id < 0:
            if user_id == -100:
                return self.write_json(user_id, '同名账户已经存在！')
            else:
                return self.write_json(user_id, '数据库操作失败！')

        return self.write_json(0)


class SysUserUpdate(TPBaseUserAuthJsonHandler):
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        if 'host_auth_id' not in args or 'kv' not in args:
            return self.write_json(-2, '参数缺失')

        kv = args['kv']
        if 'auth_mode' not in kv or 'user_pswd' not in kv or 'cert_id' not in kv:
            return self.write_json(-3, '参数缺失')

        auth_mode = kv['auth_mode']
        if 'user_pswd' in kv:
            user_pswd = kv['user_pswd']
            if 0 == len(user_pswd):
                args['kv'].pop('user_pswd')
                user_pswd = None
        else:
            user_pswd = None

        cert_id = kv['cert_id']
        if auth_mode == 1 and user_pswd is not None:
            _yr = async_enc(user_pswd)
            return_data = yield _yr
            if return_data is None:
                return self.write_json(-4, '调用核心服务加密失败')

            if 'code' not in return_data or return_data['code'] != 0:
                return self.write_json(-5, '核心服务加密返回错误')

            args['kv']['user_pswd'] = return_data['data']

        if host.sys_user_update(args['host_auth_id'], args['kv']):
            return self.write_json(0)

        return self.write_json(-6, '数据库操作失败')


class SysUserDelete(TPBaseUserAuthJsonHandler):
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        try:
            host_auth_id = args['host_auth_id']
        except IndexError:
            return self.write_json(-2, '参数缺失')

        if host.sys_user_delete(host_auth_id):
            return self.write_json(0)

        return self.write_json(-3, '数据库操作失败')
