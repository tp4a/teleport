# -*- coding: utf-8 -*-

from app.base.cron import tp_cron
from app.model import ops


def tp_init_jobs():
    cron = tp_cron()

    # 每隔一个小时清理一次过期的远程连接授权码
    cron.add_job('clean_expired_ops_token', _job_clean_expired_ops_token, first_interval_seconds=10, interval_seconds=3600)

    return True


def _job_clean_expired_ops_token():
    ops.clean_expired_ops_token()
