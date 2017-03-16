# -*- coding: utf-8 -*-

import json
import time
import threading
from .base import TPBaseUserAuthHandler, TPBaseAdminAuthHandler, TPBaseAdminAuthJsonHandler
from eom_app.app.db import get_db


class IndexHandler(TPBaseUserAuthHandler):
    def get(self):
        self.render('maintenance/index.mako')


class InstallHandler(TPBaseAdminAuthHandler):
    def get(self):
        if get_db().need_upgrade:
            return self.redirect('/maintenance/upgrade')

        self.render('maintenance/install.mako')


class UpgradeHandler(TPBaseAdminAuthHandler):
    def get(self):
        if get_db().need_create:
            return self.redirect('/maintenance/install')

        self.render('maintenance/upgrade.mako')


class RpcThreadManage:
    def __init__(self):
        self._lock = threading.RLock()
        self._threads = dict()
        self._id_base = 0

    def create_db(self):
        with self._lock:
            self._id_base += 1
            task_id = self._id_base

            t = threading.Thread(target=self._create_db, args=[task_id])
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

    def _create_db(self, tid):
        time.sleep(2)
        self._add_step_result(tid, 0, '正在初始化 1...')
        self._add_step_result(tid, 0, '正在初始化 2...')
        self._add_step_result(tid, 0, '正在初始化 3...')
        self._add_step_result(tid, 0, '正在初始化 4...')

        # self._threads[tid]['steps'].append({'stat': 0, 'msg': '执行已结束'})
        # if self._threads[tid]['stop']:
        #     self._add_step_result(tid, -1, '操作被终止')
        self._thread_end(tid)

    def _add_step_result(self, tid, code, msg):
        if len(self._threads[tid]['steps']) > 0:
            self._threads[tid]['steps'][-1]['stat'] = 0  # 0 表示此步骤已完成
        self._threads[tid]['steps'].append({'stat': 1, 'code': code, 'msg': msg})

    def _thread_end(self, tid):
        with self._lock:
            if tid in self._threads:
                self._threads[tid]['running'] = False
                if self._threads[tid]['stop']:
                    self._add_step_result(tid, -1, '操作被终止')
                if len(self._threads[tid]['steps']) > 0:
                    self._threads[tid]['steps'][-1]['stat'] = 0


thread_mgr = RpcThreadManage()


class RpcHandler(TPBaseAdminAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        # print('args', args)
        if args is not None:
            args = json.loads(args)
        else:
            self.write_json(-1)
            return

        # print(args)

        cmd = args['cmd']
        if cmd == 'create_db':
            if not get_db().need_create:
                return self.write_json(-1)
            task_id = thread_mgr.create_db()
            return self.write_json(0, data={"task_id": task_id})

        elif cmd == 'get_task_ret':
            # return self.write_json(-1)
            r = thread_mgr.get_task(args['tid'])
            if r is None:
                return self.write_json(0, data={'running': False, 'msg': []})
            else:
                # del r['stop']
                return self.write_json(0, data=r)

        else:
            self.write_json(-1, '未知命令 `{}`！'.format(cmd))
