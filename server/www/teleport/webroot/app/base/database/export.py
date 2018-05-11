# -*- coding: utf-8 -*-

import time


def _db_exec(db, step_begin, step_end, msg, sql):
    _step = step_begin(msg)

    ret = db.exec(sql)
    if not ret:
        step_end(_step, -1)
        raise RuntimeError('[FAILED] {}'.format(sql))
    else:
        step_end(_step, 0)


def _export_table(db, table_name, fields):
    ret = ['', '-- table: {}'.format(table_name), '-- fields: {}'.format(', '.join(fields)), 'TRUNCATE TABLE `{}`;'.format(table_name)]

    fields_str = '`,`'.join(fields)
    sql = 'SELECT `{}` FROM `{}{}`'.format(fields_str, db.table_prefix, table_name)
    d = db.query(sql)
    if not d or len(d) == 0:
        ret.append('-- table is empty.')
    else:
        fields_count = len(fields)
        for i in range(len(d)):
            x = []
            for j in range(fields_count):
                x.append(d[i][j].__str__())
            val = "','".join(x).replace('\n', '\\n')
            sql = "INSERT INTO `{}` VALUES ('{}');".format(table_name, val)
            ret.append(sql)

    return '\r\n'.join(ret)


def export_database(db):
    ret = []
    now = time.localtime(time.time())
    ret.append('-- {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} '.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec))
    if db.db_type == db.DB_TYPE_SQLITE:
        ret.append('-- export from SQLite Database')
    elif db.db_type == db.DB_TYPE_MYSQL:
        ret.append('-- export from MySQL Database')
    else:
        return '未知的数据库类型', False

    db_ret = db.query('SELECT `value` FROM `{}config` WHERE `name`="db_ver";'.format(db.table_prefix))
    if db_ret is None or 0 == len(db_ret):
        return '无法获取数据库版本', False
    else:
        ret.append('-- DATABASE VERSION {}'.format(db_ret[0][0]))

    _fields = ['account_id', 'account_type', 'account_name', 'account_pwd', 'account_status', 'account_lock', 'account_desc', 'oath_secret']
    ret.append(_export_table(db, 'account', _fields))
    _fields = ['auth_id', 'account_name', 'host_id', 'host_auth_id']
    ret.append(_export_table(db, 'auth', _fields))
    _fields = ['cert_id', 'cert_name', 'cert_pub', 'cert_pri', 'cert_desc']
    ret.append(_export_table(db, 'key', _fields))
    _fields = ['name', 'value']
    ret.append(_export_table(db, 'config', _fields))
    _fields = ['group_id', 'group_name']
    ret.append(_export_table(db, 'group', _fields))
    _fields = ['host_id', 'group_id', 'host_sys_type', 'host_ip', 'host_port', 'protocol', 'host_lock', 'host_desc']
    ret.append(_export_table(db, 'host_info', _fields))
    _fields = ['id', 'host_id', 'auth_mode', 'user_name', 'user_pswd', 'user_param', 'cert_id', 'encrypt', 'log_time']
    ret.append(_export_table(db, 'auth_info', _fields))
    _fields = ['id', 'session_id', 'account_name', 'host_ip', 'host_port', 'sys_type', 'auth_type', 'protocol', 'user_name', 'ret_code', 'begin_time', 'end_time', 'log_time']
    ret.append(_export_table(db, 'log', _fields))

    return '\r\n'.join(ret), True
