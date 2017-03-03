# -*- coding: utf-8 -*-

import os
import sys

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

        cfg.app_mode = APP_MODE_NORMAL
        # cfg.app_mode = APP_MODE_UNKNOWN
        # if os.path.exists(os.path.join(cfg.app_path, 'maintenance-mode')):
        #     cfg.app_mode = APP_MODE_UPGRADE
        # else:
        #     cfg.app_mode = APP_MODE_NORMAL

        _cfg_file = os.path.join(cfg.cfg_path, 'web.ini')
        if not cfg.load_web(_cfg_file):
            return False

        # TODO: 不要直接读取core.ini，而是通过core的json-rpc获取其配置数据
        _cfg_file = os.path.join(cfg.cfg_path, 'core.ini')
        if not cfg.load_core(_cfg_file):
            return False

        cfg.log_path = os.path.abspath(options['log_path'])
        cfg.log_file = os.path.join(cfg.log_path, 'tpweb.log')

        if not os.path.exists(cfg.log_path):
            utils.make_dir(cfg.log_path)
            if not os.path.exists(cfg.log_path):
                log.e('Can not create log path:{}\n'.format(cfg.log_path))
                return False

        log.set_attribute(min_level=cfg.log_level, filename=cfg.log_file)
        # log.set_attribute(min_level=self['log_level'])

        if not web_session().init():
            return False

        # TODO: 这里不要初始化数据库接口，需要根据配置文件来决定使用什么数据库（初始安装时还没有配置数据库信息）
        # get_mysql_pool().init(cfg.mysql_ip, cfg.mysql_port, cfg.mysql_user, cfg.mysql_pass)
        # db_path = os.path.join(cfg.data_path, 'ts_db.db')
        get_sqlite_pool().init(cfg.data_path)

        return True

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
            'compiled_template_cache': False,
            'static_hash_cache': False,
        }

        # TODO: 配置文件中应该增加 debug 选项
        # if cfg.debug:
        #     settings['compiled_template_cache'] = False
        #     settings['static_hash_cache'] = False
        # settings['compiled_template_cache'] = False
        # settings['static_hash_cache'] = False


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
