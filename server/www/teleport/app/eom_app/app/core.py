# -*- coding: utf-8 -*-

import json
import os
import urllib.parse
import urllib.request

import eom_common.eomcore.utils as utils
import tornado.httpserver
import tornado.ioloop
import tornado.netutil
import tornado.process
import tornado.web
from eom_common.eomcore.logger import log
from .configs import app_cfg
from .const import *
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

        _cfg_file = os.path.join(cfg.cfg_path, 'web.ini')
        if not cfg.load(_cfg_file):
            return False

        _log_file, ok = cfg.get_str('common::log-file')
        if ok:
            cfg.log_path = os.path.abspath(os.path.dirname(_log_file))
        else:
            cfg.log_path = os.path.abspath(options['log_path'])
            _log_file = os.path.join(cfg.log_path, 'tpweb.log')
            cfg.set_default('common::log-file', _log_file)

        if not os.path.exists(cfg.log_path):
            utils.make_dir(cfg.log_path)
            if not os.path.exists(cfg.log_path):
                log.e('Can not create log path:{}\n'.format(cfg.log_path))
                return False

        # log.set_attribute(min_level=cfg.common.log_level, filename=cfg.common.log_file)
        # if cfg.common.debug_mode:
        #     log.set_attribute(min_level=log.LOG_DEBUG, trace_error=log.TRACE_ERROR_FULL)

        return True

    def _get_core_server_config(self):
        try:
            req = {'method': 'get_config', 'param': []}
            req_data = json.dumps(req)
            data = urllib.parse.quote(req_data).encode('utf-8')
            req = urllib.request.Request(url=cfg.common.core_server_rpc, data=data)
            rep = urllib.request.urlopen(req, timeout=3)
            body = rep.read().decode()
            x = json.loads(body)
            log.d('connect core server and get config info succeeded.\n')
            cfg.update_core(x['data'])
        except:
            log.w('can not connect to core server to get config, maybe it not start yet, ignore.\n')

    def run(self):
        # 尝试通过CORE-JSON-RPC获取core服务的配置（主要是ssh/rdp/telnet的端口以及录像文件存放路径）
        self._get_core_server_config()

        _db = get_db()
        if not _db.init():
            log.e('can not initialize database interface.\n')
            return 0

        if _db.need_create or _db.need_upgrade:
            cfg.app_mode = APP_MODE_MAINTENANCE
        else:
            cfg.app_mode = APP_MODE_NORMAL

        if not web_session().init():
            log.e('can not initialize session manager.\n')
            return 0

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
            'debug': False,

            # 不开启模板和静态文件的缓存，这样一旦模板文件和静态文件变化，刷新浏览器即可看到更新。
            'compiled_template_cache': False,
            'static_hash_cache': False,
        }

        from eom_app.controller import controllers
        web_app = tornado.web.Application(controllers, **settings)

        server = tornado.httpserver.HTTPServer(web_app)

        try:
            server.listen(cfg.common.port, address=cfg.common.ip)
            if cfg.common.ip == '0.0.0.0':
                log.i('works on [http://127.0.0.1:{}]\n'.format(cfg.common.port))
            else:
                log.i('works on [http://{}:{}]\n'.format(cfg.common.ip, cfg.common.port))
        except:
            log.e('can not listen on port {}:{}, make sure it not been used by another application.\n'.format(cfg.common.ip, cfg.common.port))
            return 0

        # 启动session超时管理
        web_session().start()

        tornado.ioloop.IOLoop.instance().start()

        web_session().stop()

        return 0
