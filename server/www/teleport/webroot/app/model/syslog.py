# -*- coding: utf-8 -*-

from app.const import *
from app.base.db import get_db, SQL
from app.base.logger import log
from app.base.utils import tp_timestamp_utc_now


def sys_log(operator, client_ip, code, message=""):
    try:
        db = get_db()
        sql = 'INSERT INTO `{}syslog` (user_name,user_surname,client_ip,code,log_time,message) ' \
              'VALUES ("{user_name}","{user_surname}","{client_ip}",{code},{log_time},"{message}")' \
              ';'.format(db.table_prefix,
                         user_name=operator['username'], user_surname=operator['surname'], client_ip=client_ip, code=code,
                         log_time=tp_timestamp_utc_now(), message=message
                         )

        ret = db.exec(sql)
        if not ret:
            return TPE_DATABASE

        return TPE_OK

    except:
        log.e('\n')
        return TPE_DATABASE


def get_logs(sql_filter, sql_order, sql_limit):
    s = SQL(get_db())
    s.select_from('syslog', ['id', 'user_name', 'user_surname', 'client_ip', 'code', 'log_time', 'message'], alt_name='l')

    str_where = ''
    _where = list()

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'log_user_name':
                _where.append('l.user_name="{}"'.format(sql_filter[k]))
            # elif k == 'search_record':
            #     _where.append('(h.name LIKE "%{}%" OR h.ip LIKE "%{}%" OR h.router_addr LIKE "%{}%" OR h.desc LIKE "%{}%" OR h.cid LIKE "%{}%")'.format(sql_filter[k], sql_filter[k], sql_filter[k], sql_filter[k], sql_filter[k]))

    if len(_where) > 0:
        str_where = '( {} )'.format(' AND '.join(_where))

    s.where(str_where)

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'log_time' == sql_order['name']:
            s.order_by('l.log_time', _sort)
        # elif 'name' == sql_order['name']:
        #     s.order_by('h.name', _sort)
        # elif 'os_type' == sql_order['name']:
        #     s.order_by('h.os_type', _sort)
        # elif 'cid' == sql_order['name']:
        #     s.order_by('h.cid', _sort)
        # elif 'state' == sql_order['name']:
        #     s.order_by('h.state', _sort)
        else:
            log.e('unknown order field: {}\n'.format(sql_order['name']))
            return TPE_PARAM, s.total_count, s.recorder

    if len(sql_limit) > 0:
        s.limit(sql_limit['page_index'], sql_limit['per_page'])

    err = s.query()
    return err, s.total_count, s.recorder
