# -*- coding: utf-8 -*-

import os
import shutil
import struct

from eom_app.app.configs import app_cfg
from eom_app.app.db import get_db
from eom_common.eomcore.logger import log
from eom_common.eomcore.utils import timestamp_utc_now


def read_record_head(record_id):
    record_path = os.path.join(app_cfg().core.replay_path, 'ssh', '{:06d}'.format(int(record_id)))
    header_file_path = os.path.join(record_path, 'tp-ssh.tpr')
    file = None
    try:
        file = open(header_file_path, 'rb')
        data = file.read()
        offset = 0

        magic, = struct.unpack_from('I', data, offset)  # magic must be 1381126228, 'TPRR'
        offset += 4
        time_start, = struct.unpack_from('Q', data, offset)
        offset += 8
        pkg_count, = struct.unpack_from('I', data, offset)
        offset += 4
        time_used, = struct.unpack_from('I', data, offset)
        offset += 4
        width, = struct.unpack_from('H', data, offset)
        offset += 2
        height, = struct.unpack_from('H', data, offset)
        offset += 2
        file_count, = struct.unpack_from('H', data, offset)
        offset += 2
        total_size, = struct.unpack_from('I', data, offset)
        offset += 4

        account, = struct.unpack_from('16s', data, offset)
        account = account.decode()
        offset += 16
        user_name, = struct.unpack_from('16s', data, offset)
        user_name = user_name.decode()
        offset += 16

    except Exception as e:
        return None
    finally:
        if file is not None:
            file.close()

    header = dict()
    header['file_count'] = file_count
    header['time_used'] = time_used
    header['width'] = width
    header['height'] = height
    return header


# def read_record_term(record_id):
#     record_path = os.path.join(cfg.core.replay_path, 'ssh', '{}'.format(record_id))
#     term_file_path = os.path.join(record_path, 'term.init')
#     # term_file_path = r"E:\GitWork\teleport\share\data\replay\ssh\103\term.init"
#
#     file = None
#     try:
#         file = open(term_file_path, 'rb')
#         data = file.read()
#         x = len(data)
#         offset = 0
#         # data = data.decode()
#         ID, = struct.unpack_from('16s', data, offset)
#         ID = ID.decode()
#         offset += 16
#
#         Version, = struct.unpack_from('16s', data, offset)
#         Version = Version.decode()
#         offset += 16
#
#         t_count, = struct.unpack_from('I', data, offset)
#         offset += 4
#         term_list = list()
#         for i in range(t_count):
#             # _term, = struct.unpack_from('16s', data, offset)
#             # _term = _term.decode()
#             # offset += 16
#             _time, = struct.unpack_from('I', data, offset)
#             offset += 4
#
#             x, = struct.unpack_from('I', data, offset)
#             offset += 4
#
#             y, = struct.unpack_from('I', data, offset)
#             offset += 4
#
#             # px, = struct.unpack_from('I', data, offset)
#             # offset += 4
#             #
#             # py, = struct.unpack_from('I', data, offset)
#             # offset += 4
#             #
#             # _time, = struct.unpack_from('I', data, offset)
#             # offset += 4
#             temp = dict()
#             # temp['term'] = _term
#             temp['t'] = _time
#             temp['w'] = x
#             temp['h'] = y
#             # temp['px'] = px
#             # temp['py'] = py
#
#             term_list.append(temp)
#
#     except Exception as e:
#         return None
#     finally:
#         if file is not None:
#             file.close()
#
#     header = dict()
#     header['id'] = ID
#     header['ver'] = Version
#     header['count'] = t_count
#     header['term_list'] = term_list
#     return header


def read_record_info(record_id, file_id):
    record_path = os.path.join(app_cfg().core.replay_path, 'ssh', '{:06d}'.format(int(record_id)))
    file_info = os.path.join(record_path, 'tp-ssh.{:03d}'.format(int(file_id)))
    file = None
    try:
        file = open(file_info, 'rb')
        data = file.read()
        total_size = len(data)

        offset = 0
        data_size, = struct.unpack_from('I', data, offset)
        offset += 4

        data_list = list()
        while True:
            action, = struct.unpack_from('B', data, offset)
            offset += 1

            _size, = struct.unpack_from('I', data, offset)
            offset += 4

            _time, = struct.unpack_from('I', data, offset)
            offset += 4

            # skip reserved 3 bytes.
            offset += 3

            _format = '{}s'.format(_size)
            _data, = struct.unpack_from(_format, data, offset)
            offset += _size

            temp = dict()
            temp['a'] = action
            temp['t'] = _time
            if action == 1:
                # this is window size changed.
                w, h = struct.unpack_from('HH', _data)
                temp['w'] = w
                temp['h'] = h
            elif action == 2:
                _data = _data.decode()
                # this is ssh data.
                temp['d'] = _data
            else:
                return None

            data_list.append(temp)
            if offset == total_size:
                break

    except Exception as e:
        log.e('failed to read record file: {}\n'.format(file_info))
        return None
    finally:
        if file is not None:
            file.close()
    return data_list


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
                record_path = os.path.join(app_cfg().core.replay_path, 'ssh', '{:06d}'.format(log_id))
                if os.path.exists(record_path):
                    shutil.rmtree(record_path)
                record_path = os.path.join(app_cfg().core.replay_path, 'rdp', '{:06d}'.format(log_id))
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
        sql = 'UPDATE `{}log` SET `ret_code`=7 WHERE `ret_code`=0;'.format(db.table_prefix)
        return db.exec(sql)
    except:
        return False


def session_begin(sid, acc_name, host_ip, sys_type, host_port, auth_mode, user_name, protocol):
    try:
        db = get_db()
        sql = 'INSERT INTO `{}log` (`session_id`,`account_name`,`host_ip`,`sys_type`,`host_port`,`auth_type`,`user_name`,`ret_code`,`begin_time`,`end_time`,`log_time`,`protocol`) ' \
              'VALUES ("{}","{}","{}",{},{},{},"{}",{},{},{},"{}",{});' \
              ''.format(db.table_prefix,
                        sid, acc_name, host_ip, sys_type, host_port, auth_mode, user_name, 0, timestamp_utc_now(), 0, '', protocol)

        ret = db.exec(sql)
        if not ret:
            return -101

        sql = 'SELECT last_insert_rowid()'
        db_ret = db.query(sql)
        if db_ret is None:
            return -102
        user_id = db_ret[0][0]
        return user_id

    except:
        return False


def session_end(record_id, ret_code):
    try:
        db = get_db()
        sql = 'UPDATE `{}log` SET `ret_code`={}, `end_time`={} WHERE `id`={};'.format(db.table_prefix, int(ret_code), timestamp_utc_now(), int(record_id))
        return db.exec(sql)
    except:
        return False
