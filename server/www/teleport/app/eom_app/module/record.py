# -*- coding: utf-8 -*-
import os
import shutil
import struct

from .common import *


# cfg = app_cfg()


def read_record_head(record_id):
    record_path = os.path.join(cfg.data_path, 'replay', 'ssh', '{}'.format(record_id))
    header_file_path = os.path.join(record_path, 'head.init')
    # header_file_path = r"E:\GitWork\teleport\share\data\replay\ssh\99\head.init"
    file = None
    try:
        file = open(header_file_path, 'rb')
        data = file.read()
        x = len(data)
        offset = 0
        # data = data.decode()
        ID, = struct.unpack_from('16s', data, offset)
        ID = ID.decode()
        offset += 16

        Version, = struct.unpack_from('16s', data, offset)
        Version = Version.decode()
        offset += 16

        total_size, = struct.unpack_from('B', data, offset)
        offset += 1

        total_file_count, = struct.unpack_from('B', data, offset)
        offset += 1

        total_time, = struct.unpack_from('I', data, offset)
        offset += 4
        time_list = list()
        for i in range(total_file_count):
            time, = struct.unpack_from('I', data, offset)
            time_list.append(time)
            offset += 4

    except Exception as e:
        return None
    finally:
        if file is not None:
            file.close()

    header = dict()
    header['id'] = ID
    header['ver'] = Version
    header['t_size'] = total_size
    header['t_count'] = total_file_count
    header['t_time'] = total_time
    header['t_list'] = time_list
    return header


def read_record_term(record_id):
    record_path = os.path.join(cfg.data_path, 'replay', 'ssh', '{}'.format(record_id))
    term_file_path = os.path.join(record_path, 'term.init')
    # term_file_path = r"E:\GitWork\teleport\share\data\replay\ssh\103\term.init"

    file = None
    try:
        file = open(term_file_path, 'rb')
        data = file.read()
        x = len(data)
        offset = 0
        # data = data.decode()
        ID, = struct.unpack_from('16s', data, offset)
        ID = ID.decode()
        offset += 16

        Version, = struct.unpack_from('16s', data, offset)
        Version = Version.decode()
        offset += 16

        t_count, = struct.unpack_from('I', data, offset)
        offset += 4
        term_list = list()
        for i in range(t_count):
            # _term, = struct.unpack_from('16s', data, offset)
            # _term = _term.decode()
            # offset += 16
            _time, = struct.unpack_from('I', data, offset)
            offset += 4

            x, = struct.unpack_from('I', data, offset)
            offset += 4

            y, = struct.unpack_from('I', data, offset)
            offset += 4

            # px, = struct.unpack_from('I', data, offset)
            # offset += 4
            #
            # py, = struct.unpack_from('I', data, offset)
            # offset += 4
            #
            # _time, = struct.unpack_from('I', data, offset)
            # offset += 4
            temp = dict()
            # temp['term'] = _term
            temp['t'] = _time
            temp['w'] = x
            temp['h'] = y
            # temp['px'] = px
            # temp['py'] = py

            term_list.append(temp)

    except Exception as e:
        return None
    finally:
        if file is not None:
            file.close()

    header = dict()
    header['id'] = ID
    header['ver'] = Version
    header['count'] = t_count
    header['term_list'] = term_list
    return header


def read_record_info(record_id, file_id):
    record_path = os.path.join(cfg.data_path, 'replay', 'ssh', '{}'.format(record_id))
    file_info = os.path.join(record_path, '{}.ts'.format(file_id))
    # file_info = r"E:\GitWork\teleport\share\data\replay\ssh\108\0.ts"
    file = None
    try:
        file = open(file_info, 'rb')
        data = file.read()
        total_size = len(data)
        offset = 0
        data_list = list()
        while True:
            action, = struct.unpack_from('B', data, offset)
            offset += 1

            _time, = struct.unpack_from('I', data, offset)
            offset += 4

            _size, = struct.unpack_from('I', data, offset)
            offset += 4

            _format = '{}s'.format(_size)
            _data, = struct.unpack_from(_format, data, offset)
            _data = _data.decode()
            offset += _size

            temp = dict()
            temp['a'] = action
            temp['t'] = _time
            temp['d'] = _data

            data_list.append(temp)
            if offset == total_size:
                break

    except Exception as e:
        return None
    finally:
        if file is not None:
            file.close()
    return data_list


# if __name__ == '__main__':
#     read_record_info(94,1)
#     pass
#     db_path = os.path.join(cfg.data_path, 'ts_db.db')


def delete_log(log_list):
    try:
        sql_exec = get_db_con()
        for item in log_list:
            log_id = int(item)
            str_sql = 'DELETE FROM ts_log WHERE id={}'.format(log_id)
            ret = sql_exec.ExecProcNonQuery(str_sql)
            if not ret:
                return False
                #     删除录像文件
            try:
                record_path = os.path.join(cfg.data_path, 'replay', 'ssh', '{}'.format(log_id))
                if os.path.exists(record_path):
                    shutil.rmtree(record_path)
                record_path = os.path.join(cfg.data_path, 'replay', 'rdp', '{}'.format(log_id))
                if os.path.exists(record_path):
                    shutil.rmtree(record_path)
            except Exception as e:
                pass

        return True
    except:
        return False
