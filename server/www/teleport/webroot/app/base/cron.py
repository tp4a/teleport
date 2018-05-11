# -*- coding: utf-8 -*-

import datetime
import time
import threading

from app.base.logger import log


class TPCron(threading.Thread):
    def __init__(self):
        super().__init__(name='tp-cron-thread')

        import builtins
        if '__tp_cron__' in builtins.__dict__:
            raise RuntimeError('TPCron object exists, you can not create more than one instance.')

        # job表，session_id为索引，每个项为一个字典，包括 f(要执行的回调函数), t(最后一次执行的时间), i(间隔时间)
        self._jobs = dict()

        self._lock = threading.RLock()
        self._stop_flag = False

    def init(self):
        return True

    def add_job(self, name, func, first_interval_seconds=None, interval_seconds=60):
        # 加入一个待执行的任务， first_interval 为从加入开始算起到首次执行时的间隔时间，为None则立即执行
        # interval 为两次执行之间的间隔时间
        with self._lock:
            if name in self._jobs:
                return False
            self._jobs[name] = {'f': func, 't': 0, 'i': interval_seconds}
            _now = int(datetime.datetime.utcnow().timestamp())
            if first_interval_seconds is not None:
                self._jobs[name]['t'] = _now + first_interval_seconds - interval_seconds

    def stop(self):
        self._stop_flag = True
        self.join()
        log.v('{} stopped.\n'.format(self.name))

    def run(self):
        while not self._stop_flag:
            time.sleep(1)

            with self._lock:
                _now = int(datetime.datetime.utcnow().timestamp())
                for j in self._jobs:
                    # log.v('--now: {}, job-name: {}, job-t: {}, job-i: {}\n'.format(_now, j, self._jobs[j]['t'], self._jobs[j]['i']))
                    if _now - self._jobs[j]['t'] >= self._jobs[j]['i']:
                        self._jobs[j]['t'] = _now
                        try:
                            self._jobs[j]['f']()
                        except:
                            log.e('got exception when exec job: {}\n'.format(j))


def tp_cron():
    """
    取得TPCron管理器的唯一实例

    :rtype : TPCron
    """

    import builtins
    if '__tp_cron__' not in builtins.__dict__:
        builtins.__dict__['__tp_cron__'] = TPCron()
    return builtins.__dict__['__tp_cron__']
