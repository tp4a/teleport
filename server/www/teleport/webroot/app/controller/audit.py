# -*- coding: utf-8 -*-

import json
import os
import shutil

from app.const import *
from app.base.configs import tp_cfg
from app.base.logger import *
from app.model import audit
from app.model import record
from app.base.controller import TPBaseHandler, TPBaseJsonHandler
import tornado.gen


def get_free_space_bytes(folder):
    """ Return folder/drive free space (in bytes)
    """
    try:
        total, _, free = shutil.disk_usage(folder)
        return total, free
    except:
        return 0, 0


class AuzListHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return
        self.render('audit/auz-list.mako')


class PolicyDetailHandler(TPBaseHandler):
    def get(self, pid):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return
        pid = int(pid)
        err, policy = audit.get_by_id(pid)
        if err == TPE_OK:
            param = {
                'policy_id': pid,
                'policy_name': policy['name'],
                'policy_desc': policy['desc']
            }
        else:
            param = {
                'policy_id': 0,
                'policy_name': '',
                'policy_desc': ''
            }
        self.render('audit/auz-info.mako', page_param=json.dumps(param))


class DoGetPoliciesHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
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
        sql_order['name'] = 'rank'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                if i == 'state' and _filter[i] == 0:
                    tmp.append(i)
                    continue
                if i == 'search':
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

            # _order = args['order']
            # if _order is not None:
            #     sql_order['name'] = _order['k']
            #     sql_order['asc'] = _order['v']

        except:
            return self.write_json(TPE_PARAM)

        err, total, page_index, row_data = audit.get_policies(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoUpdatePolicyHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            args['id'] = int(args['id'])
            args['name'] = args['name'].strip()
            args['desc'] = args['desc'].strip()
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if len(args['name']) == 0:
            return self.write_json(TPE_PARAM)

        if args['id'] == -1:
            err, info = audit.create_policy(self, args)
        else:
            err = audit.update_policy(self, args)
            info = {}
        self.write_json(err, data=info)


class DoUpdatePoliciesHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            action = args['action']
            p_ids = args['policy_ids']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if action == 'lock':
            err = audit.update_policies_state(self, p_ids, TP_STATE_DISABLED)
            return self.write_json(err)
        elif action == 'unlock':
            err = audit.update_policies_state(self, p_ids, TP_STATE_NORMAL)
            return self.write_json(err)
        elif action == 'remove':
            err = audit.remove_policies(self, p_ids)
            return self.write_json(err)
        else:
            return self.write_json(TPE_PARAM)


class DoRankReorderHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            pid = int(args['pid'])
            new_rank = int(args['new_rank'])
            start_rank = int(args['start_rank'])
            end_rank = int(args['end_rank'])
            direct = int(args['direct'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if direct == -1:
            direct = '-1'
        elif direct == 1:
            direct = '+1'
        else:
            return self.write_json(TPE_PARAM)

        err = audit.rank_reorder(self, pid, new_rank, start_rank, end_rank, direct)
        self.write_json(err)


class DoGetAuditorsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        # print('---get operator:', args)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'id'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25

        try:
            tmp = list()
            _filter = args['filter']
            for i in _filter:
                # if i == 'user_id' and _filter[i] == 0:
                #     tmp.append(i)
                #     continue
                if i == '_name':
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

        err, total, page_index, row_data = audit.get_auditors(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoGetAuditeesHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        # print('---get auditee:', args)

        sql_filter = {}
        sql_order = dict()
        sql_order['name'] = 'id'
        sql_order['asc'] = True
        sql_limit = dict()
        sql_limit['page_index'] = 0
        sql_limit['per_page'] = 25

        try:
            # tmp = list()
            # _filter = args['filter']
            # for i in _filter:
            #     # if i == 'user_id' and _filter[i] == 0:
            #     #     tmp.append(i)
            #     #     continue
            #     if i == '_name':
            #         if len(_filter[i].strip()) == 0:
            #             tmp.append(i)
            #
            # for i in tmp:
            #     del _filter[i]

            sql_filter.update(args['filter'])

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

        err, total, page_index, row_data = audit.get_auditees(sql_filter, sql_order, sql_limit)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)


class DoAddMembersHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            policy_id = int(args['policy_id'])
            policy_type = int(args['type'])
            ref_type = int(args['rtype'])
            members = args['members']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        err = audit.add_members(self, policy_id, policy_type, ref_type, members)
        self.write_json(err)


class DoRemoveMembersHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            policy_id = int(args['policy_id'])
            policy_type = int(args['policy_type'])
            ids = args['ids']
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        err = audit.remove_members(self, policy_id, policy_type, ids)
        self.write_json(err)


class RecordHandler(TPBaseHandler):
    def get(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ | TP_PRIVILEGE_AUDIT_AUZ | TP_PRIVILEGE_AUDIT)
        if ret != TPE_OK:
            return

        if not tp_cfg().core.detected:
            total_size = 0
            free_size = 0
        else:
            total_size, free_size = get_free_space_bytes(tp_cfg().core.replay_path)

        param = {
            'total_size': total_size,
            'free_size': free_size,
        }

        self.render('audit/record.mako', page_param=json.dumps(param))


class DoGetRecordsHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ | TP_PRIVILEGE_AUDIT_AUZ | TP_PRIVILEGE_AUDIT)
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

        err, total, row_data = record.get_records(self, sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude)
        ret = dict()
        ret['page_index'] = sql_limit['page_index']
        ret['total'] = total
        ret['data'] = row_data
        self.write_json(err, data=ret)


class ReplayHandler(TPBaseHandler):
    def get(self, protocol, record_id):
        protocol = int(protocol)
        if protocol == TP_PROTOCOL_TYPE_RDP:
            param = {'record_id': record_id}
            self.render('audit/replay-rdp.mako', page_param=json.dumps(param))
        elif protocol == TP_PROTOCOL_TYPE_SSH:
            param = {'record_id': record_id}
            self.render('audit/replay-ssh.mako', page_param=json.dumps(param))
        elif protocol == TP_PROTOCOL_TYPE_TELNET:
            param = {'record_id': record_id}
            self.render('audit/replay-telnet.mako', page_param=json.dumps(param))


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
#         self.root = tp_cfg().core.replay_path
#         # self.default_filename = default_filename
#
#
class ComandLogHandler(TPBaseHandler):
    @tornado.gen.coroutine
    def get(self, protocol, record_id):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ | TP_PRIVILEGE_AUDIT_AUZ | TP_PRIVILEGE_AUDIT)
        if ret != TPE_OK:
            return

        protocol = int(protocol)

        param = dict()
        header, err = record.read_record_head(protocol, record_id)
        if header is None:
            # return self.write('操作失败！[{}]'.format(err))
            param['code'] = err
            return self.render('audit/record-ssh-cmd.mako', page_param=json.dumps(param))

        # ret = dict()
        # ret['header'] = header
        # return self.write_json(0, data=ret)

        param['header'] = header
        param['count'] = 0
        param['op'] = list()
        param['code'] = TPE_OK

        cmd_type = 0  # 0 = ssh, 1 = sftp
        if protocol == 1:
            pass
        elif protocol == 2:
            record_path = os.path.join(tp_cfg().core.replay_path, 'ssh', '{:09d}'.format(int(record_id)))
            file_info = os.path.join(record_path, 'tp-ssh-cmd.txt')
            try:
                file = open(file_info, 'r')
                data = file.readlines()
                for i in range(len(data)):
                    cmd = data[i].rstrip('\r\n').split(',', 2)
                    if len(cmd) != 3:
                        continue
                    if 0 == i:
                        if 'SFTP INITIALIZE' == cmd[2]:
                            cmd_type = 1
                            continue

                    t = int(cmd[0])
                    f = int(cmd[1])

                    if cmd_type == 0:
                        param['op'].append({'t': t, 'f': f, 'c': cmd[2]})
                    else:
                        cmd_info = cmd[2].split(',', 2)
                        if len(cmd_info) != 3:
                            continue
                        c = int(cmd_info[0])
                        r = int(cmd_info[1])
                        p = cmd_info[2].split(':')
                        p1 = p[0]
                        p2 = ''
                        if len(p) > 1:
                            p2 = p[1]
                        param['op'].append({'t': t, 'c': c, 'r': r, 'p1': p1, 'p2': p2})
            except:
                pass
            # param['count'] = len(param['op'])

        if cmd_type == 0:
            self.render('audit/record-ssh-cmd.mako', page_param=json.dumps(param))
        else:
            self.render('audit/record-sftp-cmd.mako', page_param=json.dumps(param))


class DoGetRecordHeaderHandler(TPBaseJsonHandler):
    @tornado.gen.coroutine
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_OPS_AUZ | TP_PRIVILEGE_AUDIT_AUZ | TP_PRIVILEGE_AUDIT)
        if ret != TPE_OK:
            return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            protocol_type = int(args['protocol'])
            record_id = int(args['id'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        header, err = record.read_record_head(protocol_type, record_id)
        if header is None:
            return self.write_json(err)

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
            protocol_type = int(args['protocol'])
            record_id = int(args['id'])
            offset = int(args['offset'])
        except:
            log.e('\n')
            return self.write_json(TPE_PARAM)

        if protocol_type == TP_PROTOCOL_TYPE_RDP:
            data_list, data_size, err = record.read_rdp_record_data(record_id, offset)
        elif protocol_type == TP_PROTOCOL_TYPE_SSH:
            data_list, data_size, err = record.read_ssh_record_data(record_id, offset)
        elif protocol_type == TP_PROTOCOL_TYPE_TELNET:
            data_list, data_size, err = record.read_telnet_record_data(record_id, offset)
        else:
            self.write_json(TPE_NOT_EXISTS)
        self.write_json(err, data={'data_list': data_list, 'data_size': data_size})


class DoGetFileHandler(TPBaseHandler):
    @tornado.gen.coroutine
    def get(self):

        # log.v('--{}\n'.format(self.request.uri))

        require_privilege = TP_PRIVILEGE_OPS_AUZ | TP_PRIVILEGE_AUDIT_AUZ | TP_PRIVILEGE_AUDIT

        # sid = self.get_argument('sid', None)
        # if sid is None:
        #     self.set_status(403)
        #     return self.write('need login first.')
        #
        # self._s_id = sid
        # _user = self.get_session('user')
        # if _user is None:
        #     self.set_status(403)
        #     return self.write('need login first.')
        # self._user = _user

        if not self._user['_is_login']:
            self.set_status(401)  # 401=未授权, 要求身份验证
            return self.write('need login first.')
        if (self._user['privilege'] & require_privilege) == 0:
            self.set_status(403)  # 403=禁止
            return self.write('you have no such privilege.')

        act = self.get_argument('act', None)
        _type = self.get_argument('type', None)
        rid = self.get_argument('rid', None)
        filename = self.get_argument('f', None)
        offset = int(self.get_argument('offset', '0'))
        length = int(self.get_argument('length', '-1'))  # -1 means read all content.
        if act is None or _type is None or rid is None or filename is None:
            self.set_status(400)  # 400=错误请求
            return self.write('invalid param, `rid` and `f` must present.')

        if act not in ['size', 'read']:
            self.set_status(400)
            return self.write('invalid param, `act` should be `size` or `read`.')
        if _type not in ['rdp', 'ssh', 'telnet']:
            self.set_status(400)
            return self.write('invalid param, `type` should be `rdp`, `ssh` or `telnet`.')

        file = os.path.join(tp_cfg().core.replay_path, 'rdp', '{:09d}'.format(int(rid)), filename)
        if not os.path.exists(file):
            self.set_status(404)
            return self.write('file does not exists.')

        file_size = os.path.getsize(file)

        if act == 'size':
            # log.d('--return size:{}\n'.format(file_size))
            return self.write('{}'.format(file_size))

        if offset >= file_size:
            self.set_status(416)  # 416=请求范围不符合要求
            return self.write('no more data.')

        # we read most 4096 bytes one time.
        BULK_SIZE = 4096
        total_need = file_size - offset
        if length != -1 and length < total_need:
            total_need = length
        total_read = 0
        with open(file, 'rb') as f:
            f.seek(offset)
            read_this_time = BULK_SIZE if total_need > BULK_SIZE else total_need
            while read_this_time > 0:
                self.write(f.read(read_this_time))
                total_read += read_this_time
                if total_read >= total_need:
                    break
                read_left = total_need - total_read
                read_this_time = BULK_SIZE if read_left > BULK_SIZE else read_left

        # all need data read.


class DoBuildAuzMapHandler(TPBaseJsonHandler):
    def post(self):
        ret = self.check_privilege(TP_PRIVILEGE_AUDIT_AUZ)
        if ret != TPE_OK:
            return

        err = audit.build_auz_map()
        self.write_json(err)
