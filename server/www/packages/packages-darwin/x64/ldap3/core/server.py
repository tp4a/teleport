"""
"""

# Created on 2014.05.31
#
# Author: Giovanni Cannata
#
# Copyright 2014 - 2018 Giovanni Cannata
#
# This file is part of ldap3.
#
# ldap3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ldap3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with ldap3 in the COPYING and COPYING.LESSER files.
# If not, see <http://www.gnu.org/licenses/>.

import socket
from threading import Lock
from datetime import datetime, MINYEAR

from .. import DSA, SCHEMA, ALL, BASE, get_config_parameter, OFFLINE_EDIR_8_8_8, OFFLINE_AD_2012_R2, OFFLINE_SLAPD_2_4, OFFLINE_DS389_1_3_3, SEQUENCE_TYPES, IP_SYSTEM_DEFAULT, IP_V4_ONLY, IP_V6_ONLY, IP_V4_PREFERRED, IP_V6_PREFERRED, STRING_TYPES
from .exceptions import LDAPInvalidServerError, LDAPDefinitionError, LDAPInvalidPortError, LDAPInvalidTlsSpecificationError, LDAPSocketOpenError
from ..protocol.formatters.standard import format_attribute_values
from ..protocol.rfc4511 import LDAP_MAX_INT
from ..protocol.rfc4512 import SchemaInfo, DsaInfo
from .tls import Tls
from ..utils.log import log, log_enabled, ERROR, BASIC, PROTOCOL
from ..utils.conv import to_unicode

try:
    from urllib.parse import unquote  # Python 3
except ImportError:
    from urllib import unquote  # Python 2

try:  # try to discover if unix sockets are available for LDAP over IPC (ldapi:// scheme)
    # noinspection PyUnresolvedReferences
    from socket import AF_UNIX
    unix_socket_available = True
except ImportError:
    unix_socket_available = False


class Server(object):
    """
    LDAP Server definition class

    Allowed_referral_hosts can be None (default), or a list of tuples of
    allowed servers ip address or names to contact while redirecting
    search to referrals.

    The second element of the tuple is a boolean to indicate if
    authentication to that server is allowed; if False only anonymous
    bind will be used.

    Per RFC 4516. Use [('*', False)] to allow any host with anonymous
    bind, use [('*', True)] to allow any host with same authentication of
    Server.
    """

    _message_counter = 0
    _message_id_lock = Lock()  # global lock for message_id shared by all Server objects


    def __init__(self,
                 host,
                 port=None,
                 use_ssl=False,
                 allowed_referral_hosts=None,
                 get_info=SCHEMA,
                 tls=None,
                 formatter=None,
                 connect_timeout=None,
                 mode=IP_V6_PREFERRED,
                 validator=None):

        self.ipc = False
        url_given = False
        host = host.strip()
        if host.lower().startswith('ldap://'):
            self.host = host[7:]
            use_ssl = False
            url_given = True
        elif host.lower().startswith('ldaps://'):
            self.host = host[8:]
            use_ssl = True
            url_given = True
        elif host.lower().startswith('ldapi://') and unix_socket_available:
            self.ipc = True
            use_ssl = False
            url_given = True
        elif host.lower().startswith('ldapi://') and not unix_socket_available:
            raise LDAPSocketOpenError('LDAP over IPC not available - UNIX sockets non present')
        else:
            self.host = host

        if self.ipc:
            if str is bytes:  # Python 2
                self.host = unquote(host[7:]).decode('utf-8')
            else:  # Python 3
                self.host = unquote(host[7:])  # encoding defaults to utf-8 in python3
            self.port = None
        elif ':' in self.host and self.host.count(':') == 1:
            hostname, _, hostport = self.host.partition(':')
            try:
                port = int(hostport) or port
            except ValueError:
                if log_enabled(ERROR):
                    log(ERROR, 'port <%s> must be an integer', port)
                raise LDAPInvalidPortError('port must be an integer')
            self.host = hostname
        elif url_given and self.host.startswith('['):
            hostname, sep, hostport = self.host[1:].partition(']')
            if sep != ']' or not self._is_ipv6(hostname):
                if log_enabled(ERROR):
                    log(ERROR, 'invalid IPv6 server address for <%s>', self.host)
                raise LDAPInvalidServerError()
            if len(hostport):
                if not hostport.startswith(':'):
                    if log_enabled(ERROR):
                        log(ERROR, 'invalid URL in server name for <%s>', self.host)
                    raise LDAPInvalidServerError('invalid URL in server name')
                if not hostport[1:].isdecimal():
                    if log_enabled(ERROR):
                        log(ERROR, 'port must be an integer for <%s>', self.host)
                    raise LDAPInvalidPortError('port must be an integer')
                port = int(hostport[1:])
            self.host = hostname
        elif not url_given and self._is_ipv6(self.host):
            pass
        elif self.host.count(':') > 1:
            if log_enabled(ERROR):
                log(ERROR, 'invalid server address for <%s>', self.host)
            raise LDAPInvalidServerError()

        if not self.ipc:
            self.host.rstrip('/')
            if not use_ssl and not port:
                port = 389
            elif use_ssl and not port:
                port = 636

            if isinstance(port, int):
                if port in range(0, 65535):
                    self.port = port
                else:
                    if log_enabled(ERROR):
                        log(ERROR, 'port <%s> must be in range from 0 to 65535', port)
                    raise LDAPInvalidPortError('port must in range from 0 to 65535')
            else:
                if log_enabled(ERROR):
                    log(ERROR, 'port <%s> must be an integer', port)
                raise LDAPInvalidPortError('port must be an integer')

        if allowed_referral_hosts is None:  # defaults to any server with authentication
            allowed_referral_hosts = [('*', True)]

        if isinstance(allowed_referral_hosts, SEQUENCE_TYPES):
            self.allowed_referral_hosts = []
            for referral_host in allowed_referral_hosts:
                if isinstance(referral_host, tuple):
                    if isinstance(referral_host[1], bool):
                        self.allowed_referral_hosts.append(referral_host)
        elif isinstance(allowed_referral_hosts, tuple):
            if isinstance(allowed_referral_hosts[1], bool):
                self.allowed_referral_hosts = [allowed_referral_hosts]
        else:
            self.allowed_referral_hosts = []

        self.ssl = True if use_ssl else False
        if tls and not isinstance(tls, Tls):
            if log_enabled(ERROR):
                log(ERROR, 'invalid tls specification: <%s>', tls)
            raise LDAPInvalidTlsSpecificationError('invalid Tls object')

        self.tls = Tls() if self.ssl and not tls else tls

        if not self.ipc:
            if self._is_ipv6(self.host):
                self.name = ('ldaps' if self.ssl else 'ldap') + '://[' + self.host + ']:' + str(self.port)
            else:
                self.name = ('ldaps' if self.ssl else 'ldap') + '://' + self.host + ':' + str(self.port)
        else:
            self.name = host

        self.get_info = get_info
        self._dsa_info = None
        self._schema_info = None
        self.dit_lock = Lock()
        self.custom_formatter = formatter
        self.custom_validator = validator
        self._address_info = []  # property self.address_info resolved at open time (or when check_availability is called)
        self._address_info_resolved_time = datetime(MINYEAR, 1, 1)  # smallest date ever
        self.current_address = None
        self.connect_timeout = connect_timeout
        self.mode = mode

        self.get_info_from_server(None)  # load offline schema if needed

        if log_enabled(BASIC):
            log(BASIC, 'instantiated Server: <%r>', self)

    @staticmethod
    def _is_ipv6(host):
        try:
            socket.inet_pton(socket.AF_INET6, host)
        except (socket.error, AttributeError, ValueError):
            return False
        return True

    def __str__(self):
        if self.host:
            s = self.name + (' - ssl' if self.ssl else ' - cleartext') + (' - unix socket' if self.ipc else '')
        else:
            s = object.__str__(self)
        return s

    def __repr__(self):
        r = 'Server(host={0.host!r}, port={0.port!r}, use_ssl={0.ssl!r}'.format(self)
        r += '' if not self.allowed_referral_hosts else ', allowed_referral_hosts={0.allowed_referral_hosts!r}'.format(self)
        r += '' if self.tls is None else ', tls={0.tls!r}'.format(self)
        r += '' if not self.get_info else ', get_info={0.get_info!r}'.format(self)
        r += '' if not self.connect_timeout else ', connect_timeout={0.connect_timeout!r}'.format(self)
        r += '' if not self.mode else ', mode={0.mode!r}'.format(self)
        r += ')'

        return r

    @property
    def address_info(self):
        conf_refresh_interval = get_config_parameter('ADDRESS_INFO_REFRESH_TIME')
        if not self._address_info or (datetime.now() - self._address_info_resolved_time).seconds > conf_refresh_interval:
            # converts addresses tuple to list and adds a 6th parameter for availability (None = not checked, True = available, False=not available) and a 7th parameter for the checking time
            addresses = None
            try:
                if self.ipc:
                    addresses = [(socket.AF_UNIX, socket.SOCK_STREAM, 0, None, self.host, None)]
                else:
                    addresses = socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM, socket.IPPROTO_TCP, socket.AI_ADDRCONFIG | socket.AI_V4MAPPED)
            except (socket.gaierror, AttributeError):
                pass

            if not addresses:  # if addresses not found or raised an exception (for example for bad flags) tries again without flags
                try:
                    addresses = socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM, socket.IPPROTO_TCP)
                except socket.gaierror:
                    pass

            if addresses:
                self._address_info = [list(address) + [None, None] for address in addresses]
                self._address_info_resolved_time = datetime.now()
            else:
                self._address_info = []
                self._address_info_resolved_time = datetime(MINYEAR, 1, 1)  # smallest date

            if log_enabled(BASIC):
                for address in self._address_info:
                    log(BASIC, 'address for <%s> resolved as <%r>', self, address[:-2])
        return self._address_info

    def update_availability(self, address, available):
        cont = 0
        while cont < len(self._address_info):
            if self.address_info[cont] == address:
                self._address_info[cont][5] = True if available else False
                self._address_info[cont][6] = datetime.now()
                break
            cont += 1

    def reset_availability(self):
        for address in self._address_info:
            address[5] = None
            address[6] = None

    def check_availability(self):
        """
        Tries to open, connect and close a socket to specified address
        and port to check availability. Timeout in seconds is specified in CHECK_AVAILABITY_TIMEOUT if not specified in
        the Server object
        """
        conf_availability_timeout = get_config_parameter('CHECK_AVAILABILITY_TIMEOUT')
        available = False
        self.reset_availability()
        for address in self.candidate_addresses():
            available = True
            try:
                temp_socket = socket.socket(*address[:3])
                if self.connect_timeout:
                    temp_socket.settimeout(self.connect_timeout)
                else:
                    temp_socket.settimeout(conf_availability_timeout)  # set timeout for checking availability to default
                try:
                    temp_socket.connect(address[4])
                except socket.error:
                    available = False
                finally:
                    try:
                        temp_socket.shutdown(socket.SHUT_RDWR)
                    except socket.error:
                        available = False
                    finally:
                        temp_socket.close()
            except socket.gaierror:
                available = False

            if available:
                if log_enabled(BASIC):
                    log(BASIC, 'server <%s> available at <%r>', self, address)
                self.update_availability(address, True)
                break  # if an available address is found exits immediately
            else:
                self.update_availability(address, False)
                if log_enabled(ERROR):
                    log(ERROR, 'server <%s> not available at <%r>', self, address)

        return available

    @staticmethod
    def next_message_id():
        """
        LDAP messageId is unique for all connections to same server
        """
        with Server._message_id_lock:
            Server._message_counter += 1
            if Server._message_counter >= LDAP_MAX_INT:
                Server._message_counter = 1
            if log_enabled(PROTOCOL):
                log(PROTOCOL, 'new message id <%d> generated', Server._message_counter)

        return Server._message_counter

    def _get_dsa_info(self, connection):
        """
        Retrieve DSE operational attribute as per RFC4512 (5.1).
        """
        if connection.strategy.no_real_dsa:  # do not try for mock strategies
            return

        if not connection.strategy.pooled:  # in pooled strategies get_dsa_info is performed by the worker threads
            result = connection.search(search_base='',
                                       search_filter='(objectClass=*)',
                                       search_scope=BASE,
                                       attributes=['altServer',  # requests specific dsa info attributes
                                                   'namingContexts',
                                                   'supportedControl',
                                                   'supportedExtension',
                                                   'supportedFeatures',
                                                   'supportedCapabilities',
                                                   'supportedLdapVersion',
                                                   'supportedSASLMechanisms',
                                                   'vendorName',
                                                   'vendorVersion',
                                                   'subschemaSubentry',
                                                   '*',
                                                   '+'],  # requests all remaining attributes (other),
                                       get_operational_attributes=True)

            with self.dit_lock:
                if isinstance(result, bool):  # sync request
                    self._dsa_info = DsaInfo(connection.response[0]['attributes'], connection.response[0]['raw_attributes']) if result else self._dsa_info
                elif result:  # asynchronous request, must check if attributes in response
                    results, _ = connection.get_response(result)
                    if len(results) == 1 and 'attributes' in results[0] and 'raw_attributes' in results[0]:
                        self._dsa_info = DsaInfo(results[0]['attributes'], results[0]['raw_attributes'])

            if log_enabled(BASIC):
                log(BASIC, 'DSA info read for <%s> via <%s>', self, connection)

    def _get_schema_info(self, connection, entry=''):
        """
        Retrieve schema from subschemaSubentry DSE attribute, per RFC
        4512 (4.4 and 5.1); entry = '' means DSE.
        """
        if connection.strategy.no_real_dsa:  # do not try for mock strategies
            return

        schema_entry = None
        if self._dsa_info and entry == '':  # subschemaSubentry already present in dsaInfo
            if isinstance(self._dsa_info.schema_entry, SEQUENCE_TYPES):
                schema_entry = self._dsa_info.schema_entry[0] if self._dsa_info.schema_entry else None
            else:
                schema_entry = self._dsa_info.schema_entry if self._dsa_info.schema_entry else None
        else:
            result = connection.search(entry, '(objectClass=*)', BASE, attributes=['subschemaSubentry'], get_operational_attributes=True)
            if isinstance(result, bool):  # sync request
                if result and 'subschemaSubentry' in connection.response[0]['raw_attributes']:
                    if len(connection.response[0]['raw_attributes']['subschemaSubentry']) > 0:
                        schema_entry = connection.response[0]['raw_attributes']['subschemaSubentry'][0]
            else:  # asynchronous request, must check if subschemaSubentry in attributes
                results, _ = connection.get_response(result)
                if len(results) == 1 and 'raw_attributes' in results[0] and 'subschemaSubentry' in results[0]['attributes']:
                    if len(results[0]['raw_attributes']['subschemaSubentry']) > 0:
                        schema_entry = results[0]['raw_attributes']['subschemaSubentry'][0]

        if schema_entry and not connection.strategy.pooled:  # in pooled strategies get_schema_info is performed by the worker threads
            if isinstance(schema_entry, bytes) and str is not bytes:  # Python 3
                schema_entry = to_unicode(schema_entry, from_server=True)
            result = connection.search(schema_entry,
                                       search_filter='(objectClass=subschema)',
                                       search_scope=BASE,
                                       attributes=['objectClasses',  # requests specific subschema attributes
                                                   'attributeTypes',
                                                   'ldapSyntaxes',
                                                   'matchingRules',
                                                   'matchingRuleUse',
                                                   'dITContentRules',
                                                   'dITStructureRules',
                                                   'nameForms',
                                                   'createTimestamp',
                                                   'modifyTimestamp',
                                                   '*'],  # requests all remaining attributes (other)
                                       get_operational_attributes=True
                                       )
            with self.dit_lock:
                self._schema_info = None
                if result:
                    if isinstance(result, bool):  # sync request
                        self._schema_info = SchemaInfo(schema_entry, connection.response[0]['attributes'], connection.response[0]['raw_attributes']) if result else None
                    else:  # asynchronous request, must check if attributes in response
                        results, result = connection.get_response(result)
                        if len(results) == 1 and 'attributes' in results[0] and 'raw_attributes' in results[0]:
                            self._schema_info = SchemaInfo(schema_entry, results[0]['attributes'], results[0]['raw_attributes'])
                    if self._schema_info and not self._schema_info.is_valid():  # flaky servers can return an empty schema, checks if it is so and set schema to None
                        self._schema_info = None
                    if self._schema_info:  # if schema is valid tries to apply formatter to the "other" dict with raw values for schema and info
                        for attribute in self._schema_info.other:
                            self._schema_info.other[attribute] = format_attribute_values(self._schema_info, attribute, self._schema_info.raw[attribute], self.custom_formatter)
                        if self._dsa_info:  # try to apply formatter to the "other" dict with dsa info raw values
                            for attribute in self._dsa_info.other:
                                self._dsa_info.other[attribute] = format_attribute_values(self._schema_info, attribute, self._dsa_info.raw[attribute], self.custom_formatter)
            if log_enabled(BASIC):
                log(BASIC, 'schema read for <%s> via <%s>', self, connection)

    def get_info_from_server(self, connection):
        """
        reads info from DSE and from subschema
        """
        if connection and not connection.closed:
            if self.get_info in [DSA, ALL]:
                self._get_dsa_info(connection)
            if self.get_info in [SCHEMA, ALL]:
                    self._get_schema_info(connection)
        elif self.get_info == OFFLINE_EDIR_8_8_8:
            from ..protocol.schemas.edir888 import edir_8_8_8_schema, edir_8_8_8_dsa_info
            self.attach_schema_info(SchemaInfo.from_json(edir_8_8_8_schema))
            self.attach_dsa_info(DsaInfo.from_json(edir_8_8_8_dsa_info))
        elif self.get_info == OFFLINE_AD_2012_R2:
            from ..protocol.schemas.ad2012R2 import ad_2012_r2_schema, ad_2012_r2_dsa_info
            self.attach_schema_info(SchemaInfo.from_json(ad_2012_r2_schema))
            self.attach_dsa_info(DsaInfo.from_json(ad_2012_r2_dsa_info))
        elif self.get_info == OFFLINE_SLAPD_2_4:
            from ..protocol.schemas.slapd24 import slapd_2_4_schema, slapd_2_4_dsa_info
            self.attach_schema_info(SchemaInfo.from_json(slapd_2_4_schema))
            self.attach_dsa_info(DsaInfo.from_json(slapd_2_4_dsa_info))
        elif self.get_info == OFFLINE_DS389_1_3_3:
            from ..protocol.schemas.ds389 import ds389_1_3_3_schema, ds389_1_3_3_dsa_info
            self.attach_schema_info(SchemaInfo.from_json(ds389_1_3_3_schema))
            self.attach_dsa_info(DsaInfo.from_json(ds389_1_3_3_dsa_info))

    def attach_dsa_info(self, dsa_info=None):
        if isinstance(dsa_info, DsaInfo):
            self._dsa_info = dsa_info
            if log_enabled(BASIC):
                log(BASIC, 'attached DSA info to Server <%s>', self)

    def attach_schema_info(self, dsa_schema=None):
        if isinstance(dsa_schema, SchemaInfo):
            self._schema_info = dsa_schema
        if log_enabled(BASIC):
            log(BASIC, 'attached schema info to Server <%s>', self)

    @property
    def info(self):
        return self._dsa_info

    @property
    def schema(self):
        return self._schema_info

    @staticmethod
    def from_definition(host, dsa_info, dsa_schema, port=None, use_ssl=False, formatter=None, validator=None):
        """
        Define a dummy server with preloaded schema and info
        :param host: host name
        :param dsa_info: DsaInfo preloaded object or a json formatted string or a file name
        :param dsa_schema: SchemaInfo preloaded object or a json formatted string or a file name
        :param port: dummy port
        :param use_ssl: use_ssl
        :param formatter: custom formatter
        :return: Server object
        """
        if isinstance(host, SEQUENCE_TYPES):
            dummy = Server(host=host[0], port=port, use_ssl=use_ssl, formatter=formatter, validator=validator, get_info=ALL)  # for ServerPool object
        else:
            dummy = Server(host=host, port=port, use_ssl=use_ssl, formatter=formatter, validator=validator, get_info=ALL)
        if isinstance(dsa_info, DsaInfo):
            dummy._dsa_info = dsa_info
        elif isinstance(dsa_info, STRING_TYPES):
            try:
                dummy._dsa_info = DsaInfo.from_json(dsa_info)  # tries to use dsa_info as a json configuration string
            except Exception:
                dummy._dsa_info = DsaInfo.from_file(dsa_info)  # tries to use dsa_info as a file name

        if not dummy.info:
            if log_enabled(ERROR):
                log(ERROR, 'invalid DSA info for %s', host)
            raise LDAPDefinitionError('invalid dsa info')

        if isinstance(dsa_schema, SchemaInfo):
            dummy._schema_info = dsa_schema
        elif isinstance(dsa_schema, STRING_TYPES):
            try:
                dummy._schema_info = SchemaInfo.from_json(dsa_schema)
            except Exception:
                dummy._schema_info = SchemaInfo.from_file(dsa_schema)

        if not dummy.schema:
            if log_enabled(ERROR):
                log(ERROR, 'invalid schema info for %s', host)
            raise LDAPDefinitionError('invalid schema info')

        if log_enabled(BASIC):
            log(BASIC, 'created server <%s> from definition', dummy)

        return dummy

    def candidate_addresses(self):
        conf_reset_availability_timeout = get_config_parameter('RESET_AVAILABILITY_TIMEOUT')
        if self.ipc:
            candidates = self.address_info
            if log_enabled(BASIC):
                log(BASIC, 'candidate address for <%s>: <%s> with mode UNIX_SOCKET', self, self.name)
        else:
            # checks reset availability timeout
            for address in self.address_info:
                if address[6] and ((datetime.now() - address[6]).seconds > conf_reset_availability_timeout):
                    address[5] = None
                    address[6] = None

            # selects server address based on server mode and availability (in address[5])
            addresses = self.address_info[:]  # copy to avoid refreshing while searching candidates
            candidates = []
            if addresses:
                if self.mode == IP_SYSTEM_DEFAULT:
                    candidates.append(addresses[0])
                elif self.mode == IP_V4_ONLY:
                    candidates = [address for address in addresses if address[0] == socket.AF_INET and (address[5] or address[5] is None)]
                elif self.mode == IP_V6_ONLY:
                    candidates = [address for address in addresses if address[0] == socket.AF_INET6 and (address[5] or address[5] is None)]
                elif self.mode == IP_V4_PREFERRED:
                    candidates = [address for address in addresses if address[0] == socket.AF_INET and (address[5] or address[5] is None)]
                    candidates += [address for address in addresses if address[0] == socket.AF_INET6 and (address[5] or address[5] is None)]
                elif self.mode == IP_V6_PREFERRED:
                    candidates = [address for address in addresses if address[0] == socket.AF_INET6 and (address[5] or address[5] is None)]
                    candidates += [address for address in addresses if address[0] == socket.AF_INET and (address[5] or address[5] is None)]
                else:
                    if log_enabled(ERROR):
                        log(ERROR, 'invalid server mode for <%s>', self)
                    raise LDAPInvalidServerError('invalid server mode')

            if log_enabled(BASIC):
                for candidate in candidates:
                    log(BASIC, 'obtained candidate address for <%s>: <%r> with mode %s', self, candidate[:-2], self.mode)
        return candidates
