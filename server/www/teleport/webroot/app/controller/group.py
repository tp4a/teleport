# -*- coding: utf-8 -*-

import json
from app.const import *
from app.model import group
from app.base.controller import TPBaseJsonHandler


class DoUpdateGroupHandler(TPBaseJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            gtype = int(args['gtype'])
            gid = int(args['gid'])
            name = args['name']
            desc = args['desc']
        except:
            return self.write_json(TPE_PARAM)

        if gid == -1:
            err, _ = group.create(self, gtype, name, desc)
        else:
            err = group.update(self, gid, name, desc)

        self.write_json(err)


class DoLockGroupHandler(TPBaseJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            gtype = args['gtype']
            glist = args['glist']
        except:
            return self.write_json(TPE_PARAM)

        err = group.update_groups_state(self, gtype, glist, TP_STATE_DISABLED)

        self.write_json(err)


class DoUnlockGroupHandler(TPBaseJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            gtype = args['gtype']
            glist = args['glist']
        except:
            return self.write_json(TPE_PARAM)

        err = group.update_groups_state(self, gtype, glist, TP_STATE_NORMAL)

        self.write_json(err)


class DoRemoveGroupHandler(TPBaseJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            gtype = args['gtype']
            glist = args['glist']
        except:
            return self.write_json(TPE_PARAM)

        err = group.remove(self, gtype, glist)

        self.write_json(err)


class DoAddMembersHandler(TPBaseJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            gtype = int(args['gtype'])
            gid = int(args['gid'])
            members = args['members']
        except:
            return self.write_json(TPE_PARAM)

        err = group.add_members(gtype, gid, members)
        self.write_json(err)


class DoRemoveMembersHandler(TPBaseJsonHandler):
    def post(self):
        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        try:
            gtype = int(args['gtype'])
            gid = int(args['gid'])
            members = args['members']
        except:
            return self.write_json(TPE_PARAM)

        err = group.remove_members(gtype, gid, members)
        self.write_json(err)


class DoGetGroupsHandler(TPBaseJsonHandler):
    def post(self):
        # ret = self.check_privilege(TP_PRIVILEGE_USER_GROUP)
        # if ret != TPE_OK:
        #     return

        args = self.get_argument('args', None)
        if args is None:
            return self.write_json(TPE_PARAM)
        try:
            args = json.loads(args)
        except:
            return self.write_json(TPE_JSON_FORMAT)

        # print('---get groups:', args)

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
                if i == 'search':
                    _x = _filter[i].strip()
                    if len(_x) == 0:
                        tmp.append(i)
                    continue

            for i in tmp:
                del _filter[i]

            sql_filter.update(_filter)
            # sql_filter.update(args['filter'])

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

        err, total_count, page_index, row_data = group.get_groups(sql_filter, sql_order, sql_limit, sql_restrict, sql_exclude)
        ret = dict()
        ret['page_index'] = page_index
        ret['total'] = total_count
        ret['data'] = row_data
        self.write_json(err, data=ret)
