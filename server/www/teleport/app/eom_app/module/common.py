# -*- coding: utf-8 -*-

import eom_common.eomcore.eom_mysql as mysql
import eom_common.eomcore.eom_sqlite as sqlite
# from eom_app.app.configs import app_cfg

# cfg = app_cfg()


class DbItem(dict):
    def load(self, db_item, db_fields):
        if len(db_fields) != len(db_item):
            raise RuntimeError('!=')
        for i in range(len(db_item)):
            self[db_fields[i]] = db_item[i]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise


def get_db_con():
    if False:
        sql_exec = mysql.get_mysql_pool().get_tssqlcon()
    else:
        sql_exec = sqlite.get_sqlite_pool().get_tssqlcon()
    return sql_exec

