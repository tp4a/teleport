# -*- coding: utf-8 -*-

import os
import io
import shutil
import struct
import base64

from app.const import *
from app.base.configs import get_cfg
from app.base.db import get_db, SQL
from app.base.logger import log
from app.base.utils import tp_timestamp_utc_now


def get_records(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude):
    s = SQL(get_db())
    s.select_from('record', ['id', 'user_id', 'host_id', 'acc_id', 'state', 'user_username', 'user_surname', 'host_ip', 'conn_ip', 'conn_port', 'client_ip', 'acc_username', 'protocol_type', 'protocol_sub_type', 'time_begin', 'time_end'], alt_name='r')

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

    if len(_where) > 0:
        str_where = '( {} )'.format(' AND '.join(_where))

    s.where(str_where)

    if sql_order is not None:
        _sort = False if not sql_order['asc'] else True
        if 'id' == sql_order['name']:
            s.order_by('r.id', _sort)
        elif 'time_begin' == sql_order['name']:
            s.order_by('r.time_begin', _sort)
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


def read_record_head(record_id):
    record_path = os.path.join(get_cfg().core.replay_path, 'ssh', '{:09d}'.format(int(record_id)))
    header_file_path = os.path.join(record_path, 'tp-ssh.tpr')

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
        user_name = user_name.decode()
        offset += 64
        account, = struct.unpack_from('64s', data, offset)
        account = account.decode()
        offset += 64

        host_ip, = struct.unpack_from('40s', data, offset)
        host_ip = host_ip.decode()
        offset += 40
        conn_ip, = struct.unpack_from('40s', data, offset)
        conn_ip = conn_ip.decode()
        offset += 40
        conn_port, = struct.unpack_from('H', data, offset)
        offset += 2
        client_ip, = struct.unpack_from('40s', data, offset)
        client_ip = client_ip.decode()
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


def read_record_data(record_id, offset):
    # read 1000 packages one time from offset.
    record_path = os.path.join(get_cfg().core.replay_path, 'ssh', '{:09d}'.format(int(record_id)))
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
                record_path = os.path.join(get_cfg().core.replay_path, 'ssh', '{:06d}'.format(log_id))
                if os.path.exists(record_path):
                    shutil.rmtree(record_path)
                record_path = os.path.join(get_cfg().core.replay_path, 'rdp', '{:06d}'.format(log_id))
                if os.path.exists(record_path):
                    shutil.rmtree(record_path)
            except Exception:
                pass

        return True
    except:
        return False


def session_fix():
    try:
        db = get_db()

        sql_list = []

        sql = 'UPDATE `{dbtp}record` SET state={new_state}, time_end={time_end} WHERE state={old_state};' \
              ''.format(dbtp=db.table_prefix, new_state=TP_SESS_STAT_ERR_RESET, old_state=TP_SESS_STAT_RUNNING, time_end=tp_timestamp_utc_now())
        sql_list.append(sql)
        # if not db.exec(sql):
        #     ret = False
        sql = 'UPDATE `{dbtp}record` SET state={new_state},time_end={time_end} WHERE state={old_state};' \
              ''.format(dbtp=db.table_prefix, new_state=TP_SESS_STAT_ERR_START_RESET, old_state=TP_SESS_STAT_STARTED, time_end=tp_timestamp_utc_now())
        sql_list.append(sql)
        return db.transaction(sql_list)
        # if not db.exec(sql):
        #     ret = False
        # return ret
    except:
        log.e('\n')
        return False


def session_begin(sid, user_id, host_id, acc_id, user_username, acc_username, host_ip, conn_ip, conn_port, client_ip, auth_type, protocol_type, protocol_sub_type):
    try:
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

    except:
        log.e('\n')
        return TPE_DATABASE, 0


def session_update(record_id, state):
    try:
        db = get_db()
        sql = 'UPDATE `{}record` SET state={} WHERE id={};'.format(db.table_prefix, int(state), int(record_id))
        return db.exec(sql)
    except:
        return False


def session_end(record_id, ret_code):
    try:
        db = get_db()
        sql = 'UPDATE `{}record` SET state={}, time_end={} WHERE id={};'.format(db.table_prefix, int(ret_code), tp_timestamp_utc_now(), int(record_id))
        return db.exec(sql)
    except:
        return False
