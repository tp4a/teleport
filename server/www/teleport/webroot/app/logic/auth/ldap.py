# -*- coding: utf-8 -*-

import ldap3
from app.base.logger import *
from app.const import *


class Ldap(object):
    def __init__(self, ldap_host, ldap_port, base_dn, domain):
        self._server = ldap3.Server(ldap_host, ldap_port, connect_timeout=5, use_ssl=False)
        self._base_dn = base_dn
        self._domain = domain
        pass

    def _parse_attr_map(self, attr_map):
        attrs_ldap = []
        attrs_tp = []

        lines = attr_map.split('\n')
        for line in lines:
            x = line.split('=')
            if len(x) != 2:
                return None, None, line
            y = x[0].strip().split('.')
            if len(y) != 2 or 'tp' != y[0]:
                return None, None, line
            tp_attr = y[1]
            ldap_attr = x[1].strip()
            if len(tp_attr) == 0 or len(ldap_attr) == 0:
                return None, None, line
            attrs_ldap.append(ldap_attr)
            attrs_tp.append(tp_attr)

        return attrs_ldap, attrs_tp, ''

    def list_users(self, admin, password, filter, attr_map, size_limit=0):
        attrs_ldap, attrs_tp, msg = self._parse_attr_map(attr_map)
        if attrs_ldap is None:
            return TPE_PARAM, None, '属性映射格式错误: {}'.format(msg)

        user = '{}@{}'.format(admin, self._domain)
        conn = ldap3.Connection(self._server, user=user, password=password, check_names=True, lazy=False, raise_exceptions=False)
        try:
            conn.open()
        except Exception as e:
            log.e(str(e))
            return TPE_FAILED, None, '无法连接到LDAP服务器'

        conn.bind()
        if not ('result' in conn.result and 0 == conn.result['result'] and 'description' in conn.result and 'success' == conn.result['description']):
            return TPE_FAILED, None, 'LDAP管理员认证失败'

        ret = conn.search(
            search_base=self._base_dn,
            size_limit=size_limit,

            # search_filter='(&(sAMAccountName={}*)(&(objectClass=person)))'.format(username),
            search_filter=filter,  # (&(objectClass=person))
            search_scope=ldap3.SUBTREE,

            # attributes=['cn', 'mail', 'sAMAccountName', 'objectGUID']
            # attributes=['*']
            attributes=attrs_ldap
        )

        result = []

        # print(self.conn.entries[0].entry_to_json)

        if ret:
            for u in conn.response:
                # if u['attributes']['cn'].lower() in ['guest', 'krbtgt']:
                #     continue
                # print(u)
                # print(u['attributes']['cn'])
                # result.append(u['attributes'])
                a = {}
                for i in range(0, len(attrs_ldap)):
                    a[attrs_tp[i]] = u['attributes'][attrs_ldap[i]]
                result.append(a)

        return TPE_OK, result, ''

    def valid_user(self, user_dn, password):
        return False

