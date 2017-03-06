# -*- coding: utf-8 -*-

import json
import os
import platform
import re
import socket
import subprocess
import threading
import time

from eom_app.app.configs import app_cfg
from eom_app.module import host
from eom_app.module import set
from .base import SwxAdminHandler, SwxAdminJsonHandler

cfg = app_cfg()


def get_local_ip():
    iplist = []
    PLATFORM = platform.system().lower()
    try:
        if PLATFORM == "windows":
            ip_info = socket.gethostbyname_ex(socket.gethostname())
            return ip_info[2]
        else:
            ipstr = '([0-9]{1,3}\.){3}[0-9]{1,3}'
            ipconfig_process = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)
            output = ipconfig_process.stdout.read()
            ip_pattern = re.compile('(inet addr:%s)' % ipstr)
            pattern = re.compile(ipstr)

            for ipaddr in re.finditer(ip_pattern, str(output)):
                ip = pattern.search(ipaddr.group())
                if ip.group() != "127.0.0.1":
                    iplist.append(ip.group())
            return iplist
    except Exception:
        return iplist


class IndexHandler(SwxAdminHandler):
    def get(self):
        # static_path = cfg.static_path
        # var_js = os.path.join(static_path, 'js', 'var.js')

        # f = None

        # try:
        #     config_list = host.get_config_list()
        #     ts_server = dict()
        #     ts_server['ip'] = config_list['ts_server_ip']
        #     ts_server['ssh_port'] = config_list['ts_server_ssh_port']
        #     ts_server['rdp_port'] = config_list['ts_server_rdp_port']
        #     ts_server['telnet_port'] = config_list['ts_server_telnet_port']
        #     # f = open(var_js, 'w')
        #     # f.write("\"use strict\";\nvar teleport_ip = \"{}\";\n".format(ts_server['ip']))
        # except Exception:
        #     return self.write(-1)
        # finally:
        #     # if f is not None:
        #     #     f.close()
        #     pass

        # config_list = set.get_config_list()
        # if 'ts_server_ip' in config_list:
        #     ip_list = get_local_ip()
        #     if not isinstance(ip_list, list):
        #         ip_list = [ip_list, ]
        #
        #     # ip_list.append(config_list['ts_server_ip'])
        #     if config_list['ts_server_ip'] not in ip_list:
        #         ip_list.append(config_list['ts_server_ip'])
        #
        #     # if isinstance(temp, list):
        #     #     ip_list.extend(temp)
        #
        #     config_list['_ip_list'] = ip_list

        # cfg_list = dict()
        # cfg_list['ts_server_ssh_port'] = cfg.core.ssh.port
        # cfg_list['ts_server_ssh_enabled'] = 1 if cfg.core.ssh.enabled else 0
        # cfg_list['ts_server_rdp_port'] = cfg.core.rdp.port
        # cfg_list['ts_server_rdp_enabled'] = 1 if cfg.core.rdp.enabled else 0
        # cfg_list['ts_server_telnet_port'] = cfg.core.telnet.port
        # cfg_list['ts_server_telnet_enabled'] = 1 if cfg.core.telnet.enabled else 0
        # self.render('set/index.mako', config_list=cfg_list)

        page_param = json.dumps({'core_server': cfg.core})
        self.render('set/index.mako', page_param=page_param)


def _restart_func():
    time.sleep(1)

    PLATFORM = platform.system().lower()

    if PLATFORM == 'windows':
        sf = os.path.join(cfg.app_path, 'tools', 'restart.bat')
        os.system('cmd.exe /c "{}"'.format(sf))
    else:
        # sf = os.path.join(cfg.app_path, 'tools', 'restart.sh')
        # os.system(sf)
        os.system('service eom_ts restart')

        # os.system(sf)


def restart_service():
    # todo: 使用eom_ts.exe运行脚本的方式（新进程）来重启服务，避免正在运行的本服务未退出的影响

    t = threading.Thread(target=_restart_func)
    t.start()


class UpdateConfig(SwxAdminJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            self.write_json(-1)
            return

        change_list = args['cfg']
        reboot = args['reboot']

        try:
            ret = set.set_config(change_list)
            if ret:
                for i in range(len(change_list)):
                    if change_list[i]['name'] == 'ts_server_ip':
                        # static_path = cfg.static_path
                        var_js = os.path.join(cfg.static_path, 'js', 'var.js')
                        f = None
                        try:
                            f = open(var_js, 'w')
                            # config_list = host.get_config_list()
                            # ts_server = dict()
                            # ts_server['ip'] = config_list['ts_server_ip']
                            # ts_server['ssh_port'] = config_list['ts_server_ssh_port']
                            # ts_server['rdp_port'] = config_list['ts_server_rdp_port']
                            # f.write("\"use strict\";\nvar teleport_ip = \"{}\";\n".format(ts_server['ip']))
                            f.write("\"use strict\";\nvar teleport_ip = \"{}\";\n".format(change_list[i]['value']))
                            break
                        except Exception:
                            return self.write(-1)
                        finally:
                            if f is not None:
                                f.close()

                if reboot:
                    restart_service()

                self.write_json(0)
            else:
                self.write_json(-1)
        except:
            self.write_json(-2)

# class OsOperator(SwxAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             self.write_json(-1)
#             return
#         _OP = int(args['OP'])
#         try:
#             if _OP == 1:
#                 os.system('reboot')
#             else:
#                 os.system('shutdown -h now')
#             # 重新启动
#             self.write_json(0)
#         except:
#             self.write_json(-2)
#
