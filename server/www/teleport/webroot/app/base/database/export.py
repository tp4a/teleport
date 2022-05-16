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


def _export_table(db, table_name):
    table_name = '{}{}'.format(db.table_prefix, table_name)
    f = db.get_fields(table_name)
    fields = [i[0] for i in f]
    types = [i[1] for i in f]
    if fields is None:
        return '错误：表 {} 不存在'.format(table_name)
    s = list()
    for t in types:
        if (t.lower().find('char') != -1) or (t.lower().find('text') != -1):
            s.append(True)
        else:
            s.append(False)

    ret = ['', '-- table: {}'.format(table_name), '-- fields: {}'.format(', '.join(fields)), 'TRUNCATE TABLE `{}`;'.format(table_name)]

    fields_str = '`,`'.join(fields)
    sql = 'SELECT `{}` FROM `{}`'.format(fields_str, table_name)
    d = db.query(sql)
    if not d or len(d) == 0:
        ret.append('-- table is empty.')
    else:
        fields_count = len(fields)
        for i in range(len(d)):
            x = list()
            for j in range(fields_count):
                if s[j]:
                    if d[i][j] is None:
                        x.append('NULL')
                    else:
                        x.append('"{}"'.format(d[i][j].replace(r'"', r'\"')))
                else:
                    x.append('{}'.format(d[i][j]))
            val = ','.join(x)

            sql = "INSERT INTO `{}` VALUES ({});".format(table_name, val)
            ret.append(sql)

    return '\n'.join(ret)


def export_database(db):
    ret = []
    now = time.localtime(time.time())
    ret.append('-- {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} '.format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec))
    if db.db_type == db.DB_TYPE_SQLITE:
        ret.append('-- export from Teleport SQLite Database')
    elif db.db_type == db.DB_TYPE_MYSQL:
        ret.append('-- export from Teleport MySQL Database')
    else:
        return '未知的数据库类型', False

    db_ret = db.query('SELECT `value` FROM `{}config` WHERE `name`="db_ver";'.format(db.table_prefix))
    if db_ret is None or 0 == len(db_ret):
        return '无法获取数据库版本', False
    else:
        ret.append('-- TELEPORT DATABASE VERSION {}'.format(db_ret[0][0]))

    ret.append(_export_table(db, 'config'))
    ret.append(_export_table(db, 'core_server'))
    ret.append(_export_table(db, 'role'))
    ret.append(_export_table(db, 'user'))
    ret.append(_export_table(db, 'user_rpt'))
    ret.append(_export_table(db, 'host'))
    ret.append(_export_table(db, 'acc'))
    ret.append(_export_table(db, 'acc_auth'))
    ret.append(_export_table(db, 'group'))
    ret.append(_export_table(db, 'group_map'))
    ret.append(_export_table(db, 'ops_policy'))
    ret.append(_export_table(db, 'ops_auz'))
    ret.append(_export_table(db, 'ops_map'))
    ret.append(_export_table(db, 'audit_policy'))
    ret.append(_export_table(db, 'audit_auz'))
    ret.append(_export_table(db, 'audit_map'))
    ret.append(_export_table(db, 'syslog'))
    ret.append(_export_table(db, 'record'))
    ret.append(_export_table(db, 'record_audit'))

    return '\n'.join(ret), True
