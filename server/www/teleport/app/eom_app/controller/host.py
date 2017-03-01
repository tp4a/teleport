# -*- coding: utf-8 -*-

import time
import csv
import os
import urllib
import urllib.parse
import urllib.request

from eom_app.app.configs import app_cfg
from eom_app.module import set
from eom_app.module import host
from eom_app.module.common import *
from eom_common.eomcore.logger import *
from .base import SwxAuthHandler, SwxAuthJsonHandler

cfg = app_cfg()


class IndexHandler(SwxAuthHandler):
    def get(self):
        _user = self.get_session('user')
        if _user is None:
            return self.write(-1)

        # static_path = cfg.static_path
        # var_js = os.path.join(static_path, 'js', 'var.js')
        try:
            # f = open(var_js, 'w')
            _type = _user['type']
            config_list = set.get_config_list()
            ts_server = dict()
            # ts_server['ip'] = config_list['ts_server_ip']
            # ts_server['ip'] = cfg['ts_server_ip']
            # ts_server['ip'] = '0.0.0.0'

            # ts_server['ssh_port'] = config_list['ts_server_ssh_port']
            # ts_server['rdp_port'] = config_list['ts_server_rdp_port']
            # ts_server['telnet_port'] = config_list['ts_server_telnet_port']

            ts_server['ssh_port'] = cfg.core.ssh.port
            ts_server['rdp_port'] = cfg.core.rdp.port
            ts_server['telnet_port'] = cfg.core.telnet.port

            # f.write("\"use strict\";\nvar teleport_ip = \"{}\";\n".format(ts_server['ip']))
        except Exception as e:
            return self.write(-1)
        # finally:
        #     f.close()

        if _type >= 100:
            group_list = host.get_group_list()
            cert_list = host.get_cert_list()
            self.render('host/admin_index.mako',
                        group_list=group_list,
                        cert_list=cert_list,
                        ts_server=ts_server)
        else:
            group_list = host.get_group_list()

            if config_list is None:
                return

            self.render('host/common_index.mako',
                        group_list=group_list,
                        ts_server=ts_server)


class LoadFile(SwxAuthJsonHandler):
    def get(self):
        pass

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
        ret['msg'] = list()  # 记录跳过的行（格式不正确，或者数据重复等）
        csv_filename = ''

        try:
            upload_path = os.path.join(os.path.dirname(__file__), 'csv-files')  # 文件的暂存路径
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)
            file_metas = self.request.files['csvfile']  # 提取表单中‘name’为‘file’的文件元数据
            for meta in file_metas:
                now = time.localtime(time.time())
                tmp_name = 'upload-{:04d}{:02d}{:02d}{:02d}{:02d}{:02d}.csv'.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
                csv_filename = os.path.join(upload_path, tmp_name)
                with open(csv_filename, 'wb') as up:
                    up.write(meta['body'])

            # file encode maybe utf8 or gbk... check it out.
            file_encode = None
            with open(csv_filename, encoding='gbk') as up:
                try:
                    up.readlines()
                    file_encode = 'gbk'
                except:
                    log.e('open file:{} -1\n'.format(csv_filename))

            if file_encode is None:
                with open(csv_filename, encoding='utf8') as up:
                    try:
                        up.readlines()
                        file_encode = 'utf8'
                    except:
                        log.e('open file:{} -2\n'.format(csv_filename))

            if file_encode is None:
                os.remove(csv_filename)
                self.write_json(-2)
                log.e('file {} unknown encode.\n'.format(csv_filename))
                return

            with open(csv_filename, encoding=file_encode) as up:
                csv_reader = csv.reader(up)
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

                    # pro_type = int(line[6])
                    # host_port = int(line[3])

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
                    is_encrpty = int(csv_recorder[9])
                    user_args['user_param'] = csv_recorder[10].replace('\\n', '\n')
                    user_args['cert_id'] = int(csv_recorder[11])
                    auth_mode = int(csv_recorder[12])
                    user_args['auth_mode'] = auth_mode
                    user_args['user_pswd'] = ''
                    ret_code = 0
                    if auth_mode == 0:
                        pass
                    elif auth_mode == 1:
                        try:
                            if is_encrpty == 0:
                                ret_code, tmp_pswd = get_enc_data(user_pswd)
                            else:
                                tmp_pswd = user_pswd
                            user_args['user_pswd'] = tmp_pswd
                        except Exception:
                            ret_code = -1
                            log.e('get_enc_data() failed.\n')

                        if 0 != ret_code:
                            ret['msg'].append({'reason': '加密用户密码失败，可能原因：Teleport核心服务未启动', 'line': ', '.join(csv_recorder)})
                            log.e('get_enc_data() failed, error={}\n'.format(ret_code))
                            continue

                    elif auth_mode == 2:
                        pass
                        # user_args['cert_id'] = int(csv_recorder[7])
                    else:
                        ret['msg'].append({'reason': '未知的认证模式', 'line': ', '.join(csv_recorder)})
                        log.e('auth_mode unknown\n')
                        continue

                    uid = host.sys_user_add(user_args)
                    if uid < 0:
                        if uid == -100:
                            ret['msg'].append({'reason': '添加登录账号失败，账号已存在', 'line': ', '.join(csv_recorder)})
                        else:
                            ret['msg'].append({'reason': '添加登录账号失败，操作数据库失败', 'line': ', '.join(csv_recorder)})
                            # log.e('sys_user_add() failed.\n')

            ret = json.dumps(ret).encode('utf8')
            self.write(ret)
        except:
            log.e('error\n')
            ret['code'] = -1
            ret = json.dumps(ret).encode('utf8')
            self.write(ret)

        finally:
            if os.path.exists(csv_filename):
                os.remove(csv_filename)

                # self.write_json(0)


class GetListHandler(SwxAuthJsonHandler):
    def post(self):
        _user = self.get_session('user')
        if _user is None:
            return self.write(-1)

        _type = _user['type']
        _uname = _user['name']

        filter = dict()
        user = self.get_current_user()
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
        if _type == 100:
            _total, _hosts = host.get_all_host_info_list(filter, order, limit)
        else:
            filter['account_name'] = _uname
            _total, _hosts = host.get_host_info_list_by_user(filter, order, limit)
        # print(_hosts)

        ret = dict()
        ret['page_index'] = limit['page_index']
        ret['total'] = _total
        ret['data'] = _hosts
        self.write_json(0, data=ret)
        # self.write(json_encode(data))


class GetGrouplist(SwxAuthJsonHandler):
    def post(self):
        group_list = host.get_group_list()
        self.write_json(0, data=group_list)


class UpdateHandler(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return

        if 'host_id' not in args or 'kv' not in args:
            # ret = {'code':-2}
            self.write_json(-2)
            return

        # _host_id = args['host_id']

        _ret = host.update(args['host_id'], args['kv'])

        if _ret:
            self.write_json(0)
        else:
            self.write_json(-1)


class AddHost(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return

        try:
            ret = host.add_host(args)
            if ret > 0:
                self.write_json(0)
            else:
                self.write_json(ret)
            return
        except:
            self.write_json(-1)
            return


class LockHost(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return

        host_id = args['host_id']
        lock = args['lock']
        try:
            ret = host.lock_host(host_id, lock)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class DeleteHost(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        host_list = args['host_list']
        try:
            ret = host.delete_host(host_list)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class ExportHost(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        order = dict()
        order['name'] = 'host_id'
        order['asc'] = True

        limit = dict()
        limit['page_index'] = 0
        limit['per_page'] = 999999
        _total, _hosts = host.get_all_host_info_list(dict(), order, limit, True)
        export_file = os.path.join(cfg.static_path, 'download', 'export_csv_data.csv')
        if os.path.exists(export_file):
            os.remove(export_file)
        try:
            csv_file = open(export_file, 'w', encoding='utf8')
            # with open(export_file, 'wb') as csvfile:
            #     spamwriter = csv.writer(csvfile)
            #     spamwriter.writerow(['Spam'] * 5 + ['Baked Beans'])
            #     spamwriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])
            csv_header = "分组ID, 操作系统, " \
                         "IP地址, 端口, 协议, 状态, 描述, " \
                         "系统用户, 系统密码, 是否加密,附加参数, 密钥ID, 认证类型"
            csv_file.write(csv_header)
            csv_file.write('\n')
        except:
            log.e('')
            csv_file.close()
            self.write_json(-1)
            return

        try:

            for h in _hosts:
                auth_list = h['auth_list']
                # 分组ID, 操作系统, IP地址, 端口, 协议, 状态, 描述, 系统用户, 系统密码, 是否加密,附加参数, , 密钥ID, 认证类型
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
                    csv_file.write(row_string)
                    csv_file.write('\n')
                    # row = list()
                    # row.append(h['host_id'])
                    # row.append(h['group_id'])
                    # row.append(h['host_sys_type'])
                    # row.append(h['host_ip'])
                    # row.append(h['host_port'])
                    # row.append(h['protocol'])
                    # row.append(h['host_lock'])
                    # row.append(h['host_desc'])
                    # auth_list = h['auth_list']
                    # row.append(j['host_auth_id'])
                    # row.append(j['user_name'])
                    # row.append(j['user_pswd'])
                    # row.append(1)
                    # row.append(j['user_param'])
                    # row.append(j['cert_id'])
                    # row.append(j['auth_mode'])
        except Exception as e:
            log.e('')
        finally:
            csv_file.close()
        url = '/static/download/export_csv_data.csv'
        ret = dict()
        ret['url'] = url
        self.write_json(0, data=ret)
        return


class GetCertList(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        _certs = host.get_cert_list()
        if _certs is None:
            self.write_json(-1)
            return
        else:
            self.write_json(0, data=_certs)
            return


class AddCert(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return

        cert_pub = args['cert_pub']
        cert_pri = args['cert_pri']
        cert_name = args['cert_name']

        if len(cert_pri) == 0:
            self.write_json(-1)
            return
        try:
            ret_code, cert_pri = get_enc_data(cert_pri)
        except Exception as e:
            self.write_json(-100)
            return
        if 0 != ret_code:
            self.write_json(ret_code)
            return

        try:
            ret = host.add_cert(cert_pub, cert_pri, cert_name)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class DeleteCert(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        cert_id = args['cert_id']
        try:
            ret = host.delete_cert(cert_id)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class UpdateCert(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        cert_id = args['cert_id']
        cert_pub = args['cert_pub']
        cert_pri = args['cert_pri']
        cert_name = args['cert_name']

        if len(cert_pri) > 0:
            try:
                ret_code, cert_pri = get_enc_data(cert_pri)
            except Exception as e:
                self.write_json(-100)
                return
            if 0 != ret_code:
                self.write_json(ret_code)
                return

        try:
            ret = host.update_cert(cert_id, cert_pub, cert_pri, cert_name)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class AddGroup(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        group_name = args['group_name']
        try:
            ret = host.add_group(group_name)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class UpdateGroup(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        group_id = args['group_id']
        group_name = args['group_name']
        try:
            ret = host.update_group(group_id, group_name)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class DeleteGroup(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        group_id = args['group_id']
        try:
            ret = host.delete_group(group_id)
            if ret == 0:
                self.write_json(0)
            else:
                self.write_json(ret)
            return
        except:
            self.write_json(-1)
            return


class AddHostToGroup(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        host_list = args['host_list']
        group_id = args['group_id']
        try:
            ret = host.add_host_to_group(host_list, group_id)
            if ret:
                self.write_json(0)
            else:
                self.write_json(-1)
            return
        except:
            self.write_json(-1)
            return


class GetHostExtendInfo(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        try:
            host_id = args['host_id']
            _host = host.get_host_extend_info(host_id)
            self.write_json(0, data=_host)
            return
        except:
            self.write_json(-1)
            return


class UpdateHostExtendInfo(SwxAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        host_id = args['host_id']

        if args['host_auth_mode'] == 1:
            if len(args['user_pwd']) > 0:
                try:
                    ret_code, tmp_pswd = get_enc_data(args['user_pwd'])
                except Exception as e:
                    self.write_json(-100)
                    return
                if 0 != ret_code:
                    self.write_json(ret_code)
                    return

                args['user_pwd'] = tmp_pswd

        # ip = args['ip']
        # port = args['port']
        # user_name = args['user_name']
        # user_pwd = args['user_pwd']
        # cert_id = args['cert_id']
        # pro_type = args['pro_type']
        ret = host.update_host_extend_info(host_id, args)
        if ret:
            self.write_json(0)
        else:
            self.write_json(-1)


def post_http(url, values):
    try:
        # log.v('post_http(), url={}\n'.format(url))

        user_agent = 'Mozilla/4.0 (compatible;MSIE 5.5; Windows NT)'
        # values = {
        #     'act': 'login',
        #     'login[email]': 'yzhang@i9i8.com',
        #     'login[password]': '123456'
        # }
        values = json.dumps(values)
        data = urllib.parse.quote(values).encode('utf-8')
        headers = {'User-Agent': user_agent}
        req = urllib.request.Request(url=url, data=data, headers=headers)
        response = urllib.request.urlopen(req, timeout=3)
        the_page = response.read()
        info = response.info()
        _zip = info.get('Content-Encoding')
        if _zip == 'gzip':
            the_page = gzip.decompress(the_page)
        else:
            pass
        the_page = the_page.decode()
        # print(the_page)
        return the_page
    except:
        return None


class GetSessionId(SwxAuthJsonHandler):
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
            # print('args', args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return
        if 'auth_id' not in args:
            self.write_json(-1)
            return
        auth_id = args['auth_id']

        # config_list = host.get_config_list()
        # ts_server_rpc_ip = '127.0.0.1'
        #
        # if 'ts_server_rpc_ip' in config_list:
        #     ts_server_rpc_ip = config_list['ts_server_rpc_ip']
        # ts_server_rpc_port = 52080
        # if 'ts_server_rpc_port' in config_list:
        #     ts_server_rpc_port = config_list['ts_server_rpc_port']
        ts_server_rpc_ip = cfg.core.rpc.ip
        ts_server_rpc_port = cfg.core.rpc.port

        url = 'http://{}:{}/rpc'.format(ts_server_rpc_ip, ts_server_rpc_port)
        req = {'method': 'request_session', 'param': {'authid': auth_id}}
        return_data = post_http(url, req)
        if return_data is None:
            return self.write_json(-1)
        return_data = json.loads(return_data)
        if 'code' not in return_data:
            return self.write_json(-1)
        _code = return_data['code']
        if _code != 0:
            return self.write_json(_code)
        try:
            session_id = return_data['data']['sid']
        except:
            return self.write_json(-1)

        data = dict()
        data['session_id'] = session_id

        return self.write_json(0, data=data)


class AdminGetSessionId(SwxAuthJsonHandler):
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            self.write_json(-1)
            return

        if 'host_auth_id' not in args:
            self.write_json(-1)
            return
        host_auth_id = args['host_auth_id']

        values = host.get_host_auth_info(host_auth_id)
        if values is None:
            self.write_json(-1)
            return
        values['account'] = 'admin'

        # config_list = host.get_config_list()
        # ts_server_rpc_ip = '127.0.0.1'
        #
        # if 'ts_server_rpc_ip' in config_list:
        #     ts_server_rpc_ip = config_list['ts_server_rpc_ip']
        # ts_server_rpc_port = 52080
        # if 'ts_server_rpc_port' in config_list:
        #     ts_server_rpc_port = config_list['ts_server_rpc_port']
        ts_server_rpc_ip = cfg.core.rpc.ip
        ts_server_rpc_port = cfg.core.rpc.port

        url = 'http://{}:{}/request_session'.format(ts_server_rpc_ip, ts_server_rpc_port)
        # values['auth_id'] = auth_id
        return_data = post_http(url, values)
        if return_data is None:
            return self.write_json(-1)
        return_data = json.loads(return_data)
        if 'code' not in return_data:
            return self.write_json(-1)
        _code = return_data['code']
        if _code != 0:
            return self.write_json(_code)
        try:
            session_id = return_data['data']['sid']
        except:
            return self.write_json(-1)

        data = dict()
        data['session_id'] = session_id

        return self.write_json(0, data=data)


class AdminFastGetSessionId(SwxAuthJsonHandler):
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            self.write_json(-1)
            return

        try:
            host_ip = args['host_ip']
            host_port = args['host_port']
            sys_type = args['sys_type']
            user_name = args['user_name']
            user_pswd = args['user_pswd']
            host_auth_id = args['host_auth_id']
            cert_id = args['cert_id']
            auth_mode = args['auth_mode']
            protocol = args['protocol']
            user_param = args['user_param']
        except Exception as e:
            self.write_json(-2)
            return

        values = dict()
        values['ip'] = host_ip
        values['port'] = int(host_port)
        values['systype'] = int(sys_type)

        values['uname'] = user_name
        values['uparam'] = user_param
        values['authmode'] = int(auth_mode)

        values['protocol'] = int(protocol)
        values['enc'] = 1

        if auth_mode == 1:
            if len(user_pswd) == 0:
                h = host.get_host_auth_info(host_auth_id)
                tmp_pswd = h['uauth']
            else:
                ret_code, tmp_pswd = get_enc_data(user_pswd)
                if ret_code != 0:
                    self.write_json(-99)
                    return
            values['uauth'] = tmp_pswd
        elif auth_mode == 2:
            uauth = host.get_cert_info(int(cert_id))
            if uauth is None:
                self.write_json(-100)
                return
            values['uauth'] = uauth
        elif auth_mode == 0:
            values['uauth'] = ''
        else:
            self.write_json(-101)
            return

        values['account'] = 'admin'

        # config_list = host.get_config_list()
        # ts_server_rpc_ip = '127.0.0.1'
        #
        # if 'ts_server_rpc_ip' in config_list:
        #     ts_server_rpc_ip = config_list['ts_server_rpc_ip']
        # ts_server_rpc_port = 52080
        # if 'ts_server_rpc_port' in config_list:
        #     ts_server_rpc_port = config_list['ts_server_rpc_port']
        ts_server_rpc_ip = cfg.core.rpc.ip
        ts_server_rpc_port = cfg.core.rpc.port

        url = 'http://{}:{}/request_session'.format(ts_server_rpc_ip, ts_server_rpc_port)
        # values['auth_id'] = auth_id
        return_data = post_http(url, values)
        if return_data is None:
            return self.write_json(-1)
        return_data = json.loads(return_data)
        if 'code' not in return_data:
            return self.write_json(-1)
        _code = return_data['code']
        if _code != 0:
            return self.write_json(_code)
        try:
            session_id = return_data['data']['sid']
        except:
            return self.write_json(-1)

        data = dict()
        data['session_id'] = session_id

        return self.write_json(0, data=data)


class SysUserList(SwxAuthJsonHandler):
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            self.write_json(-1)
            return
        try:
            host_id = args['host_id']
        except Exception as e:
            self.write_json(-2)
            return

        data = host.sys_user_list(host_id)
        return self.write_json(0, data=data)


class SysUserAdd(SwxAuthJsonHandler):
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            self.write_json(-1)
            return

        try:
            auth_mode = args['auth_mode']
            user_pswd = args['user_pswd']
            cert_id = args['cert_id']
        except Exception as e:
            self.write_json(-2)
            return

        if auth_mode == 1:
            if 0 == len(args['user_pswd']):
                self.write_json(-1)
                return
            try:
                ret_code, tmp_pswd = get_enc_data(user_pswd)
            except Exception as e:
                self.write_json(ret_code)
                return
            if 0 != ret_code:
                self.write_json(ret_code)
                return

            args['user_pswd'] = tmp_pswd

        if host.sys_user_add(args) < 0:
            return self.write_json(-1)

        return self.write_json(0)


class SysUserUpdate(SwxAuthJsonHandler):
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            # ret = {'code':-1}
            self.write_json(-1)
            return

        if 'host_auth_id' not in args or 'kv' not in args:
            # ret = {'code':-2}
            self.write_json(-2)
            return

        kv = args['kv']
        if 'auth_mode' not in kv or 'user_pswd' not in kv or 'cert_id' not in kv:
            self.write_json(-3)
            return

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
            try:
                ret_code, tmp_pswd = get_enc_data(user_pswd)
            except Exception as e:
                self.write_json(-100)
                return
            if 0 != ret_code:
                self.write_json(ret_code)
                return

            args['kv']['user_pswd'] = tmp_pswd

        if host.sys_user_update(args['host_auth_id'], args['kv']):
            return self.write_json(0)

        return self.write_json(-1)


class SysUserDelete(SwxAuthJsonHandler):
    def post(self, *args, **kwargs):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            self.write_json(-2)
            return
        try:
            host_auth_id = args['host_auth_id']
        except Exception as e:
            self.write_json(-2)
            return

        if host.sys_user_delete(host_auth_id):
            return self.write_json(0)

        return self.write_json(-1)
