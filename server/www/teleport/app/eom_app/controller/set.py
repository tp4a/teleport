# -*- coding: utf-8 -*-

import json
import tornado.gen
import tornado.httpclient

from eom_ver import *
from eom_app.app.configs import app_cfg
from eom_app.app.util import *
from .base import TPBaseAdminAuthHandler, TPBaseAdminAuthJsonHandler

cfg = app_cfg()


class InfoHandler(TPBaseAdminAuthHandler):
    @tornado.gen.coroutine
    def get(self):
        core_detected = False
        req = {'method': 'get_config', 'param': []}
        _yr = async_post_http(req)
        return_data = yield _yr
        if return_data is not None:
            if 'code' in return_data:
                _code = return_data['code']
                if _code == 0:
                    # core['detected'] = True
                    cfg.update_core(return_data['data'])
                    core_detected = True

        if not core_detected:
            cfg.update_core(None)

        param = {
            'core': cfg.core,
            'web': {
                'version': TS_VER,
                'core_server_rpc': cfg['core_server_rpc']
            }
        }
        self.render('set/info.mako', page_param=json.dumps(param))


class DatabaseHandler(TPBaseAdminAuthHandler):
    def get(self):
        param = {'core_server': cfg.core}
        self.render('set/database.mako', page_param=json.dumps(param))

# def _restart_func():
#     time.sleep(1)
#
#     PLATFORM = platform.system().lower()
#
#     if PLATFORM == 'windows':
#         sf = os.path.join(cfg.app_path, 'tools', 'restart.bat')
#         os.system('cmd.exe /c "{}"'.format(sf))
#     else:
#         # sf = os.path.join(cfg.app_path, 'tools', 'restart.sh')
#         # os.system(sf)
#         os.system('service eom_ts restart')
#
#         # os.system(sf)


# def restart_service():
#     # todo: 使用eom_ts.exe运行脚本的方式（新进程）来重启服务，避免正在运行的本服务未退出的影响
#
#     t = threading.Thread(target=_restart_func)
#     t.start()
#

# class UpdateConfig(TPBaseAdminAuthJsonHandler):
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             self.write_json(-1)
#             return
#
#         change_list = args['cfg']
#         reboot = args['reboot']
#
#         try:
#             ret = set.set_config(change_list)
#             if ret:
#                 for i in range(len(change_list)):
#                     if change_list[i]['name'] == 'ts_server_ip':
#                         # static_path = cfg.static_path
#                         var_js = os.path.join(cfg.static_path, 'js', 'var.js')
#                         f = None
#                         try:
#                             f = open(var_js, 'w')
#                             # config_list = host.get_config_list()
#                             # ts_server = dict()
#                             # ts_server['ip'] = config_list['ts_server_ip']
#                             # ts_server['ssh_port'] = config_list['ts_server_ssh_port']
#                             # ts_server['rdp_port'] = config_list['ts_server_rdp_port']
#                             # f.write("\"use strict\";\nvar teleport_ip = \"{}\";\n".format(ts_server['ip']))
#                             f.write("\"use strict\";\nvar teleport_ip = \"{}\";\n".format(change_list[i]['value']))
#                             break
#                         except Exception:
#                             return self.write(-1)
#                         finally:
#                             if f is not None:
#                                 f.close()
#
#                 if reboot:
#                     restart_service()
#
#                 self.write_json(0)
#             else:
#                 self.write_json(-1)
#         except:
#             self.write_json(-2)

# class OsOperator(TPBaseUserAuthJsonHandler):
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
