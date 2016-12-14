# -*- coding: utf-8 -*-
import os
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.netutil
import tornado.process
import tornado.web
# from eom_app.controller import controllers

# from eom_common.eomcore.eom_mysql import get_mysql_pool
from eom_common.eomcore.eom_sqlite import get_sqlite_pool
import eom_common.eomcore.utils as utils
from eom_common.eomcore.logger import log
from .configs import app_cfg
from .session import swx_session
cfg = app_cfg()


class SwxCore:
    def __init__(self):
        # self._cfg = ConfigFile()
        pass

    def init(self, options):
        cfg.debug = False

        cfg.dev_mode = options['dev_mode']

        if 'log_path' not in options:
            return False
        else:
            cfg.log_path = options['log_path']

        if not os.path.exists(cfg.log_path):
            utils.make_dir(cfg.log_path)
            if not os.path.exists(cfg.log_path):
                log.e('Can not create log path.\n')
                return False

        if 'app_path' not in options:
            return False
        else:
            cfg.app_path = options['app_path']

        if not self._load_config(options):
            return False

        if 'static_path' in options:
            cfg.static_path = options['static_path']
        else:
            cfg.static_path = os.path.join(options['app_path'], 'static')

        if 'data_path' in options:
            cfg.data_path = options['data_path']
        else:
            cfg.data_path = os.path.join(options['app_path'], 'data')

        if 'template_path' in options:
            cfg.template_path = options['template_path']
        else:
            cfg.template_path = os.path.join(options['app_path'], 'view')

        if 'res_path' in options:
            cfg.res_path = options['res_path']
        else:
            cfg.res_path = os.path.join(options['app_path'], 'res')

        if not swx_session().init():
            return False

        # get_mysql_pool().init(cfg.mysql_ip, cfg.mysql_port, cfg.mysql_user, cfg.mysql_pass)
        # db_path = os.path.join(cfg.data_path, 'ts_db.db')
        get_sqlite_pool().init(cfg.data_path)

        var_js = os.path.join(cfg.static_path, 'js', 'var.js')
        try:
            # if not os.path.exists(var_js):
            f = open(var_js, 'w')
            f.write("\"use strict\";\nvar teleport_ip = \"{}\";\n".format(get_sqlite_pool().get_config_server_ip()))
            f.close()
        except Exception:
            log.e('can not load config: server_ip.\n')
            return False

        return True

    def _load_config(self, options):
        if 'cfg_path' in options:
            _cfg_path = options['cfg_path']
        else:
            _cfg_path = os.path.join(options['app_path'], 'conf')

        _cfg_file = os.path.join(_cfg_path, 'web.conf')
        if not cfg.load(_cfg_file):
            return False

        cfg.cfg_path = _cfg_path

        return True

    @staticmethod
    def _daemon():
        # fork for daemon.
        if sys.platform == 'win32':
            # log.v('os.fork() not support Windows, operation ignored.\n')
            return True

        try:
            pid = os.fork()
            if pid > 0:
                # log.w('parent #1 exit.\n')
                # return False
                os._exit(0)
        except OSError:
            log.e('fork #1 failed.\n')
            os._exit(1)

        # Detach from parent env.
        os.chdir('/')
        os.umask(0)
        os.setsid()

        # Second fork.
        try:
            pid = os.fork()
            if pid > 0:
                # log.w('parent #2 exit.\n')
                # return False
                os._exit(0)
        except OSError:
            log.e('fork #2 failed.\n')
            # return False
            os._exit(1)

        # OK I'm daemon now.
        for f in sys.stdout, sys.stderr:
            f.flush()
        si = open('/dev/null', 'r')
        so = open('/dev/null', 'a+')
        se = open('/dev/null', 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # test print() not raise exception.
        # print('good.')

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

        # if cfg.debug:
        #     settings['compiled_template_cache'] = False
        #     settings['static_hash_cache'] = False
        # settings['compiled_template_cache'] = False
        # settings['static_hash_cache'] = False

        from eom_app.controller import controllers
        web_app = tornado.web.Application(controllers, **settings)

        # if sys.platform == 'win32':
        #     web_app.listen(cfg.server_port)
        #     log.v('Web Server start on http://127.0.0.1:{}\n'.format(cfg.server_port))
        #     tornado.ioloop.IOLoop.instance().start()
        # else:
        #     if not cfg.debug:
        #         if not self._daemon():
        #             return False
        #         # 进入daemon模式了，不再允许输出信息到控制台了
        #         log.set_attribute(console=False, filename='/var/log/eom/ts-backend.log')
        #         log.v('\n=====================================\n')
        #
        #         def _run(port):
        #             log.v('Web Server start on http://127.0.0.1:{}\n'.format(port))
        #             web_app.listen(port)
        #             tornado.ioloop.IOLoop.instance().start()
        #             log.w('a tornado io-loop exit.\n')
        #
        #         jobs = list()
        #         port = cfg.server_port
        #         for x in range(cfg.server_worker):
        #             p = multiprocessing.Process(target=_run, args=(port,))
        #             jobs.append(p)
        #             p.start()
        #             port = port + 1
        #
        #     else:
        #         # sockets = tornado.netutil.bind_sockets(cfg.server_port)
        #         # tornado.process.fork_processes(2)
        #         # server = tornado.httpserver.HTTPServer(web_app)
        #         # server.add_sockets(sockets)
        #         web_app.listen(cfg.server_port)
        #         log.v('Web Server start on http://127.0.0.1:{}\n'.format(cfg.server_port))
        #         tornado.ioloop.IOLoop.instance().start()

        # server = tornado.httpserver.HTTPServer(web_app, ssl_options={
        #     'certfile': os.path.join(cfg.cfg_path, 'ssl', 'server.pem'),
        #     'keyfile': os.path.join(cfg.cfg_path, 'ssl', 'server.key')
        # })
        # if sys.platform == 'win32':
        #     log.set_attribute(console=False, filename='/var/log/eom_ts/ts-backend.log')
        # else:
        #     log.set_attribute(console=False, filename='/var/log/eom_ts/ts-backend.log')

        log.v('Web Server start on http://127.0.0.1:{}\n'.format(cfg.server_port))

        server = tornado.httpserver.HTTPServer(web_app)
        try:
            server.listen(cfg.server_port)
        except:
            log.e('Can not listen on port {}, maybe it been used by another application.\n'.format(cfg.server_port))
            return 0

        if not cfg.dev_mode:
            log_file = os.path.join(cfg.log_path, 'ts-web.log')
            log.set_attribute(console=False, filename=log_file)

        tornado.ioloop.IOLoop.instance().start()
        return 0
