# -*- coding: utf-8 -*-

from .common import *
import time


# 获取主机列表，包括主机的基本信息
def get_all_host_info_list(filter, order, limit, with_pwd=False):
    sql_exec = get_db_con()

    _where = ''

    if len(filter) > 0:
        _where = 'WHERE ( '

        need_and = False
        for k in filter:
            if k == 'host_group':
                if need_and:
                    _where += ' AND'
                _where += ' b.group_id={}'.format(filter[k])
                need_and = True
            elif k == 'host_sys_type':
                if need_and:
                    _where += ' AND'
                _where += ' a.host_sys_type={}'.format(filter[k])
                need_and = True
            elif k == 'search':
                # 查找，限于主机ID和IP地址，前者是数字，只能精确查找，后者可以模糊匹配
                # 因此，先判断搜索项能否转换为数字。

                if need_and:
                    _where += ' AND '

                _where += '('
                _where += 'a.host_ip LIKE "%{}%" OR a.host_desc LIKE "%{}%" )'.format(filter[k], filter[k], filter[k])
                need_and = True
        _where += ')'

    # http://www.jb51.net/article/46015.htm
    field_a = ['host_id', 'host_lock', 'host_ip', 'host_port', 'protocol', 'host_desc', 'group_id', 'host_sys_type']
    field_b = ['group_name']

    # field_c = ['id', 'auth_mode', 'user_name']

    str_sql = 'SELECT COUNT(*) ' \
              'FROM ts_host_info AS a ' \
              'LEFT JOIN ts_group AS b ON a.group_id = b.group_id ' \
              '{};'.format(_where)

    db_ret = sql_exec.ExecProcQuery(str_sql)
    total_count = db_ret[0][0]

    # 修正分页数据
    _limit = ''
    if len(limit) > 0:
        _page_index = limit['page_index']
        _per_page = limit['per_page']
        _limit = 'LIMIT {},{}'.format(_page_index * _per_page, (_page_index + 1) * _per_page)

        if _page_index * _per_page >= total_count:
            _page_index = int(total_count / _per_page)
            _limit = 'LIMIT {},{}'.format(_page_index * _per_page, (_page_index + 1) * _per_page)

    # 生成排序规则
    _order = ''
    if order is not None:
        _order = 'ORDER BY '
        if 'host_id' == order['name']:
            _order += 'a.host_id'
        elif 'ip' == order['name']:
            _order += 'a.host_ip'
        else:
            _order = ''

        if not order['asc'] and len(_order) > 0:
            _order += ' DESC'

    str_sql = 'SELECT {},{} ' \
              'FROM ts_host_info AS a ' \
              'LEFT JOIN ts_group AS b ON a.group_id = b.group_id ' \
              '{} {} {};'.format(
        ','.join(['a.{}'.format(i) for i in field_a]),
        ','.join(['b.{}'.format(i) for i in field_b]),
        _where, _order, _limit)

    db_ret = sql_exec.ExecProcQuery(str_sql)
    if db_ret is None:
        return 0, None

    ret = list()
    for item in db_ret:
        x = DbItem()
        x.load(item, ['a_{}'.format(i) for i in field_a] +
               ['b_{}'.format(i) for i in field_b])

        h = dict()
        h['host_id'] = x.a_host_id
        h['host_port'] = x.a_host_port
        h['protocol'] = x.a_protocol
        h['host_lock'] = x.a_host_lock
        h['host_ip'] = x.a_host_ip
        h['host_desc'] = x.a_host_desc
        h['group_id'] = x.a_group_id
        h['host_sys_type'] = x.a_host_sys_type
        group_name = '默认分组'
        if x.b_group_name is not None:
            group_name = x.b_group_name
        h['group_name'] = group_name

        # h['auth_list'] = list()
        # auth_list = h['auth_list']
        h['auth_list'] = sys_user_list(x.a_host_id, with_pwd)
        # auth = dict()
        # auth['host_auth_id'] = x.c_id
        # auth['auth_mode'] = x.c_auth_mode
        # auth['user_name'] = x.c_user_name
        # auth_list.append(auth)

        ret.append(h)
    return total_count, ret


def get_host_info_list_by_user(filter, order, limit):
    sql_exec = get_db_con()

    _where = ''

    # _where = ''

    # _where = 'WHERE ( a.account_name=\'{}\' '.format(uname)

    if len(filter) > 0:
        _where = 'WHERE ( '

        need_and = False
        for k in filter:
            if k == 'host_group':
                if need_and:
                    _where += ' AND'
                _where += ' b.group_id={}'.format(filter[k])
                need_and = True
            elif k == 'host_sys_type':
                if need_and:
                    _where += ' AND'
                _where += ' b.host_sys_type={}'.format(filter[k])
                need_and = True

            elif k == 'account_name':
                if need_and:
                    _where += ' AND'
                _where += ' a.account_name=\'{}\''.format(filter[k])
                need_and = True

            elif k == 'search':
                # 查找，限于主机ID和IP地址，前者是数字，只能精确查找，后者可以模糊匹配
                # 因此，先判断搜索项能否转换为数字。

                if need_and:
                    _where += ' AND '

                _where += '('
                _where += 'b.host_ip LIKE "%{}%" OR b.host_desc LIKE "%{}%" )'.format(filter[k], filter[k], filter[k])
                need_and = True

    _where += ')'

    # http://www.jb51.net/article/46015.htm
    field_a = ['auth_id', 'host_id', 'account_name', 'host_auth_id']
    field_b = ['host_id', 'host_lock', 'host_ip', 'protocol', 'host_port', 'host_desc', 'group_id', 'host_sys_type']
    field_c = ['group_name']
    field_d = ['auth_mode', 'user_name']
    str_sql = 'SELECT COUNT(DISTINCT a.host_id) ' \
              'FROM ts_auth AS a ' \
              'LEFT JOIN ts_host_info AS b ON a.host_id = b.host_id ' \
              '{};'.format(_where)

    db_ret = sql_exec.ExecProcQuery(str_sql)
    total_count = db_ret[0][0]

    # 修正分页数据
    _limit = ''
    if len(limit) > 0:
        _page_index = limit['page_index']
        _per_page = limit['per_page']
        _limit = 'LIMIT {},{}'.format(_page_index * _per_page, (_page_index + 1) * _per_page)

        if _page_index * _per_page >= total_count:
            _page_index = int(total_count / _per_page)
            _limit = 'LIMIT {},{}'.format(_page_index * _per_page, (_page_index + 1) * _per_page)

    # 生成排序规则
    _order = ''
    # log.d(order['name'])
    if order is not None:
        _order = 'ORDER BY '
        if 'host_id' == order['name']:
            _order += 'b.host_id'
        elif 'ip' == order['name']:
            _order += 'b.host_ip'
        else:
            _order = ''

        if not order['asc'] and len(_order) > 0:
            _order += ' DESC'

    str_sql = 'SELECT {}, {},{},{} ' \
              'FROM ts_auth AS a ' \
              'LEFT JOIN ts_host_info AS b ON a.host_id=b.host_id ' \
              'LEFT JOIN ts_group AS c ON b.group_id = c.group_id ' \
              'LEFT JOIN ts_auth_info AS d ON d.id = a.host_auth_id ' \
              '{} {} {};'.format(
        ','.join(['a.{}'.format(i) for i in field_a]),
        ','.join(['b.{}'.format(i) for i in field_b]),
        ','.join(['c.{}'.format(i) for i in field_c]),
        ','.join(['d.{}'.format(i) for i in field_d]),
        _where, _order, _limit)

    db_ret = sql_exec.ExecProcQuery(str_sql)
    ret = list()
    temp = dict()
    for item in db_ret:
        x = DbItem()
        x.load(item, ['a_{}'.format(i) for i in field_a] + ['b_{}'.format(i) for i in field_b] + ['c_{}'.format(i) for i in field_c] + ['d_{}'.format(i) for i in field_d])

        host_ip = x.b_host_ip
        protocol = x.b_protocol
        key = '{}-{}'.format(host_ip, protocol)
        temp_auth = None
        extend_auth_list = sys_user_list(x.b_host_id, False, x.a_host_auth_id)
        if extend_auth_list is not None and len(extend_auth_list) > 0:
            auth = extend_auth_list[0]
            auth['auth_id'] = x.a_auth_id
            temp_auth = auth
        add = False
        if key in temp:
            h = temp[key]
            auth_list = h['auth_list']
            auth_list.append(temp_auth)
            h['auth_list'] = auth_list
        else:
            h = dict()
            h['host_id'] = x.b_host_id
            h['host_lock'] = x.b_host_lock
            h['host_ip'] = host_ip
            h['host_port'] = x.b_host_port
            h['host_desc'] = x.b_host_desc
            h['group_id'] = x.b_group_id
            h['host_sys_type'] = x.b_host_sys_type
            h['protocol'] = x.b_protocol
            group_name = '默认分组'
            if x.c_group_name is not None:
                group_name = x.c_group_name
            h['group_name'] = group_name
            add = True
            temp[key] = h
            h['auth_list'] = list()
            auth_list = h['auth_list']
            auth_list.append(temp_auth)
            h['auth_list'] = auth_list

        if add:
            ret.append(h)

    return total_count, ret


def get_group_list():
    field_a = ['group_id', 'group_name']
    sql_exec = get_db_con()
    str_sql = 'SELECT {} ' \
              'FROM ts_group AS a; ' \
        .format(','.join(['a.{}'.format(i) for i in field_a]))
    db_ret = sql_exec.ExecProcQuery(str_sql)
    ret = list()
    for item in db_ret:
        x = DbItem()
        x.load(item, ['a_{}'.format(i) for i in field_a])
        h = dict()

        h['id'] = x.a_group_id
        h['group_name'] = x.a_group_name
        ret.append(h)
    return ret


# def get_config_list():
#     try:
#         sql_exec = get_db_con()
#         field_a = ['name', 'value']
#         string_sql = 'SELECT {} FROM ts_config as a ;'.format(','.join(['a.{}'.format(i) for i in field_a]))
#         db_ret = sql_exec.ExecProcQuery(string_sql)
#         h = dict()
#         for item in db_ret:
#             x = DbItem()
#             x.load(item, ['a_{}'.format(i) for i in field_a])
#             h[x.a_name] = x.a_value
#
#         return h
#     except:
#         return None


def update(host_id, kv):
    if len(kv) == 0:
        return False

    _val = ''
    for k in kv:
        if len(_val) > 0:
            _val += ','
        if k == 'desc':
            _val += 'host_desc="{}"'.format(kv[k])
        elif k == 'pro_port':
            temp = json.dumps(kv[k])
            _val += '{}=\'{}\''.format(k, temp)
        else:
            _val += '{}="{}"'.format(k, kv[k])

    str_sql = 'UPDATE ts_host_info SET {} ' \
              'WHERE host_id={};'.format(_val, host_id)

    sql_exec = get_db_con()
    db_ret = sql_exec.ExecProcNonQuery(str_sql)
    return db_ret


def get_cert_list():
    sql_exec = get_db_con()

    # http://www.jb51.net/article/46015.htm
    field_a = ['cert_id', 'cert_name', 'cert_pub', 'cert_pri', 'cert_desc']

    str_sql = 'SELECT {} ' \
              'FROM ts_key as a '.format(','.join(['a.{}'.format(i) for i in field_a]))

    db_ret = sql_exec.ExecProcQuery(str_sql)

    if db_ret is None:
        return None
    ret = list()
    for item in db_ret:
        x = DbItem()

        x.load(item, ['a_{}'.format(i) for i in field_a])
        h = dict()

        h['cert_id'] = x.a_cert_id
        if x.a_cert_name is None:
            x.a_cert_name = ''

        h['cert_name'] = x.a_cert_name
        h['cert_pub'] = x.a_cert_pub

        h['cert_pri'] = x.a_cert_pri
        if x.a_cert_desc is None:
            x.a_cert_desc = ''
        h['cert_desc'] = x.a_cert_desc
        ret.append(h)
    return ret


def add_host(args, must_not_exists=True):
    sql_exec = get_db_con()

    protocol = args['protocol']
    host_port = args['host_port']
    host_ip = args['host_ip']

    str_sql = 'SELECT host_id FROM ts_host_info WHERE (host_ip=\'{}\' and protocol={} and host_port={});' \
        .format(host_ip, protocol, host_port)
    db_ret = sql_exec.ExecProcQuery(str_sql)
    if db_ret is not None and len(db_ret) > 0:
        if not must_not_exists:
            return db_ret[0][0]
        else:
            return -100

    group_id = args['group_id']
    host_sys_type = args['host_sys_type']
    # pro_port = args['pro_port']
    # pro_port = json.dumps(pro_port)
    # host_user_name = args['user_name']
    # host_user_pwd = args['user_pwd']
    # host_pro_type = args['pro_type']
    # cert_id = args['cert_id']
    # host_encrypt = 1
    # host_auth_mode = args['host_auth_mode']
    host_desc = args['host_desc']
    if len(host_desc) == 0:
        host_desc = '描述未填写'
    host_lock = 0

    #
    str_sql = 'INSERT INTO ts_host_info (group_id, host_sys_type, host_ip, ' \
              'host_port, protocol, host_lock, host_desc) ' \
              'VALUES ({},{},\'{}\',' \
              '{},{},{},' \
              '\'{}\')'.format(group_id, host_sys_type, host_ip,
                               host_port, protocol, host_lock, host_desc)

    ret = sql_exec.ExecProcNonQuery(str_sql)
    if not ret:
        return -101

    str_sql = 'select last_insert_rowid()'
    db_ret = sql_exec.ExecProcQuery(str_sql)
    if db_ret is None:
        return -102
    host_id = db_ret[0][0]
    return host_id


def lock_host(host_id, lock):
    sql_exec = get_db_con()
    #
    str_sql = 'UPDATE ts_host_info SET host_lock = {} ' \
              '  WHERE host_id = {}'.format(lock, host_id)
    ret = sql_exec.ExecProcNonQuery(str_sql)
    return ret


def delete_host(host_list):
    sql_exec = get_db_con()
    #
    for item in host_list:
        host_id = int(item)
        str_sql = 'DELETE FROM ts_host_info WHERE host_id = {} '.format(host_id)
        ret = sql_exec.ExecProcNonQuery(str_sql)

        str_sql = 'DELETE FROM ts_auth_info WHERE host_id = {} '.format(host_id)
        ret = sql_exec.ExecProcNonQuery(str_sql)

        str_sql = 'DELETE FROM ts_auth WHERE host_id = {} '.format(host_id)
        ret = sql_exec.ExecProcNonQuery(str_sql)
    return True


def add_cert(cert_pub, cert_pri, cert_name):
    sql_exec = get_db_con()
    #
    str_sql = 'INSERT INTO ts_key (cert_pub, cert_pri, cert_name) VALUES (\'{}\',\'{}\',\'{}\')'.format(cert_pub, cert_pri, cert_name)
    ret = sql_exec.ExecProcNonQuery(str_sql)
    return ret


def delete_cert(cert_id):
    sql_exec = get_db_con()
    #
    str_sql = 'DELETE FROM ts_key WHERE cert_id = {} '.format(cert_id)
    ret = sql_exec.ExecProcNonQuery(str_sql)
    return ret


def update_cert(cert_id, cert_pub, cert_pri, cert_name):
    sql_exec = get_db_con()
    #

    if 0 == len(cert_pri):
        str_sql = 'UPDATE ts_key SET cert_pub = \'{}\', ' \
                  'cert_name = \'{}\'' \
                  '  WHERE cert_id = {}'.format(cert_pub, cert_name, cert_id)
    else:
        str_sql = 'UPDATE ts_key SET cert_pub = \'{}\', ' \
                  'cert_pri = \'{}\', cert_name = \'{}\'' \
                  '  WHERE cert_id = {}'.format(cert_pub, cert_pri, cert_name, cert_id)

    ret = sql_exec.ExecProcNonQuery(str_sql)
    return ret


def add_group(group_name):
    sql_exec = get_db_con()
    #
    str_sql = 'INSERT INTO ts_group (group_name) VALUES (\'{}\')'.format(group_name)
    ret = sql_exec.ExecProcNonQuery(str_sql)
    return ret


def delete_group(group_id):
    sql_exec = get_db_con()
    #
    string_sql = 'SELECT host_id FROM ts_host_info WHERE group_id = {};'.format(group_id)
    db_ret = sql_exec.ExecProcQuery(string_sql)
    if len(db_ret) != 0:
        return -2

    str_sql = 'DELETE FROM ts_group WHERE group_id = {} '.format(group_id)
    ret = sql_exec.ExecProcNonQuery(str_sql)
    if ret:
        return 0
    return -3


def update_group(group_id, group_name):
    sql_exec = get_db_con()
    str_sql = 'UPDATE ts_group SET group_name = \'{}\' ' \
              'WHERE group_id = {}'.format(group_name, group_id)
    ret = sql_exec.ExecProcNonQuery(str_sql)
    return ret


def add_host_to_group(host_list, group_id):
    sql_exec = get_db_con()
    for item in host_list:
        host_id = item
        str_sql = 'UPDATE ts_host_info SET  ' \
                  'group_id = {}' \
                  '  WHERE host_id = {}'.format(group_id, host_id)
        ret = sql_exec.ExecProcNonQuery(str_sql)
    return ret


def get_host_auth_info(host_auth_id):
    sql_exec = get_db_con()

    field_a = ['id', 'auth_mode', 'user_name', 'user_pswd', 'user_param', 'cert_id', 'encrypt']
    field_b = ['host_id', 'host_lock', 'host_ip', 'host_port', 'host_desc', 'group_id', 'host_sys_type', 'protocol']

    str_sql = 'SELECT {},{} ' \
              'FROM ts_auth_info AS a ' \
              'LEFT JOIN ts_host_info AS b ON a.host_id=b.host_id ' \
              'WHERE a.id = {}'.format(
        ','.join(['a.{}'.format(i) for i in field_a]),
        ','.join(['b.{}'.format(i) for i in field_b]), host_auth_id)
    db_ret = sql_exec.ExecProcQuery(str_sql)

    if db_ret is None or len(db_ret) != 1:
        return None
    x = DbItem()
    x.load(db_ret[0], ['a_{}'.format(i) for i in field_a] + ['b_{}'.format(i) for i in field_b])

    h = dict()
    h['host_ip'] = x.b_host_ip
    h['host_port'] = x.b_host_port
    h['sys_type'] = x.b_host_sys_type
    h['auth_mode'] = x.a_auth_mode
    h['user_name'] = x.a_user_name
    h['protocol'] = x.b_protocol

    if x.a_encrypt is None:
        h['encrypt'] = 1
    else:
        h['encrypt'] = x.a_encrypt

    if x.a_user_param is None:
        h['user_param'] = ''
    else:
        h['user_param'] = x.a_user_param

    h['user_auth'] = x.a_user_pswd

    if x.a_auth_mode == 1:
        h['user_auth'] = x.a_user_pswd
    elif x.a_auth_mode == 2:
        if x.a_cert_id is None:
            cert_id = 0
        else:
            cert_id = int(x.a_cert_id)  # int(user_auth)
        str_sql = 'SELECT cert_pri FROM ts_key WHERE cert_id = {}'.format(cert_id)
        db_ret = sql_exec.ExecProcQuery(str_sql)
        if db_ret is not None and len(db_ret) == 1:
            (cert_pri,) = db_ret[0]
            h['user_auth'] = cert_pri
        else:
            return None
    elif x.a_auth_mode == 0:
        h['user_auth'] = ''
    else:
        return None

    return h


def update_host_extend_info(host_id, args):
    sql_exec = get_db_con()

    ip = args['ip']
    port = int(args['port'])
    user_name = args['user_name']
    user_pwd = args['user_pwd']
    cert_id = int(args['cert_id'])
    pro_type = int(args['pro_type'])
    sys_type = int(args['sys_type'])
    group_id = args['group_id']
    host_desc = args['desc']
    host_auth_mode = int(args['host_auth_mode'])
    host_encrypt = 1

    # if len(user_pwd) == 0 and 0 == cert_id:
    #     return False
    if 0 == len(user_pwd):
        str_sql = 'UPDATE ts_host_info SET host_ip = \'{}\', ' \
                  'host_pro_port = {}, host_user_name = \'{}\', ' \
                  'cert_id = {}, host_pro_type = {},host_sys_type={}, group_id={},host_auth_mode={},host_encrypt={}, ' \
                  'host_desc=\'{}\' WHERE host_id = {}'.format(
            ip, port, user_name, cert_id, pro_type, sys_type, group_id, host_auth_mode, host_encrypt, host_desc, host_id)

    else:
        str_sql = 'UPDATE ts_host_info SET host_ip = \'{}\', ' \
                  'host_pro_port = {}, host_user_name = \'{}\', host_user_pwd = \'{}\', ' \
                  'cert_id = {}, host_pro_type = {},host_sys_type={}, group_id={},host_auth_mode={},host_encrypt={}, ' \
                  'host_desc=\'{}\' WHERE host_id = {}'.format(
            ip, port, user_name, user_pwd, cert_id, pro_type, sys_type, group_id, host_auth_mode, host_encrypt, host_desc, host_id)

    ret = sql_exec.ExecProcNonQuery(str_sql)
    return ret


def get_cert_info(cert_id):
    sql_exec = get_db_con()
    str_sql = 'SELECT cert_pri FROM ts_key WHERE cert_id = {}'.format(cert_id)
    db_ret = sql_exec.ExecProcQuery(str_sql)
    if db_ret is not None and len(db_ret) == 1:
        (cert_pri,) = db_ret[0]
        return cert_pri
    else:
        return None


def sys_user_list(host_id, with_pwd=True, host_auth_id=0):
    sql_exec = get_db_con()

    field_a = ['id', 'host_id', 'auth_mode', 'user_name', 'user_pswd', 'user_param', 'cert_id', 'log_time']
    if host_auth_id == 0:
        str_sql = 'SELECT {} ' \
                  'FROM ts_auth_info AS a ' \
                  'WHERE a.host_id = {};'.format(','.join(['a.{}'.format(i) for i in field_a]), host_id)
    else:
        str_sql = 'SELECT {} ' \
                  'FROM ts_auth_info AS a ' \
                  'WHERE a.id = {} and a.host_id = {};'.format(','.join(['a.{}'.format(i) for i in field_a]),
                                                               host_auth_id, host_id)

    db_ret = sql_exec.ExecProcQuery(str_sql)

    if db_ret is None:
        return None
    ret = list()
    for item in db_ret:
        x = DbItem()
        x.load(item, ['a_{}'.format(i) for i in field_a])

        h = dict()
        # h['id'] = x.a_id

        h['host_auth_id'] = x.a_id
        h['host_id'] = x.a_host_id
        # h['pro_type'] = x.a_pro_type
        h['auth_mode'] = x.a_auth_mode
        h['user_name'] = x.a_user_name
        if with_pwd:
            h['user_pswd'] = x.a_user_pswd

        if x.a_user_param is None:
            h['user_param'] = ''
        else:
            h['user_param'] = x.a_user_param

        h['cert_id'] = x.a_cert_id
        h['log_time'] = x.a_log_time
        # if x.a_auth_mode == 2:
        #     h['user_auth'] = x.a_user_auth
        # else:
        #     h['user_auth'] = "******"
        ret.append(h)

    return ret


def GetNowTime():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))


def sys_user_add(args):
    host_id = args['host_id']
    auth_mode = args['auth_mode']
    user_name = args['user_name']
    user_pswd = args['user_pswd']
    cert_id = args['cert_id']

    if 'user_param' in args:
        user_param = args['user_param']
    else:
        user_param = 'ogin:\nassword:'

    encrypt = 1

    sql_exec = get_db_con()

    # 判断此登录账号是否已经存在，如果存在则报错
    str_sql = 'SELECT id FROM ts_auth_info WHERE (host_id={} and auth_mode={} and user_name=\'{}\');' \
        .format(host_id, auth_mode, user_name)
    db_ret = sql_exec.ExecProcQuery(str_sql)
    if db_ret is not None and len(db_ret) > 0:
        return -100

    log_time = GetNowTime()

    if auth_mode == 1:
        str_sql = 'INSERT INTO ts_auth_info (host_id, auth_mode, user_name, user_pswd, user_param,' \
                  'encrypt, cert_id, log_time) ' \
                  'VALUES ({},{},\'{}\',\'{}\',\'{}\',{}, {},\'{}\')'.format(host_id, auth_mode, user_name, user_pswd, user_param, encrypt, 0, log_time)
    elif auth_mode == 2:
        str_sql = 'INSERT INTO ts_auth_info (host_id, auth_mode, user_name,user_param, ' \
                  'user_pswd,cert_id, encrypt, log_time) ' \
                  'VALUES ({},{},\'{}\',\'{}\',\'{}\',{},{}, \'{}\')'.format(host_id, auth_mode, user_name, user_param,
                                                                             '', cert_id, encrypt, log_time)
    elif auth_mode == 0:
        str_sql = 'INSERT INTO ts_auth_info (host_id, auth_mode, user_name,user_param, ' \
                  'user_pswd,cert_id, encrypt, log_time) ' \
                  'VALUES ({},{},\'{}\',\'{}\',\'{}\',{},{}, \'{}\')'.format(host_id, auth_mode, user_name, user_param,
                                                                             '', 0, encrypt, log_time)
    ret = sql_exec.ExecProcNonQuery(str_sql)
    if not ret:
        return -101

    str_sql = 'select last_insert_rowid()'
    db_ret = sql_exec.ExecProcQuery(str_sql)
    if db_ret is None:
        return -102
    user_id = db_ret[0][0]
    return user_id


def sys_user_update(_id, kv):
    if len(kv) == 0:
        return False

    _val = ''
    for k in kv:
        if len(_val) > 0:
            _val += ','

        _val += '{}="{}"'.format(k, kv[k])

    str_sql = 'UPDATE ts_auth_info SET {} ' \
              'WHERE id={};'.format(_val, _id)

    sql_exec = get_db_con()
    db_ret = sql_exec.ExecProcNonQuery(str_sql)
    return db_ret


def sys_user_delete(_id):
    sql_exec = get_db_con()
    try:
        str_sql = 'DELETE FROM ts_auth_info WHERE id = {} '.format(_id)
        ret = sql_exec.ExecProcNonQuery(str_sql)

        str_sql = 'DELETE FROM ts_auth WHERE host_auth_id = {} '.format(_id)
        ret = sql_exec.ExecProcNonQuery(str_sql)
    except Exception as e:
        return False

    return True


def get_auth_info(auth_id):
    """
    根据指定的auth_id查询相关的认证信息（远程主机IP、端口、登录用户名、登录密码或私钥，等等）
    @param auth_id: integer
    @return:
    """
    sql_exec = get_db_con()

    field_a = ['auth_id', 'account_name', 'host_auth_id', 'host_id']
    field_b = ['host_sys_type', 'host_ip', 'host_port', 'protocol']
    field_c = ['user_pswd', 'cert_id', 'user_name', 'encrypt', 'auth_mode', 'user_param']
    field_d = ['account_lock']

    str_sql = 'SELECT {},{},{},{} ' \
              'FROM ts_auth AS a ' \
              'LEFT JOIN ts_host_info AS b ON a.host_id = b.host_id ' \
              'LEFT JOIN ts_auth_info AS c ON a.host_auth_id = c.id ' \
              'LEFT JOIN ts_account AS d ON a.account_name = d.account_name ' \
              'WHERE a.auth_id={};'.format(
        ','.join(['a.{}'.format(i) for i in field_a]),
        ','.join(['b.{}'.format(i) for i in field_b]),
        ','.join(['c.{}'.format(i) for i in field_c]),
        ','.join(['d.{}'.format(i) for i in field_d]),
        auth_id)

    db_ret = sql_exec.ExecProcQuery(str_sql)

    if db_ret is None or len(db_ret) != 1:
        return None

    db_item = DbItem()

    db_item.load(db_ret[0],
                 ['a_{}'.format(i) for i in field_a] +
                 ['b_{}'.format(i) for i in field_b] +
                 ['c_{}'.format(i) for i in field_c] +
                 ['d_{}'.format(i) for i in field_d]
                 )

    ret = dict()
    ret['host_ip'] = db_item.b_host_ip
    ret['sys_type'] = db_item.b_host_sys_type
    ret['account_name'] = db_item.a_account_name
    ret['account_lock'] = db_item.d_account_lock
    # h['host_lock'] = x.a_host_lock
    ret['host_port'] = db_item.b_host_port
    ret['protocol'] = db_item.b_protocol
    ret['encrypt'] = db_item.c_encrypt
    ret['auth_mode'] = db_item.c_auth_mode
    ret['user_name'] = db_item.c_user_name
    ret['user_param'] = db_item.c_user_param

    if db_item.c_auth_mode == 1:
        ret['user_auth'] = db_item.c_user_pswd
    elif db_item.c_auth_mode == 2:
        cert_id = db_item.c_cert_id

        str_sql = 'SELECT cert_pri FROM ts_key WHERE cert_id={}'.format(cert_id)
        db_ret = sql_exec.ExecProcQuery(str_sql)
        if db_ret is None or len(db_ret) > 1:
            return None
        ret['user_auth'] = db_ret[0][0]
    else:
        pass

    return ret
