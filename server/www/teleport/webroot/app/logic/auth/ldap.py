# -*- coding: utf-8 -*-

import json
import ldap3
import ldap3.core.exceptions
from app.base.logger import *
from app.const import *


class Ldap(object):
    def __init__(self, ldap_host, ldap_port, base_dn):
        self._server = ldap3.Server(ldap_host, ldap_port, connect_timeout=5, use_ssl=False)
        self._base_dn = base_dn

    @staticmethod
    def _parse_attr_map(attr_username, attr_surname, attr_email):
        attrs_ldap = []
        attrs_tp = []

        if len(attr_username) > 0:
            attrs_ldap.append(attr_username)
            attrs_tp.append('username')
        if len(attr_surname) > 0:
            attrs_ldap.append(attr_surname)
            attrs_tp.append('surname')
        if len(attr_email) > 0:
            attrs_ldap.append(attr_email)
            attrs_tp.append('email')

        if len(attrs_ldap) > 0:
            return attrs_ldap, attrs_tp
        else:
            return None, None

        # lines = attr_map.split('\n')
        # for line in lines:
        #     x = line.split('=')
        #     if len(x) != 2:
        #         return None, None, line
        #     y = x[0].strip().split('.')
        #     if len(y) != 2 or 'tp' != y[0]:
        #         return None, None, line
        #     tp_attr = y[1]
        #     ldap_attr = x[1].strip()
        #     if len(tp_attr) == 0 or len(ldap_attr) == 0:
        #         return None, None, line
        #     attrs_ldap.append(ldap_attr)
        #     attrs_tp.append(tp_attr)
        #
        # return attrs_ldap, attrs_tp, ''

    def get_all_attr(self, admin, password, search_filter):
        conn = ldap3.Connection(
            self._server, user=admin, password=password, check_names=True, lazy=False, raise_exceptions=False
        )

        try:
            conn.open()
        except Exception as e:
            log.e(str(e))
            return TPE_FAILED, None, '无法连接到LDAP服务器'

        conn.bind()
        if not (
                ('result' in conn.result and 0 == conn.result['result'])
                and
                ('description' in conn.result and 'success' == conn.result['description'])
        ):
            return TPE_FAILED, None, 'LDAP管理员认证失败'

        ret = conn.search(
            search_base=self._base_dn,
            size_limit=1,
            search_filter=search_filter,  # (&(objectClass=person))
            search_scope=ldap3.SUBTREE,
            attributes=['*']
        )
        if not ret:
            return TPE_FAILED, None, '未能找到任何用户'

        if len(conn.response) == 0:
            return TPE_FAILED, None, '未能找到任何用户'

        result = json.loads(conn.entries[0].entry_to_json())
        for attr_name in result:
            attr_val = result[attr_name]
            if isinstance(result[attr_name], list):
                if len(attr_val) >= 1:
                    attr_val = attr_val[0]
                else:
                    attr_val = ''
            result[attr_name] = attr_val
        return TPE_OK, result, ''

    def list_users(self, admin, password, search_filter, attr_username, attr_surname, attr_email, size_limit=0):
        attrs_ldap, attrs_tp = self._parse_attr_map(attr_username, attr_surname, attr_email)
        if attrs_ldap is None:
            return TPE_PARAM, None, '属性映射错误'

        user = admin
        conn = ldap3.Connection(
            self._server, user=user, password=password, check_names=True, lazy=False, raise_exceptions=False
        )
        try:
            conn.open()
        except Exception as e:
            log.e(str(e))
            return TPE_FAILED, None, '无法连接到LDAP服务器'

        conn.bind()
        if not (
                ('result' in conn.result and 0 == conn.result['result'])
                and
                ('description' in conn.result and 'success' == conn.result['description'])
        ):
            return TPE_FAILED, None, 'LDAP管理员认证失败'

        try:
            ret = conn.search(
                search_base=self._base_dn,
                size_limit=size_limit,
                search_filter=search_filter,  # (&(objectClass=person))
                search_scope=ldap3.SUBTREE,
                attributes=attrs_ldap
            )

            if not ret:
                return TPE_FAILED, None, '未能搜索到LDAP用户，请检查用户基准DN和过滤器设置'

        except ldap3.core.exceptions.LDAPAttributeError as e:
            log.e('')
            return TPE_FAILED, None, '请检查属性映射设置：{}'.format(e.__str__())

        result = {}

        for i in range(0, len(conn.entries)):
            attrs = json.loads(conn.entries[i].entry_to_json())
            user = {}
            for m in range(0, len(attrs_ldap)):
                ldap_name = attrs_ldap[m]
                tp_name = attrs_tp[m]
                attr_val = attrs['attributes'][ldap_name]
                if isinstance(attr_val, list):
                    if len(attr_val) >= 1:
                        attr_val = attr_val[0]
                    else:
                        attr_val = ''
                user[tp_name] = attr_val
            result[attrs['dn']] = user

        return TPE_OK, result, ''

    def valid_user(self, user_dn, password):
        conn = ldap3.Connection(
            self._server, user=user_dn, password=password, check_names=True, lazy=False, raise_exceptions=False
        )

        try:
            conn.open()
        except Exception as e:
            log.e(str(e))
            return TPE_FAILED, '无法连接到LDAP服务器'

        conn.bind()
        if not (
                ('result' in conn.result and 0 == conn.result['result'])
                and
                ('description' in conn.result and 'success' == conn.result['description'])
        ):
            return TPE_USER_AUTH, '认证失败'

        return TPE_OK, ''
