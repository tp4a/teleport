# -*- coding: utf-8 -*-
def get_config_list():
    try:
        from eom_app.module.common import get_db_con
        from eom_app.module.common import DbItem
        sql_exec = get_db_con()
        field_a = ['name', 'value']
        string_sql = 'SELECT {} FROM ts_config as a ;'.format(','.join(['a.{}'.format(i) for i in field_a]))
        db_ret = sql_exec.ExecProcQuery(string_sql)
        h = dict()
        for item in db_ret:
            x = DbItem()
            x.load(item, ['a_{}'.format(i) for i in field_a])
            h[x.a_name] = x.a_value

        return h
    except Exception as e:
        return None


def set_config(change_list):
    from eom_app.module.common import get_db_con
    sql_exec = get_db_con()
    #
    for item in change_list:
        name = item['name']
        value = item['value']
        str_sql = 'UPDATE ts_config SET value = \'{}\' ' \
                  '  WHERE name = \'{}\''.format(value, name)
        ret = sql_exec.ExecProcNonQuery(str_sql)

    return ret
