# -*- coding: utf-8 -*-

from app.const import *
from app.base.db import get_db
from app.base.configs import tp_cfg
from app.base.utils import tp_timestamp_utc_now


def get_basic_stats():
    db = get_db()
    ret = {'user': 1,
           'host': 0,
           'acc': 0,
           'conn': 0
           }

    if db.need_create or db.need_upgrade:
        return TPE_EXISTS, ret

    sql = 'SELECT COUNT(*) FROM `{tpdb}user`;'.format(tpdb=db.table_prefix)
    db_ret = db.query(sql)
    if not db_ret or len(db_ret) == 0:
        pass
    else:
        ret['user'] = db_ret[0][0]

    sql = 'SELECT COUNT(*) FROM `{tpdb}host`;'.format(tpdb=db.table_prefix)
    db_ret = db.query(sql)
    if not db_ret or len(db_ret) == 0:
        pass
    else:
        ret['host'] = db_ret[0][0]

    sql = 'SELECT COUNT(*) FROM `{tpdb}acc`;'.format(tpdb=db.table_prefix)
    db_ret = db.query(sql)
    if not db_ret or len(db_ret) == 0:
        pass
    else:
        ret['acc'] = db_ret[0][0]

    sql = 'SELECT COUNT(*) FROM `{tpdb}record` WHERE `state` IN ({sess_running},{sess_started});'.format(tpdb=db.table_prefix, sess_running=TP_SESS_STAT_RUNNING, sess_started=TP_SESS_STAT_STARTED)
    db_ret = db.query(sql)
    if not db_ret or len(db_ret) == 0:
        pass
    else:
        ret['conn'] = db_ret[0][0]

    return TPE_OK, ret


def update_temp_locked_user_state():
    sys_cfg = tp_cfg().sys
    if sys_cfg.login.lock_timeout == 0:
        return

    _lock_time = tp_timestamp_utc_now() - (sys_cfg.login.lock_timeout * 60)
    db = get_db()
    if db.need_create or db.need_upgrade:
        return

    sql = 'UPDATE `{}user` SET state={new_state}, lock_time=0, fail_count=0 WHERE (state={old_state} AND lock_time<{lock_time});' \
          ''.format(db.table_prefix, new_state=TP_STATE_NORMAL, old_state=TP_STATE_LOCKED, lock_time=_lock_time)
    db.exec(sql)
