# -*- coding: utf-8 -*-
import datetime

from app.const import *
from app.base.cron import tp_cron
from app.base.configs import tp_cfg
from app.base.logger import log
from app.model import ops
from app.model import record


def tp_init_jobs():
    cron = tp_cron()

    # 每隔一个小时清理一次过期的远程连接授权码
    cron.add_job('clean_expired_ops_token', _job_clean_expired_ops_token, first_interval_seconds=10, interval_seconds=3600)

    # 每50秒检查一下是否要到了每日清理系统日志和会话记录的时间了，到了则执行清理操作
    cron.add_job('check_and_clean_log_and_record', _job_clean_log_and_record, interval_seconds=50)

    return True


def _job_clean_expired_ops_token():
    log.v('clean expired ops token.\n')
    ops.clean_expired_ops_token()


def _job_clean_log_and_record():
    sto = tp_cfg().sys.storage
    if sto.keep_log == 0 or sto.keep_record == 0:
        # nothing need remove
        return

    now = datetime.datetime.now()
    if not (now.hour == sto.cleanup_hour and now.minute == sto.cleanup_minute):
        return

    log.v('[cron] time to clean log and record.\n')
    err, msg = record.cleanup_log_and_record()
    for m in msg:
        log.v('[cron] {}\n'.format(m))
