# -*- coding: utf-8 -*-

import ctypes
import json
import os
import platform

from app.base.configs import get_cfg
from app.module import record
from app.module import user
from app.base.controller import TPBaseAdminAuthHandler, TPBaseAdminAuthJsonHandler
import tornado.web


def get_free_space_bytes(folder):
    """ Return folder/drive free space (in bytes)
    """
    if platform.system() == 'Windows':
        _free_bytes = ctypes.c_ulonglong(0)
        _total_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(folder, None, ctypes.pointer(_total_bytes), ctypes.pointer(_free_bytes))
        total_bytes = _total_bytes.value
        free_bytes = _free_bytes.value
    else:
        try:
            st = os.statvfs(folder)
            total_bytes = st.f_blocks * st.f_frsize
            free_bytes = st.f_bavail * st.f_frsize
        except:
            total_bytes = 0
            free_bytes = 0

    return total_bytes, free_bytes


class LogHandler(TPBaseAdminAuthHandler):
    def get(self):
        if not get_cfg().core.detected:
            total_size = 0
            free_size = 0
        else:
            total_size, free_size = get_free_space_bytes(get_cfg().core.replay_path)

        param = {
            'user_list': user.get_user_list(with_admin=True),
            'total_size': total_size,
            'free_size': free_size,
        }

        self.render('log/index.mako', page_param=json.dumps(param))


class RecordHandler(TPBaseAdminAuthHandler):
    def get(self, protocol, record_id):
        protocol = int(protocol)
        if protocol == 1:
            return
        elif protocol == 2:
            self.render('log/record.mako', record_id=record_id)


# class PlayRdpHandler(TPBaseAdminAuthHandler):
#     def get(self, ip, record_id):
#         # protocol = int(protocol)
#         # if protocol == 1:
#         #     return
#         # elif protocol == 2:
#         #     self.render('log/record.mako', record_id=record_id)
#         #     return
#         # pass
#         filename = os.path.join(cfg.base.replay_path, 'replay', 'rdp', '{}'.format(record_id), 'tp-rdp.tpr')

class ReplayStaticFileHandler(tornado.web.StaticFileHandler):
    def initialize(self, path, default_filename=None):
        super().initialize(path, default_filename)
        self.root = get_cfg().core.replay_path
        # self.default_filename = default_filename


class ComandLogHandler(TPBaseAdminAuthHandler):
    def get(self, protocol, record_id):

        header = record.read_record_head(record_id)
        if header is None:
            return self.write_json(-3, '操作失败')

        # ret = dict()
        # ret['header'] = header
        # return self.write_json(0, data=ret)

        param = dict()
        param['header'] = header
        param['count'] = 0
        param['op'] = list()

        cmd_type = 0  # 0 = ssh, 1 = sftp
        protocol = int(protocol)
        if protocol == 1:
            pass
        elif protocol == 2:
            record_path = os.path.join(get_cfg().core.replay_path, 'ssh', '{:06d}'.format(int(record_id)))
            file_info = os.path.join(record_path, 'tp-ssh-cmd.txt')
            try:
                file = open(file_info, 'r')
                data = file.readlines()
                for i in range(len(data)):
                    if 0 == i:
                        cmd = data[i][22:-1]
                        if 'SFTP INITIALIZE' == cmd:
                            cmd_type = 1
                            continue
                    if cmd_type == 0:
                        param['op'].append({'t': data[i][1:20], 'c': data[i][22:-1]})
                    else:
                        cmd_info = data[i][22:-1].split(':')
                        if len(cmd_info) != 4:
                            continue
                        param['op'].append({'t': data[i][1:20], 'c': cmd_info[0], 'p1': cmd_info[2], 'p2': cmd_info[3]})
            except:
                pass
            param['count'] = len(param['op'])

        if cmd_type == 0:
            self.render('log/record-ssh-cmd.mako', page_param=json.dumps(param))
        else:
            self.render('log/record-sftp-cmd.mako', page_param=json.dumps(param))


class RecordGetHeader(TPBaseAdminAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        record_id = args['id']

        header = record.read_record_head(record_id)
        if header is None:
            return self.write_json(-3, '操作失败')

        ret = dict()
        ret['header'] = header
        return self.write_json(0, data=ret)


class RecordGetInfo(TPBaseAdminAuthJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        record_id = args['id']
        file_id = args['file_id']

        data = record.read_record_info(record_id, file_id)
        if data is None:
            return self.write_json(-3, '操作失败')

        return self.write_json(0, data=data)


class DeleteLog(TPBaseAdminAuthJsonHandler):
    # TODO: 用户可能会批量删除大量录像文件，因此io操作可能会比较耗时，这里应该改为异步方式。
    def post(self):
        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)
        else:
            return self.write_json(-1, '参数错误')

        log_list = args['log_list']

        if not record.delete_log(log_list):
            return self.write_json(-3, '操作失败')

        return self.write_json(0)


class LogList(TPBaseAdminAuthJsonHandler):
    def post(self):
        filter = dict()
        order = dict()
        order['name'] = 'host_id'
        order['asc'] = True
        limit = dict()
        limit['page_index'] = 0
        limit['per_page'] = 25

        args = self.get_argument('args', None)
        if args is not None:
            args = json.loads(args)

            tmp = list()
            _filter = args['filter']
            if _filter is not None:
                for i in _filter:
                    if i == 'user_name':
                        _x = _filter[i].strip()
                        if _x == '全部':
                            tmp.append(i)

                    if i == 'search':
                        _x = _filter[i].strip()
                        if len(_x) == 0:
                            tmp.append(i)
                        continue

                for i in tmp:
                    del _filter[i]

                filter.update(_filter)

        _limit = args['limit']
        if _limit['page_index'] < 0:
            _limit['page_index'] = 0
        if _limit['per_page'] < 10:
            _limit['per_page'] = 10
        if _limit['per_page'] > 100:
            _limit['per_page'] = 100

        limit.update(_limit)

        _order = args['order']
        if _order is not None:
            order['name'] = _order['k']
            order['asc'] = _order['v']

        total, log_list = user.get_log_list(filter, _limit)
        ret = dict()
        ret['page_index'] = limit['page_index']
        ret['total'] = total
        ret['data'] = log_list

        return self.write_json(0, data=ret)
