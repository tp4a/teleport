"""
"""

# Created on 2015.04.08
#
# Author: Giovanni Cannata
#
# Copyright 2015 - 2020 Giovanni Cannata
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

# original code by Hugh Cole-Baker, modified by Peter Foley
# it needs the gssapi package
import socket

from ...core.exceptions import LDAPPackageUnavailableError, LDAPCommunicationError

try:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import gssapi
except ImportError:
    raise LDAPPackageUnavailableError('package gssapi missing')

from .sasl import send_sasl_negotiation, abort_sasl_negotiation

NO_SECURITY_LAYER = 1
INTEGRITY_PROTECTION = 2
CONFIDENTIALITY_PROTECTION = 4


def sasl_gssapi(connection, controls):
    """
    Performs a bind using the Kerberos v5 ("GSSAPI") SASL mechanism
    from RFC 4752. Does not support any security layers, only authentication!

    sasl_credentials can be empty or a tuple with one or two elements.
    The first element determines which service principal to request a ticket for and can be one of the following:
    
    - None or False, to use the hostname from the Server object
    - True to perform a reverse DNS lookup to retrieve the canonical hostname for the hosts IP address
    - A string containing the hostname
    
    The optional second element is what authorization ID to request.
    
    - If omitted or None, the authentication ID is used as the authorization ID
    - If a string, the authorization ID to use. Should start with "dn:" or "user:".

    The optional third element is a raw gssapi credentials structure which can be used over
    the implicit use of a krb ccache.
    """
    target_name = None
    authz_id = b""
    raw_creds = None
    creds = None
    if connection.sasl_credentials:
        if len(connection.sasl_credentials) >= 1 and connection.sasl_credentials[0]:
            if connection.sasl_credentials[0] is True:
                hostname = socket.gethostbyaddr(connection.socket.getpeername()[0])[0]
                target_name = gssapi.Name('ldap@' + hostname, gssapi.NameType.hostbased_service)
            else:
                target_name = gssapi.Name('ldap@' + connection.sasl_credentials[0], gssapi.NameType.hostbased_service)
        if len(connection.sasl_credentials) >= 2 and connection.sasl_credentials[1]:
            authz_id = connection.sasl_credentials[1].encode("utf-8")
        if len(connection.sasl_credentials) >= 3 and connection.sasl_credentials[2]:
            raw_creds = connection.sasl_credentials[2]
    if target_name is None:
        target_name = gssapi.Name('ldap@' + connection.server.host, gssapi.NameType.hostbased_service)

    if raw_creds is not None:
        creds = gssapi.Credentials(base=raw_creds, usage='initiate', store=connection.cred_store)
    else:
        creds = gssapi.Credentials(name=gssapi.Name(connection.user), usage='initiate', store=connection.cred_store) if connection.user else None
    ctx = gssapi.SecurityContext(name=target_name, mech=gssapi.MechType.kerberos, creds=creds)
    in_token = None
    try:
        while True:
            out_token = ctx.step(in_token)
            if out_token is None:
                out_token = ''
            result = send_sasl_negotiation(connection, controls, out_token)
            in_token = result['saslCreds']
            try:
                # This raised an exception in gssapi<1.1.2 if the context was
                # incomplete, but was fixed in
                # https://github.com/pythongssapi/python-gssapi/pull/70
                if ctx.complete:
                    break
            except gssapi.exceptions.MissingContextError:
                pass

        unwrapped_token = ctx.unwrap(in_token)
        if len(unwrapped_token.message) != 4:
            raise LDAPCommunicationError("Incorrect response from server")

        server_security_layers = unwrapped_token.message[0]
        if not isinstance(server_security_layers, int):
            server_security_layers = ord(server_security_layers)
        if server_security_layers in (0, NO_SECURITY_LAYER):
            if unwrapped_token.message[1:] != '\x00\x00\x00':
                raise LDAPCommunicationError("Server max buffer size must be 0 if no security layer")
        if not (server_security_layers & NO_SECURITY_LAYER):
            raise LDAPCommunicationError("Server requires a security layer, but this is not implemented")

        client_security_layers = bytearray([NO_SECURITY_LAYER, 0, 0, 0])
        out_token = ctx.wrap(bytes(client_security_layers)+authz_id, False)
        return send_sasl_negotiation(connection, controls, out_token.message)
    except (gssapi.exceptions.GSSError, LDAPCommunicationError):
        abort_sasl_negotiation(connection, controls)
        raise
