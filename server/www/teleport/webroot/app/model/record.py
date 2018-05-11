# -*- coding: utf-8 -*-

import os
import io
import shutil
import struct
import base64

from app.const import *
from app.base.configs import tp_cfg
from app.base.db import get_db, SQL
from app.base.logger import log
from app.base.utils import tp_timestamp_utc_now
import tornado.gen


def get_records(handler, sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude):
    """
    获取会话列表
    会话审计列表的显示策略（下列的`审计`操作指为会话做标记、置为保留状态、写备注等）：
     1. 运维权限：可以查看自己的会话，但不能审计；
     2. 运维授权权限：可以查看所有会话，但不能审计；
     3. 审计权限：可以查看被授权的主机相关的会话，且可以审计；
     4. 审计授权权限：可以查看所有会话，且可以审计。
    """

    allow_uid = 0
    allow_hids = list()
    allow_all = False
    user = handler.get_current_user()
    if (user['privilege'] & TP_PRIVILEGE_OPS_AUZ) != 0 or (user['privilege'] & TP_PRIVILEGE_AUDIT_AUZ) != 0:
        allow_all = True
    if not allow_all:
        if (user['privilege'] & TP_PRIVILEGE_OPS) != 0:
            allow_uid = user.id
        if (user['privilege'] & TP_PRIVILEGE_AUDIT) != 0:
            s = SQL(get_db())
            s.select_from('audit_map', ['u_id', 'h_id', 'p_state', 'policy_auth_type', 'u_state', 'gu_state'], alt_name='a')
            s.where(
                'a.u_id={user_id} AND '
                'a.p_state={enable_state} AND'
                '('
                '((a.policy_auth_type={U2H} OR a.policy_auth_type={U2HG}) AND a.u_state={enable_state}) OR '
                '((a.policy_auth_type={UG2H} OR a.policy_auth_type={UG2HG}) AND a.u_state={enable_state} AND a.gu_state={enable_state})'
                ')'.format(enable_state=TP_STATE_NORMAL, user_id=user.id, U2H=TP_POLICY_AUTH_USER_HOST, U2HG=TP_POLICY_AUTH_USER_gHOST, UG2H=TP_POLICY_AUTH_gUSER_HOST, UG2HG=TP_POLICY_AUTH_gUSER_gHOST))
            err = s.query()
            if err != TPE_OK:
                return err, 0, []
            for h in s.recorder:
                if h.h_id not in allow_hids:
                    allow_hids.append(h.h_id)
            if len(allow_hids) == 0:
                return TPE_OK, 0, []

        if allow_uid == 0 and len(allow_hids) == 0:
            return TPE_FAILED, 0, []

    s = SQL(get_db())
    s.select_from('record', ['id', 'sid', 'user_id', 'host_id', 'acc_id', 'state', 'user_username', 'user_surname', 'host_ip', 'conn_ip', 'conn_port', 'client_ip', 'acc_username', 'protocol_type', 'protocol_sub_type', 'time_begin', 'time_end'], alt_name='r')

    str_where = ''
    _where = list()

    if len(sql_restrict) > 0:
        for k in sql_restrict:
            if k == 'state':
                _where.append('r.state IN ({})'.format(','.join([str(state) for state in sql_restrict[k]])))
            else:
                log.w('unknown restrict field: {}\n'.format(k))

    if len(sql_exclude) > 0:
        for k in sql_exclude:
            if k == 'state':
                _where.append('r.state NOT IN ({})'.format(','.join([str(state) for state in sql_exclude[k]])))
            else:
                log.w('unknown exclude field: {}\n'.format(k))

    if len(sql_filter) > 0:
        for k in sql_filter:
            if k == 'state':
                _where.append('r.state={}'.format(sql_filter[k]))
            # elif k == 'search_record':
            #     _where.append('(h.name LIKE "%{}%" OR h.ip LIKE "%{}%" OR h.router_addr LIKE "%{}%" OR h.desc LIKE "%{}%" OR h.cid LIKE "%{}%")'.format(sql_filter[k], sql_filter[k], sql_filter[k], sql_filter[k], sql_filter[k]))

    if not allow_all:
        if allow_uid != 0:
            _where.append('r.user_id={uid}'.format(uid=allow_uid))
        if len(allow_hids) > 0:
            hids = [str(h) for h in allow_hids]
            _where.append('r.host_id IN ({hids})'.format(hids=','.join(hids)))

    if len(_where) > 0:
        str_where = '( {} )'.format(' AND '.join(_where))

    s.where(str_where)

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'id' == sql_order['name']:
            s.order_by('r.id', _sort)
        elif 'time_begin' == sql_order['name']:
            s.order_by('r.time_begin', _sort)
        elif 'sid' == sql_order['name']:
            s.order_by('r.sid', _sort)
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


def _remove_padding_space(s):
    r = []
    for i in range(len(s)):
        if s[i] == 0x00:
            break
        r.append(s[i])
    return bytearray(r)


def read_record_head(protocol_type, record_id):
    if not tp_cfg().core.detected:
        return None, TPE_NO_CORE_SERVER

    if protocol_type == TP_PROTOCOL_TYPE_RDP:
        path_name = 'rdp'
    elif protocol_type == TP_PROTOCOL_TYPE_SSH:
        path_name = 'ssh'
    elif protocol_type == TP_PROTOCOL_TYPE_TELNET:
        path_name = 'telnet'

    record_path = os.path.join(tp_cfg().core.replay_path, path_name, '{:09d}'.format(int(record_id)))
    header_file_path = os.path.join(record_path, 'tp-{}.tpr'.format(path_name))

    if not os.path.exists(header_file_path):
        return None, TPE_NOT_EXISTS

    file = None
    try:
        file = open(header_file_path, 'rb')
        data = file.read()
        offset = 0

        magic, = struct.unpack_from('I', data, offset)  # magic must be 1381126228, 'TPPR'
        offset += 4
        ver, = struct.unpack_from('H', data, offset)
        offset += 2
        pkg_count, = struct.unpack_from('I', data, offset)
        offset += 4
        time_used, = struct.unpack_from('I', data, offset)
        offset += 4

        protocol_type, = struct.unpack_from('H', data, offset)
        offset += 2
        protocol_sub_type, = struct.unpack_from('H', data, offset)
        offset += 2
        time_start, = struct.unpack_from('Q', data, offset)
        offset += 8
        width, = struct.unpack_from('H', data, offset)
        offset += 2
        height, = struct.unpack_from('H', data, offset)
        offset += 2

        # file_count, = struct.unpack_from('H', data, offset)
        # offset += 2
        # total_size, = struct.unpack_from('I', data, offset)
        # offset += 4

        user_name, = struct.unpack_from('64s', data, offset)
        user_name = _remove_padding_space(user_name).decode()
        offset += 64
        account, = struct.unpack_from('64s', data, offset)
        account = _remove_padding_space(account).decode()
        offset += 64

        host_ip, = struct.unpack_from('40s', data, offset)
        host_ip = _remove_padding_space(host_ip).decode()
        offset += 40
        conn_ip, = struct.unpack_from('40s', data, offset)
        conn_ip = _remove_padding_space(conn_ip).decode()
        offset += 40
        conn_port, = struct.unpack_from('H', data, offset)
        offset += 2
        client_ip, = struct.unpack_from('40s', data, offset)
        client_ip = _remove_padding_space(client_ip).decode()
        offset += 40

    except Exception as e:
        log.e(e)
        return None, TPE_FAILED
    finally:
        if file is not None:
            file.close()

    header = dict()
    header['start'] = time_start
    header['pkg_count'] = pkg_count
    header['time_used'] = time_used
    header['width'] = width
    header['height'] = height
    header['account'] = account
    header['user_name'] = user_name
    header['host_ip'] = host_ip
    header['conn_ip'] = conn_ip
    header['conn_port'] = conn_port
    header['client_ip'] = client_ip

    return header, TPE_OK


def read_rdp_record_data(record_id, offset):
    if not tp_cfg().core.detected:
        return None, TPE_NO_CORE_SERVER

    record_path = os.path.join(tp_cfg().core.replay_path, 'rdp', '{:09d}'.format(int(record_id)))
    file_data = os.path.join(record_path, 'tp-rdp.dat')

    if not os.path.exists(file_data):
        return None, 0, TPE_NOT_EXISTS

    data_list = list()
    data_size = 0
    file = None
    try:
        file_size = os.path.getsize(file_data)
        if offset >= file_size:
            return None, 0, TPE_FAILED

        file = open(file_data, 'rb')
        if offset > 0:
            file.seek(offset, io.SEEK_SET)

        # read 1000 packages one time from offset.
        for i in range(1000):
            """
            // 一个数据包的头
            typedef struct TS_RECORD_PKG
            {
                ex_u8 type;			// 包的数据类型
                ex_u32 size;		// 这个包的总大小（不含包头）
                ex_u32 time_ms;		// 这个包距起始时间的时间差（毫秒，意味着一个连接不能持续超过49天）
                ex_u8 _reserve[3];	// 保留
            }TS_RECORD_PKG;
            """
            _data = file.read(12)
            data_size += 12
            _action, _size, _time, = struct.unpack_from('=BII', _data)
            if offset + data_size + _size > file_size:
                return None, 0, TPE_FAILED

            _data = file.read(_size)
            data_size += _size

            temp = dict()
            temp['a'] = _action
            temp['t'] = _time
            if _action == 0x10:
                # this is mouse movement event.
                x, y = struct.unpack_from('HH', _data)
                temp['x'] = x
                temp['y'] = y
            elif _action == 0x11:
                # this is a data package.
                _data = base64.b64encode(_data)
                temp['d'] = _data.decode()
            elif _action == 0x12:
                # this is a bitmap package.
                _data = base64.b64encode(_data)
                temp['d'] = _data.decode()
            else:
                return None, 0, TPE_FAILED

            data_list.append(temp)
            if offset + data_size == file_size:
                break

    except Exception:
        log.e('failed to read record file: {}\n'.format(file_data))
        return None, 0, TPE_FAILED
    finally:
        if file is not None:
            file.close()

    return data_list, data_size, TPE_OK


def read_ssh_record_data(record_id, offset):
    if not tp_cfg().core.detected:
        return None, TPE_NO_CORE_SERVER

    record_path = os.path.join(tp_cfg().core.replay_path, 'ssh', '{:09d}'.format(int(record_id)))
    file_data = os.path.join(record_path, 'tp-ssh.dat')

    if not os.path.exists(file_data):
        return None, 0, TPE_NOT_EXISTS

    data_list = list()
    data_size = 0
    file = None
    try:
        file_size = os.path.getsize(file_data)
        if offset >= file_size:
            return None, 0, TPE_FAILED

        file = open(file_data, 'rb')
        if offset > 0:
            file.seek(offset, io.SEEK_SET)

        # read 1000 packages one time from offset.
        for i in range(1000):
            """
            // 一个数据包的头
            typedef struct TS_RECORD_PKG
            {
                ex_u8 type;			// 包的数据类型
                ex_u32 size;		// 这个包的总大小（不含包头）
                ex_u32 time_ms;		// 这个包距起始时间的时间差（毫秒，意味着一个连接不能持续超过49天）
                ex_u8 _reserve[3];	// 保留
            }TS_RECORD_PKG;
            """
            _data = file.read(12)
            data_size += 12
            _action, _size, _time, = struct.unpack_from('=BII', _data)
            if offset + data_size + _size > file_size:
                return None, 0, TPE_FAILED

            _data = file.read(_size)
            data_size += _size

            temp = dict()
            temp['a'] = _action
            temp['t'] = _time
            if _action == 1:
                # this is window size changed.
                w, h = struct.unpack_from('HH', _data)
                temp['w'] = w
                temp['h'] = h
            elif _action == 2:
                try:
                    _d = _data.decode()
                    temp['d'] = _d
                except:
                    _data = base64.b64encode(_data)
                    temp['a'] = 3
                    temp['d'] = _data.decode()
            else:
                return None, 0, TPE_FAILED

            data_list.append(temp)
            if offset + data_size == file_size:
                break

    except Exception:
        log.e('failed to read record file: {}\n'.format(file_data))
        return None, 0, TPE_FAILED
    finally:
        if file is not None:
            file.close()

    return data_list, data_size, TPE_OK


def read_telnet_record_data(record_id, offset):
    if not tp_cfg().core.detected:
        return None, TPE_NO_CORE_SERVER

    record_path = os.path.join(tp_cfg().core.replay_path, 'telnet', '{:09d}'.format(int(record_id)))
    file_data = os.path.join(record_path, 'tp-telnet.dat')

    if not os.path.exists(file_data):
        return None, 0, TPE_NOT_EXISTS

    data_list = list()
    data_size = 0
    file = None
    try:
        file_size = os.path.getsize(file_data)
        if offset >= file_size:
            return None, 0, TPE_FAILED

        file = open(file_data, 'rb')
        if offset > 0:
            file.seek(offset, io.SEEK_SET)

        # read 1000 packages one time from offset.
        for i in range(1000):
            """
            // 一个数据包的头
            typedef struct TS_RECORD_PKG
            {
                ex_u8 type;			// 包的数据类型
                ex_u32 size;		// 这个包的总大小（不含包头）
                ex_u32 time_ms;		// 这个包距起始时间的时间差（毫秒，意味着一个连接不能持续超过49天）
                ex_u8 _reserve[3];	// 保留
            }TS_RECORD_PKG;
            """
            _data = file.read(12)
            data_size += 12
            _action, _size, _time, = struct.unpack_from('=BII', _data)
            if offset + data_size + _size > file_size:
                return None, 0, TPE_FAILED

            _data = file.read(_size)
            data_size += _size

            temp = dict()
            temp['a'] = _action
            temp['t'] = _time
            if _action == 1:
                # this is window size changed.
                w, h = struct.unpack_from('HH', _data)
                temp['w'] = w
                temp['h'] = h
            elif _action == 2:
                try:
                    _d = _data.decode()
                    temp['d'] = _d
                except:
                    _data = base64.b64encode(_data)
                    temp['a'] = 3
                    temp['d'] = _data.decode()
            else:
                return None, 0, TPE_FAILED

            data_list.append(temp)
            if offset + data_size == file_size:
                break

    except Exception:
        log.e('failed to read record file: {}\n'.format(file_data))
        return None, 0, TPE_FAILED
    finally:
        if file is not None:
            file.close()

    return data_list, data_size, TPE_OK


def delete_log(log_list):
    try:
        where = list()
        for item in log_list:
            where.append(' `id`={}'.format(item))

        db = get_db()
        sql = 'DELETE FROM `{}log` WHERE{};'.format(db.table_prefix, ' OR'.join(where))
        ret = db.exec(sql)
        if not ret:
            return False

        # TODO: 此处应该通过json-rpc接口通知core服务来删除重放文件。
        for item in log_list:
            log_id = int(item)
            try:
                record_path = os.path.join(tp_cfg().core.replay_path, 'ssh', '{:06d}'.format(log_id))
                if os.path.exists(record_path):
                    shutil.rmtree(record_path)
                record_path = os.path.join(tp_cfg().core.replay_path, 'rdp', '{:06d}'.format(log_id))
                if os.path.exists(record_path):
                    shutil.rmtree(record_path)
            except Exception:
                pass

        return True
    except:
        return False


def session_fix():
    db = get_db()

    if db.need_create or db.need_upgrade:
        return TPE_OK

    sql_list = []

    sql = 'UPDATE `{dbtp}record` SET state={new_state}, time_end={time_end} WHERE state={old_state};' \
          ''.format(dbtp=db.table_prefix, new_state=TP_SESS_STAT_ERR_RESET, old_state=TP_SESS_STAT_RUNNING, time_end=tp_timestamp_utc_now())
    sql_list.append(sql)

    sql = 'UPDATE `{dbtp}record` SET state={new_state},time_end={time_end} WHERE state={old_state};' \
          ''.format(dbtp=db.table_prefix, new_state=TP_SESS_STAT_ERR_START_RESET, old_state=TP_SESS_STAT_STARTED, time_end=tp_timestamp_utc_now())
    sql_list.append(sql)
    return db.transaction(sql_list)


def session_begin(sid, user_id, host_id, acc_id, user_username, acc_username, host_ip, conn_ip, conn_port, client_ip, auth_type, protocol_type, protocol_sub_type):
    db = get_db()
    sql = 'INSERT INTO `{}record` (sid,user_id,host_id,acc_id,state,user_username,host_ip,conn_ip,conn_port,client_ip,acc_username,auth_type,protocol_type,protocol_sub_type,time_begin,time_end) ' \
          'VALUES ("{sid}",{user_id},{host_id},{acc_id},0,"{user_username}","{host_ip}","{conn_ip}",{conn_port},"{client_ip}","{acc_username}",{auth_type},{protocol_type},{protocol_sub_type},{time_begin},0)' \
          ';'.format(db.table_prefix,
                     sid=sid, user_id=user_id, host_id=host_id, acc_id=acc_id, user_username=user_username, host_ip=host_ip, conn_ip=conn_ip, conn_port=conn_port,
                     client_ip=client_ip, acc_username=acc_username, auth_type=auth_type, protocol_type=protocol_type, protocol_sub_type=protocol_sub_type,
                     time_begin=tp_timestamp_utc_now())

    ret = db.exec(sql)
    if not ret:
        return TPE_DATABASE, 0

    record_id = db.last_insert_id()
    if record_id == -1:
        return TPE_DATABASE, 0
    else:
        return TPE_OK, record_id


def session_update(record_id, protocol_sub_type, state):
    db = get_db()
    sql = 'UPDATE `{}record` SET protocol_sub_type={}, state={} WHERE id={};'.format(db.table_prefix, protocol_sub_type, int(state), int(record_id))
    return db.exec(sql)


def session_end(record_id, ret_code):
    db = get_db()
    sql = 'UPDATE `{}record` SET state={}, time_end={} WHERE id={};'.format(db.table_prefix, int(ret_code), tp_timestamp_utc_now(), int(record_id))
    return db.exec(sql)


@tornado.gen.coroutine
def cleanup_storage(handler):
    # storage config
    sto = tp_cfg().sys.storage

    db = get_db()
    _now = tp_timestamp_utc_now()
    msg = []
    have_error = False

    s = SQL(db)
    chk_time = _now - sto.keep_log * 24 * 60 * 60

    if sto.keep_log > 0:
        # find out all sys-log to be remove
        s.select_from('syslog', ['id'], alt_name='s')
        s.where('s.log_time<{chk_time}'.format(chk_time=chk_time))
        err = s.query()
        if err != TPE_OK:
            have_error = True
            msg.append('清理系统日志时发生错误：无法获取系统日志信息！')
            # return err, msg
        else:
            removed_log = len(s.recorder)
            if 0 == removed_log:
                msg.append('没有满足条件的系统日志需要清除！')
            else:
                s.reset().delete_from('syslog').where('log_time<{chk_time}'.format(chk_time=chk_time))
                err = s.exec()
                if err != TPE_OK:
                    have_error = True
                    msg.append('清理系统日志时发生错误：无法清除指定的系统日志！')
                else:
                    msg.append('{} 条系统日志已清除！'.format(removed_log))

    if sto.keep_record > 0:
        core_cfg = tp_cfg().core
        if not core_cfg.detected:
            have_error = True
            msg.append('清除指定会话录像失败：未能检测到核心服务！')
        else:
            replay_path = core_cfg.replay_path
            if not os.path.exists(replay_path):
                have_error = True
                msg.append('清除指定会话录像失败：会话录像路径不存在（{}）！'.format(replay_path))
            else:
                # find out all record to be remove
                s.reset().select_from('record', ['id', 'protocol_type'], alt_name='r')
                s.where('r.time_begin<{chk_time}'.format(chk_time=chk_time))
                err = s.query()
                if err != TPE_OK:
                    have_error = True
                    msg.append('清除指定会话录像失败：无法获取会话录像信息！')
                elif len(s.recorder) == 0:
                    msg.append('没有满足条件的会话录像需要清除！')
                else:
                    record_removed = 0
                    for r in s.recorder:
                        if r.protocol_type == TP_PROTOCOL_TYPE_RDP:
                            path_remove = os.path.join(replay_path, 'rdp', '{:09d}'.format(r.id))
                        elif r.protocol_type == TP_PROTOCOL_TYPE_SSH:
                            path_remove = os.path.join(replay_path, 'ssh', '{:09d}'.format(r.id))
                        elif r.protocol_type == TP_PROTOCOL_TYPE_TELNET:
                            path_remove = os.path.join(replay_path, 'telnet', '{:09d}'.format(r.id))
                        else:
                            have_error = True
                            msg.append('会话录像记录编号 {}，未知远程访问协议！'.format(r.id))
                            continue

                        if os.path.exists(path_remove):
                            # print('remove path', path_remove)
                            try:
                                shutil.rmtree(path_remove)
                            except:
                                have_error = True
                                msg.append('会话录像记录 {} 清除失败，无法删除目录 {}！'.format(r.id, path_remove))

                        ss = SQL(db)
                        ss.delete_from('record').where('id={rid}'.format(rid=r.id))
                        ss.exec()

                        record_removed += 1

                    msg.append('{} 条会话录像数据已清除！'.format(record_removed))

    if have_error:
        return TPE_FAILED, msg
    else:
        return TPE_OK, msg
