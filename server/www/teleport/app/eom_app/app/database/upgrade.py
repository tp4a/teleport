# -*- coding: utf-8 -*-

from eom_app.app.util import sec_generate_password
from eom_common.eomcore.logger import log


def _db_exec(db, step_begin, step_end, msg, sql):
    _step = step_begin(msg)

    ret = db.exec(sql)
    if not ret:
        step_end(_step, -1)
        raise RuntimeError('[FAILED] {}'.format(sql))
    else:
        step_end(_step, 0)


def upgrade_database(db, step_begin, step_end, db_ver):
    try:
        pass
        return True
    except:
        log.e('ERROR')
        return False
