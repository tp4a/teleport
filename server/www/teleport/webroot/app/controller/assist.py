# -*- coding: utf-8 -*-

import json
import os

import tornado.ioloop
import tornado.gen
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.logger import log
from app.base.configs import tp_cfg
from app.base.assist_bridge import tp_assist_bridge
from app.const import *
from tornado.escape import json_encode


class ConfigHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_LOGIN_WEB)
        if ret != TPE_OK:
            return

        param = {'username': self._user['username']}
        self.render('assist/config.mako', page_param=json.dumps(param))


class DoGetAssistInfoHandler(TPBaseJsonHandler):
    def post(self):
        user_info = self.get_current_user()
        if not user_info['_is_login']:
            return self.write_json(TPE_NEED_LOGIN)

        assist = tp_assist_bridge().get_assist_bridge(self._s_id)
        if assist is None:
            return self.write_json(TPE_NOT_EXISTS)

        return self.write_json(TPE_OK, data={'assist_id': assist.assist_id, 'assist_ver': assist.assist_ver})


class DoDownloadAssistHandler(TPBaseHandler):
    @tornado.gen.coroutine
    def get(self, os_type):
        cfg = tp_cfg()
        dl_path = os.path.join(cfg.data_path, 'assist')
        if not os.path.exists(dl_path):
            self.show_error_page(TPE_HTTP_404_NOT_FOUND)
            return
        files = os.listdir(dl_path)
        files.sort(reverse=True)
        name = None
        for f in files:
            if f.startswith('teleport-assist-{}-'.format(os_type)):
                name = f
                break
        if not name:
            self.show_error_page(TPE_HTTP_404_NOT_FOUND)
            return

        filename = os.path.join(dl_path, name)
        file_size = os.path.getsize(filename)

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename="{}"'.format(name))
        self.set_header('Content-Length', file_size)

        # read most 8192 bytes one time.
        BULK_SIZE = 8192
        total_read = 0
        with open(filename, 'rb') as f:
            read_this_time = BULK_SIZE if (file_size - total_read) > BULK_SIZE else (file_size - total_read)
            while read_this_time > 0:
                self.write(f.read(read_this_time))
                self.flush()
                total_read += read_this_time
                if total_read >= file_size:
                    break
                read_this_time = BULK_SIZE if (file_size - total_read) > BULK_SIZE else (file_size - total_read)
