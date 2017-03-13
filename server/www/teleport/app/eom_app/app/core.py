# -*- coding: utf-8 -*-

import os
# import sys
import json
import urllib.parse
import urllib.request

import tornado.httpserver
import tornado.ioloop
import tornado.netutil
import tornado.process
import tornado.web

# from eom_common.eomcore.eom_mysql import get_mysql_pool
from eom_common.eomcore.eom_sqlite import get_sqlite_pool
import eom_common.eomcore.utils as utils
from eom_common.eomcore.logger import log
from .const import *
from .configs import app_cfg
from .db import get_db
from .session import web_session

cfg = app_cfg()


class WebServerCore:
    def __init__(self):
        pass

    def init(self, options):
        log.initialize()

        cfg.app_path = os.path.abspath(options['app_path'])
        cfg.static_path = os.path.abspath(options['static_path'])
        cfg.data_path = os.path.abspath(options['data_path'])
        cfg.template_path = os.path.abspath(options['template_path'])
        cfg.res_path = os.path.abspath(options['res_path'])
        cfg.cfg_path = os.path.abspath(options['cfg_path'])

        # cfg.app_mode = APP_MODE_NORMAL
        # if os.path.exists(os.path.join(cfg.cfg_path, 'maintenance-mode')):
        #     cfg.app_mode = APP_MODE_MAINTENANCE
        # else:
        #     cfg.app_mode = APP_MODE_NORMAL

        _cfg_file = os.path.join(cfg.cfg_path, 'web.ini')
        if not cfg.load_web(_cfg_file):
            return False

        cfg.log_path = os.path.abspath(options['log_path'])
        cfg.log_file = os.path.join(cfg.log_path, 'tpweb.log')

        if not os.path.exists(cfg.log_path):
            utils.make_dir(cfg.log_path)
            if not os.path.exists(cfg.log_path):
                log.e('Can not create log path:{}\n'.format(cfg.log_path))
                return False

        log.set_attribute(min_level=cfg.log_level, filename=cfg.log_file)
        if cfg.debug:
            log.set_attribute(trace_error=log.TRACE_ERROR_FULL)

        # 尝试通过CORE-JSON-RPC获取core服务的配置（主要是ssh/rdp/telnet的端口）
        self._get_core_server_config()

        if not web_session().init():
            return False

        # TODO: 这里不要初始化数据库接口，需要根据配置文件来决定使用什么数据库（初始安装时还没有配置数据库信息）
        # get_mysql_pool().init(cfg.mysql_ip, cfg.mysql_port, cfg.mysql_user, cfg.mysql_pass)
        # db_path = os.path.join(cfg.data_path, 'ts_db.db')
        get_sqlite_pool().init(cfg.data_path)

        get_db().init_sqlite(os.path.join(cfg.data_path, 'ts_db.db'))
        if get_db().need_create or get_db().need_upgrade:
            cfg.app_mode = APP_MODE_MAINTENANCE
        else:
            cfg.app_mode = APP_MODE_NORMAL

        return True

    def _get_core_server_config(self):
        try:
            req = {'method': 'get_config', 'param': []}
            req_data = json.dumps(req)
            data = urllib.parse.quote(req_data).encode('utf-8')
            req = urllib.request.Request(url=cfg.core_server_rpc, data=data)
            rep = urllib.request.urlopen(req, timeout=3)
            body = rep.read().decode()
            x = json.loads(body)
            cfg.update_core(x['data'])
        except:
            log.w('can not connect to core server for get config, maybe it not start yet, ignore.\n')

    def run(self):

        settings = {
            #
            'cookie_secret': '8946svdABGD345fg98uhIaefEBePIfegOIakjFH43oETzK',

            'login_url': '/auth/login',

            # 指定静态文件的路径，页面模板中可以用 {{ static_url('css/main.css') }} 的方式调用
            'static_path': cfg.static_path,

            # 指定模板文件的路径
            'template_path': cfg.template_path,

            # 防止跨站伪造请求，参见 http://old.sebug.net/paper/books/tornado/#_7
            'xsrf_cookies': False,

            'autoescape': 'xhtml_escape',

            # 'ui_modules': ui_modules,
            # 'debug': True,

            # Debug Mode.
            'compiled_template_cache': True,
            'static_hash_cache': True,
        }

        if cfg.debug:
            settings['compiled_template_cache'] = False
            settings['static_hash_cache'] = False

        from eom_app.controller import controllers
        web_app = tornado.web.Application(controllers, **settings)

        server = tornado.httpserver.HTTPServer(web_app)
        try:
            server.listen(cfg.server_port)
            log.i('works on [http://127.0.0.1:{}]\n'.format(cfg.server_port))
        except:
            log.e('Can not listen on port {}, maybe it been used by another application.\n'.format(cfg.server_port))
            return 0

        # 启动session超时管理
        web_session().start()

        tornado.ioloop.IOLoop.instance().start()

        web_session().stop()

        return 0
