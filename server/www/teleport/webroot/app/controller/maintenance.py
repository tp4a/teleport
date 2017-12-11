# -*- coding: utf-8 -*-

import json
import threading

from app.const import *
from app.base.configs import tp_cfg
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
from app.base.db import get_db

cfg = tp_cfg()


class IndexHandler(TPBaseHandler):
    def get(self):
        self.render('maintenance/index.mako')


class InstallHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_CONFIG)
        if ret != TPE_OK:
            return

        if get_db().need_create:
            cfg.reload()

            _db = get_db()
            _db.init()

            db = {'type': _db.db_type}
            if _db.db_type == _db.DB_TYPE_SQLITE:
                db['sqlite_file'] = _db.sqlite_file
            elif _db.db_type == _db.DB_TYPE_MYSQL:
                db['mysql_host'] = _db.mysql_host
                db['mysql_port'] = _db.mysql_port
                db['mysql_user'] = _db.mysql_user
                db['mysql_db'] = _db.mysql_db

            param = {'db': db}
            self.render('maintenance/install.mako', page_param=json.dumps(param))
        elif get_db().need_upgrade:
            return self.redirect('/maintenance/upgrade')
        else:
            self.redirect('/')


class UpgradeHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_CONFIG)
        if ret != TPE_OK:
            return

        if get_db().need_create:
            return self.redirect('/maintenance/install')
        elif get_db().need_upgrade:
            self.render('maintenance/upgrade.mako')
        else:
            self.redirect('/')


class RpcThreadManage:
    def __init__(self):
        self._lock = threading.RLock()
        self._threads = dict()
        self._id_base = 0

    def create_db(self, sysadmin, email, password):
        with self._lock:
            self._id_base += 1
            task_id = self._id_base

            t = threading.Thread(target=self._create_db, args=[task_id, sysadmin, email, password])
            self._threads[task_id] = {'cmd': 'create_db', 'running': True, 'stop': False, 'steps': list()}
            t.start()

        return task_id

    def upgrade_db(self):
        with self._lock:
            self._id_base += 1
            task_id = self._id_base

            t = threading.Thread(target=self._upgrade_db, args=[task_id])
            self._threads[task_id] = {'cmd': 'create_db', 'running': True, 'stop': False, 'steps': list()}
            t.start()

        return task_id

    def get_task(self, task_id):
        with self._lock:
            if task_id in self._threads:
                # msg = list()
                # for i in range(len(self._threads[task_id]['sub_tasks'])):
                #     msg.append({'ip': self._threads[task_id]['sub_tasks'][i]['ip'], 'msg': self._threads[task_id]['sub_tasks'][i]['msg']})

                ret = {
                    'cmd': self._threads[task_id]['cmd'],
                    'running': self._threads[task_id]['running'],
                    # 'stop': self._threads[task_id]['stop'],
                    'steps': self._threads[task_id]['steps']
                }
                if not self._threads[task_id]['running']:
                    del self._threads[task_id]
                return ret
            else:
                return None

    def stop_task(self, task_id):
        with self._lock:
            if task_id in self._threads:
                self._threads[task_id]['msg'] = '正在终止...'
                self._threads[task_id]['stop'] = True

    def _create_db(self, tid, sysadmin, email, password):
        def _step_begin(msg):
            return self._step_begin(tid, msg)

        def _step_end(sid, code, msg=None):
            self._step_end(tid, sid, code, msg)

        if get_db().create_and_init(_step_begin, _step_end, sysadmin, email, password):
            cfg.app_mode = APP_MODE_NORMAL

        # self._step_begin(tid, '操作已完成')

        self._thread_end(tid)

    def _upgrade_db(self, tid):
        def _step_begin(msg):
            return self._step_begin(tid, msg)

        def _step_end(sid, code, msg=None):
            self._step_end(tid, sid, code, msg)

        if get_db().upgrade_database(_step_begin, _step_end):
            cfg.app_mode = APP_MODE_NORMAL

        # self._step_begin(tid, '操作已完成')

        self._thread_end(tid)

    def _step_begin(self, tid, msg):
        with self._lock:
            if len(self._threads[tid]['steps']) > 0:
                self._threads[tid]['steps'][-1]['stat'] = 0  # 0 表示此步骤已完成
            self._threads[tid]['steps'].append({'stat': 1, 'code': 0, 'msg': msg})

            return len(self._threads[tid]['steps']) - 1

    def _step_end(self, tid, sid, code, msg=None):
        with self._lock:
            try:
                self._threads[tid]['steps'][sid]['code'] = code
                self._threads[tid]['steps'][sid]['stat'] = 0  # 0 表示此步骤已完成
                if msg is not None:
                    self._threads[tid]['steps'][sid]['msg'] = '{}{}'.format(self._threads[tid]['steps'][sid]['msg'], msg)
            except:
                pass

    def _thread_end(self, tid):
        with self._lock:
            if tid in self._threads:
                self._threads[tid]['running'] = False
                if self._threads[tid]['stop']:
                    sid = self._step_begin(tid, '操作被终止')
                    self._step_end(tid, sid, -1)
                if len(self._threads[tid]['steps']) > 0:
                    self._threads[tid]['steps'][-1]['stat'] = 0


thread_mgr = RpcThreadManage()


class RpcHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_SYS_CONFIG)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is not None:
            try:
                args = json.loads(args)
            except:
                return self.write_json(TPE_JSON_FORMAT)
        else:
            return self.write_json(TPE_PARAM)

        if 'cmd' not in args:
            return self.write_json(TPE_PARAM)

        cmd = args['cmd']
        # if cmd == 'enter_maintenance_mode':
        #     cfg.app_mode = APP_MODE_MAINTENANCE
        #     return self.write_json(0)

        if cmd == 'install':
            if not get_db().need_create:
                return self.write_json(TPE_FAILED, '数据库已存在，无需创建！')

            if 'sysadmin' not in args or 'email' not in args or 'password' not in args:
                return self.write_json(TPE_PARAM)

            task_id = thread_mgr.create_db(args['sysadmin'], args['email'], args['password'])
            return self.write_json(0, data={"task_id": task_id})

        if cmd == 'upgrade_db':
            if not get_db().need_upgrade:
                return self.write_json(-1, '无需升级')
            task_id = thread_mgr.upgrade_db()
            return self.write_json(0, data={"task_id": task_id})

        elif cmd == 'get_task_ret':
            r = thread_mgr.get_task(args['tid'])
            if r is None:
                return self.write_json(0, data={'running': False, 'steps': []})
            else:
                return self.write_json(0, data=r)

        else:
            self.write_json(-1, '未知命令 `{}`！'.format(cmd))
