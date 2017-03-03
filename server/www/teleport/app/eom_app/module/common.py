# -*- coding: utf-8 -*-

import gzip
import json
import urllib.parse
import urllib.request

import eom_common.eomcore.eom_mysql as mysql
import eom_common.eomcore.eom_sqlite as sqlite
from eom_app.app.configs import app_cfg
# from eom_app.module import set

cfg = app_cfg()


class DbItem(dict):
    def load(self, db_item, db_fields):
        if len(db_fields) != len(db_item):
            raise RuntimeError('!=')
        for i in range(len(db_item)):
            self[db_fields[i]] = db_item[i]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise


def get_db_con():
    if False:
        sql_exec = mysql.get_mysql_pool().get_tssqlcon()
    else:
        sql_exec = sqlite.get_sqlite_pool().get_tssqlcon()
    return sql_exec


# def post_http(url, values):
#     try:
#         # log.v('post_http(), url={}\n'.format(url))
#
#         user_agent = 'Mozilla/4.0 (compatible;MSIE 5.5; Windows NT)'
#         # values = {
#         #     'act': 'login',
#         #     'login[email]': 'yzhang@i9i8.com',
#         #     'login[password]': '123456'
#         # }
#         values = json.dumps(values)
#         data = urllib.parse.quote(values).encode('utf-8')
#         # data = urllib.parse.urlencode(values).encode()
#         headers = {'User-Agent': user_agent}
#         # url = 'http://www.baidu.com'
#         req = urllib.request.Request(url=url, data=data, headers=headers)
#         response = urllib.request.urlopen(req, timeout=3)
#         the_page = response.read()
#         info = response.info()
#         _zip = info.get('Content-Encoding')
#         if _zip == 'gzip':
#             the_page = gzip.decompress(the_page)
#         else:
#             pass
#         the_page = the_page.decode()
#         return the_page
#     except:
#         return None


# def get_enc_data(data):
#     # url = cfg.ts_enc_url
#     config_list = set.get_config_list()
#     rpc_port = 52080
#     if 'ts_server_rpc_port' in config_list:
#         rpc_port = int(config_list['ts_server_rpc_port'])
#     ts_server_rpc_ip = '127.0.0.1'
#     if 'ts_server_rpc_ip' in config_list:
#         ts_server_rpc_ip = config_list['ts_server_rpc_ip']
#
#     url = 'http://{}:{}/enc'.format(ts_server_rpc_ip, rpc_port)
#
#     values = dict()
#     if not isinstance(data, str):
#         data = "{}".format(data)
#
#     values['p'] = data
#     return_data = post_http(url, values)
#     if return_data is None:
#         return -2, ''
#
#     if return_data is not None:
#         return_data = json.loads(return_data)
#     else:
#         return -3, ''
#
#     ret_code = return_data['code']
#     if ret_code != 0:
#         return ret_code, ''
#     if 'data' not in return_data:
#         return -5, ''
#
#     data = return_data['data']
#     if 'c' not in data:
#         return -6, ''
#
#     decry_data = data['c']
#
#     return 0, decry_data
