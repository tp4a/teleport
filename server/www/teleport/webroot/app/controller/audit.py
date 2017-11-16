# -*- coding: utf-8 -*-

# import ctypes
import json
import os
# import platform
import shutil

from app.const import *
from app.base.configs import get_cfg
from app.base.logger import *
from app.model import record
# from app.model import user
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
# import tornado.web
import tornado.gen


def get_free_space_bytes(folder):
    """ Return folder/drive free space (in bytes)
    """
    try:
        total, used, free = shutil.disk_usage(folder)
        return total, free
    except:
        return 0, 0

        # if platform.system() == 'Windows':
        #     _free_bytes = ctypes.c_ulonglong(0)
        #     _total_bytes = ctypes.c_ulonglong(0)
        #     ctypes.windll.kernel32.GetDiskFreeSpaceExW(folder, None, ctypes.pointer(_total_bytes), ctypes.pointer(_free_bytes))
        #     total_bytes = _total_bytes.value
        #     free_bytes = _free_bytes.value
        # else:
        #     try:
        #         st = os.statvfs(folder)
        #         total_bytes = st.f_blocks * st.f_frsize
        #         free_bytes = st.f_bavail * st.f_frsize
        #     except:
        #         total_bytes = 0
        #         free_bytes = 0
        #
        # return total_bytes, free_bytes


class RecordHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS | TP_PRIVILEGE_OPS_AUZ | TP_PRIVILEGE_AUDIT_AUZ | TP_PRIVILEGE_AUDIT_OPS_HISTORY)
        if ret != TPE_OK:
            return

        if not get_cfg().core.detected:
            total_size = 0
            free_size = 0
        else:
            total_size, free_size = get_free_space_bytes(get_cfg().core.replay_path)

        param = {
            # 'user_list': user.get_user_list(with_admin=True),
            'total_size': total_size,
            'free_size': free_size,
        }

        self.render('audit/record.mako', page_param=json.dumps(param))


class DoGetRecordsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS | TP_PRIVILEGE_OPS_AUZ | TP_PRIVILEGE_AUDIT_AUZ | TP_PRIVILEGE_AUDIT_OPS_HISTORY)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'id'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25
        sql_restrict = args['restrict'] if 'restrict' in args else {}
        sql_exclude = args['exclude'] if 'exclude' in args else {}

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                if i == 'user_id' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'user_name':
                    if len(_filter[i].strip()) == 0:
                        tmp.append(i)

            for i in tmp:
                del _filter[i]

            sql_filter.update(_filter)

            _limit = args['limit']
            if _limit['page_index'] < 0:
                _limit['page_index'] = 0
            if _limit['per_page'] < 10:
                _limit['per_page'] = 10
            if _limit['per_page'] > 100:
                _limit['per_page'] = 100

            sql_limit.update(_limit)

            _order = args['order']
            if _order is not None:
                sql_order['name'] = _order['k']
                sql_order['asc'] = _order['v']

        except:
            return self.write_json(TPE_PARAM)

        err, total, row_data = record.get_records(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude)
        ret = dict()
        ret['page_index'] = sql_limit['page_index']
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)

        # err, total, record_list = record.get_records(filter, order, _limit)
        # if err != TPE_OK:
        #     return self.write_json(err)
        # ret = dict()
        # ret['page_index'] = limit['page_index']
        # ret['total'] = total
        # ret['data'] = record_list
        # return self.write_json(0, data=ret)


class ReplayHandler(TPBaseHandler):
    def get(self, protocol, record_id):
        protocol = int(protocol)
        if protocol == TP_PROTOCOL_TYPE_RDP:
            return
        elif protocol == TP_PROTOCOL_TYPE_SSH:
            param = {'record_id': record_id}
            self.render('audit/replay-ssh.mako', page_param=json.dumps(param))


# # class PlayRdpHandler(TPBaseAdminAuthHandler):
# #     def get(self, ip, record_id):
# #         # protocol = int(protocol)
# #         # if protocol == 1:
# #         #     return
# #         # elif protocol == 2:
# #         #     self.render('log/record.mako', record_id=record_id)
# #         #     return
# #         # pass
# #         filename = os.path.join(cfg.base.replay_path, 'replay', 'rdp', '{}'.format(record_id), 'tp-rdp.tpr')
#
# class ReplayStaticFileHandler(tornado.web.StaticFileHandler):
#     def initialize(self, path, default_filename=None):
#         super().initialize(path, default_filename)
#         self.root = get_cfg().core.replay_path
#         # self.default_filename = default_filename
#
#
class ComandLogHandler(TPBaseHandler):
    @tornado.gen.coroutine
    def get(self, protocol, record_id):

        header, err = record.read_record_head(record_id)
        if header is None:
            return self.write('操作失败')

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
            record_path = os.path.join(get_cfg().core.replay_path, 'ssh', '{:09d}'.format(int(record_id)))
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
            self.render('audit/record-ssh-cmd.mako', page_param=json.dumps(param))
        else:
            self.render('audit/record-sftp-cmd.mako', page_param=json.dumps(param))


class DoGetRecordHeaderHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            record_id = int(args['id'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        header, err = record.read_record_head(record_id)
        if header is None:
            return self.write_json(err, '操作失败')

        return self.write_json(0, data=header)


class DoGetRecordDataHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            record_id = int(args['id'])
            offset = int(args['offset'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        data_list, data_size, err = record.read_record_data(record_id, offset)
        self.write_json(err, data={'data_list': data_list, 'data_size': data_size})

# class DeleteLog(TPBaseAdminAuthJsonHandler):
#     # TODO: 用户可能会批量删除大量录像文件，因此io操作可能会比较耗时，这里应该改为异步方式。
#     def post(self):
#         args = self.get_argument('args', None)
#         if args is not None:
#             args = json.loads(args)
#         else:
#             return self.write_json(-1, '参数错误')
#
#         log_list = args['log_list']
#
#         if not record.delete_log(log_list):
#             return self.write_json(-3, '操作失败')
#
#         return self.write_json(0)
