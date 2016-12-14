# Copyright 2012 Pinterest.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Charles Gordon"

import errno
import socket
import six

from pymemcache import pool

from pymemcache.exceptions import (
    MemcacheClientError,
    MemcacheUnknownCommandError,
    MemcacheIllegalInputError,
    MemcacheServerError,
    MemcacheUnknownError,
    MemcacheUnexpectedCloseError
)


RECV_SIZE = 4096
VALID_STORE_RESULTS = {
    b'set':     (b'STORED',),
    b'add':     (b'STORED', b'NOT_STORED'),
    b'replace': (b'STORED', b'NOT_STORED'),
    b'append':  (b'STORED', b'NOT_STORED'),
    b'prepend': (b'STORED', b'NOT_STORED'),
    b'cas':     (b'STORED', b'EXISTS', b'NOT_FOUND'),
}


# Some of the values returned by the "stats" command
# need mapping into native Python types
STAT_TYPES = {
    # General stats
    b'version': six.binary_type,
    b'rusage_user': lambda value: float(value.replace(b':', b'.')),
    b'rusage_system': lambda value: float(value.replace(b':', b'.')),
    b'hash_is_expanding': lambda value: int(value) != 0,
    b'slab_reassign_running': lambda value: int(value) != 0,

    # Settings stats
    b'inter': six.binary_type,
    b'evictions': lambda value: value == b'on',
    b'growth_factor': float,
    b'stat_key_prefix': six.binary_type,
    b'umask': lambda value: int(value, 8),
    b'detail_enabled': lambda value: int(value) != 0,
    b'cas_enabled': lambda value: int(value) != 0,
    b'auth_enabled_sasl': lambda value: value == b'yes',
    b'maxconns_fast': lambda value: int(value) != 0,
    b'slab_reassign': lambda value: int(value) != 0,
    b'slab_automove': lambda value: int(value) != 0,
}

# Common helper functions.


def _check_key(key, key_prefix=b''):
    """Checks key and add key_prefix."""
    if isinstance(key, six.text_type):
        try:
            key = key.encode('ascii')
        except UnicodeEncodeError:
            raise MemcacheIllegalInputError("No ascii key: %r" % (key,))
    key = key_prefix + key
    if b' ' in key:
        raise MemcacheIllegalInputError("Key contains spaces: %r" % (key,))
    if len(key) > 250:
        raise MemcacheIllegalInputError("Key is too long: %r" % (key,))
    return key


class Client(object):
    """
    A client for a single memcached server.

    *Keys and Values*

     Keys must have a __str__() method which should return a str with no more
     than 250 ASCII characters and no whitespace or control characters. Unicode
     strings must be encoded (as UTF-8, for example) unless they consist only
     of ASCII characters that are neither whitespace nor control characters.

     Values must have a __str__() method to convert themselves to a byte
     string. Unicode objects can be a problem since str() on a Unicode object
     will attempt to encode it as ASCII (which will fail if the value contains
     code points larger than U+127). You can fix this with a serializer or by
     just calling encode on the string (using UTF-8, for instance).

     If you intend to use anything but str as a value, it is a good idea to use
     a serializer and deserializer. The pymemcache.serde library has some
     already implemented serializers, including one that is compatible with
     the python-memcache library.

    *Serialization and Deserialization*

     The constructor takes two optional functions, one for "serialization" of
     values, and one for "deserialization". The serialization function takes
     two arguments, a key and a value, and returns a tuple of two elements, the
     serialized value, and an integer in the range 0-65535 (the "flags"). The
     deserialization function takes three parameters, a key, value and flags
     and returns the deserialized value.

     Here is an example using JSON for non-str values:

     .. code-block:: python

         def serialize_json(key, value):
             if type(value) == str:
                 return value, 1
             return json.dumps(value), 2

         def deserialize_json(key, value, flags):
             if flags == 1:
                 return value

             if flags == 2:
                 return json.loads(value)

             raise Exception("Unknown flags for value: {1}".format(flags))

    *Error Handling*

     All of the methods in this class that talk to memcached can throw one of
     the following exceptions:

      * MemcacheUnknownCommandError
      * MemcacheClientError
      * MemcacheServerError
      * MemcacheUnknownError
      * MemcacheUnexpectedCloseError
      * MemcacheIllegalInputError
      * socket.timeout
      * socket.error

     Instances of this class maintain a persistent connection to memcached
     which is terminated when any of these exceptions are raised. The next
     call to a method on the object will result in a new connection being made
     to memcached.
    """

    def __init__(self,
                 server,
                 serializer=None,
                 deserializer=None,
                 connect_timeout=None,
                 timeout=None,
                 no_delay=False,
                 ignore_exc=False,
                 socket_module=socket,
                 key_prefix=b'',
                 default_noreply=True):
        """
        Constructor.

        Args:
          server: tuple(hostname, port)
          serializer: optional function, see notes in the class docs.
          deserializer: optional function, see notes in the class docs.
          connect_timeout: optional float, seconds to wait for a connection to
            the memcached server. Defaults to "forever" (uses the underlying
            default socket timeout, which can be very long).
          timeout: optional float, seconds to wait for send or recv calls on
            the socket connected to memcached. Defaults to "forever" (uses the
            underlying default socket timeout, which can be very long).
          no_delay: optional bool, set the TCP_NODELAY flag, which may help
            with performance in some cases. Defaults to False.
          ignore_exc: optional bool, True to cause the "get", "gets",
            "get_many" and "gets_many" calls to treat any errors as cache
            misses. Defaults to False.
          socket_module: socket module to use, e.g. gevent.socket. Defaults to
            the standard library's socket module.
          key_prefix: Prefix of key. You can use this as namespace. Defaults
            to b''.
          default_noreply: bool, the default value for 'noreply' as passed to
            store commands (except from cas, incr, and decr, which default to
            False).

        Notes:
          The constructor does not make a connection to memcached. The first
          call to a method on the object will do that.
        """
        self.server = server
        self.serializer = serializer
        self.deserializer = deserializer
        self.connect_timeout = connect_timeout
        self.timeout = timeout
        self.no_delay = no_delay
        self.ignore_exc = ignore_exc
        self.socket_module = socket_module
        self.sock = None
        if isinstance(key_prefix, six.text_type):
            key_prefix = key_prefix.encode('ascii')
        if not isinstance(key_prefix, bytes):
            raise TypeError("key_prefix should be bytes.")
        self.key_prefix = key_prefix
        self.default_noreply = default_noreply

    def check_key(self, key):
        """Checks key and add key_prefix."""
        return _check_key(key, key_prefix=self.key_prefix)

    def _connect(self):
        sock = self.socket_module.socket(self.socket_module.AF_INET,
                                         self.socket_module.SOCK_STREAM)
        sock.settimeout(self.connect_timeout)
        sock.connect(self.server)
        sock.settimeout(self.timeout)
        if self.no_delay:
            sock.setsockopt(self.socket_module.IPPROTO_TCP,
                            self.socket_module.TCP_NODELAY, 1)
        self.sock = sock

    def close(self):
        """Close the connection to memcached, if it is open. The next call to a
        method that requires a connection will re-open it."""
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = None

    def set(self, key, value, expire=0, noreply=None):
        """
        The memcached "set" command.

        Args:
          key: str, see class docs for details.
          value: str, see class docs for details.
          expire: optional int, number of seconds until the item is expired
                  from the cache, or zero for no expiry (the default).
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          If no exception is raised, always returns True. If an exception is
          raised, the set may or may not have occurred. If noreply is True,
          then a successful return does not guarantee a successful set.
        """
        if noreply is None:
            noreply = self.default_noreply
        return self._store_cmd(b'set', key, expire, noreply, value)

    def set_many(self, values, expire=0, noreply=None):
        """
        A convenience function for setting multiple values.

        Args:
          values: dict(str, str), a dict of keys and values, see class docs
                  for details.
          expire: optional int, number of seconds until the item is expired
                  from the cache, or zero for no expiry (the default).
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          If no exception is raised, always returns True. Otherwise all, some
          or none of the keys have been successfully set. If noreply is True
          then a successful return does not guarantee that any keys were
          successfully set (just that the keys were successfully sent).
        """

        # TODO: make this more performant by sending all the values first, then
        # waiting for all the responses.
        for key, value in six.iteritems(values):
            self.set(key, value, expire, noreply)
        return True

    set_multi = set_many

    def add(self, key, value, expire=0, noreply=None):
        """
        The memcached "add" command.

        Args:
          key: str, see class docs for details.
          value: str, see class docs for details.
          expire: optional int, number of seconds until the item is expired
                  from the cache, or zero for no expiry (the default).
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          If noreply is True, the return value is always True. Otherwise the
          return value is True if the value was stgored, and False if it was
          not (because the key already existed).
        """
        if noreply is None:
            noreply = self.default_noreply
        return self._store_cmd(b'add', key, expire, noreply, value)

    def replace(self, key, value, expire=0, noreply=None):
        """
        The memcached "replace" command.

        Args:
          key: str, see class docs for details.
          value: str, see class docs for details.
          expire: optional int, number of seconds until the item is expired
                  from the cache, or zero for no expiry (the default).
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          If noreply is True, always returns True. Otherwise returns True if
          the value was stored and False if it wasn't (because the key didn't
          already exist).
        """
        if noreply is None:
            noreply = self.default_noreply
        return self._store_cmd(b'replace', key, expire, noreply, value)

    def append(self, key, value, expire=0, noreply=None):
        """
        The memcached "append" command.

        Args:
          key: str, see class docs for details.
          value: str, see class docs for details.
          expire: optional int, number of seconds until the item is expired
                  from the cache, or zero for no expiry (the default).
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          True.
        """
        if noreply is None:
            noreply = self.default_noreply
        return self._store_cmd(b'append', key, expire, noreply, value)

    def prepend(self, key, value, expire=0, noreply=None):
        """
        The memcached "prepend" command.

        Args:
          key: str, see class docs for details.
          value: str, see class docs for details.
          expire: optional int, number of seconds until the item is expired
                  from the cache, or zero for no expiry (the default).
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          True.
        """
        if noreply is None:
            noreply = self.default_noreply
        return self._store_cmd(b'prepend', key, expire, noreply, value)

    def cas(self, key, value, cas, expire=0, noreply=False):
        """
        The memcached "cas" command.

        Args:
          key: str, see class docs for details.
          value: str, see class docs for details.
          cas: int or str that only contains the characters '0'-'9'.
          expire: optional int, number of seconds until the item is expired
                  from the cache, or zero for no expiry (the default).
          noreply: optional bool, False to wait for the reply (the default).

        Returns:
          If noreply is True, always returns True. Otherwise returns None if
          the key didn't exist, False if it existed but had a different cas
          value and True if it existed and was changed.
        """
        return self._store_cmd(b'cas', key, expire, noreply, value, cas)

    def get(self, key):
        """
        The memcached "get" command, but only for one key, as a convenience.

        Args:
          key: str, see class docs for details.

        Returns:
          The value for the key, or None if the key wasn't found.
        """
        return self._fetch_cmd(b'get', [key], False).get(key, None)

    def get_many(self, keys):
        """
        The memcached "get" command.

        Args:
          keys: list(str), see class docs for details.

        Returns:
          A dict in which the keys are elements of the "keys" argument list
          and the values are values from the cache. The dict may contain all,
          some or none of the given keys.
        """
        if not keys:
            return {}

        return self._fetch_cmd(b'get', keys, False)

    get_multi = get_many

    def gets(self, key):
        """
        The memcached "gets" command for one key, as a convenience.

        Args:
          key: str, see class docs for details.

        Returns:
          A tuple of (key, cas), or (None, None) if the key was not found.
        """
        return self._fetch_cmd(b'gets', [key], True).get(key, (None, None))

    def gets_many(self, keys):
        """
        The memcached "gets" command.

        Args:
          keys: list(str), see class docs for details.

        Returns:
          A dict in which the keys are elements of the "keys" argument list and
          the values are tuples of (value, cas) from the cache. The dict may
          contain all, some or none of the given keys.
        """
        if not keys:
            return {}

        return self._fetch_cmd(b'gets', keys, True)

    def delete(self, key, noreply=None):
        """
        The memcached "delete" command.

        Args:
          key: str, see class docs for details.
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          If noreply is True, always returns True. Otherwise returns True if
          the key was deleted, and False if it wasn't found.
        """
        if noreply is None:
            noreply = self.default_noreply
        cmd = b'delete ' + self.check_key(key)
        if noreply:
            cmd += b' noreply'
        cmd += b'\r\n'
        result = self._misc_cmd(cmd, b'delete', noreply)
        if noreply:
            return True
        return result == b'DELETED'

    def delete_many(self, keys, noreply=None):
        """
        A convenience function to delete multiple keys.

        Args:
          keys: list(str), the list of keys to delete.
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          True. If an exception is raised then all, some or none of the keys
          may have been deleted. Otherwise all the keys have been sent to
          memcache for deletion and if noreply is False, they have been
          acknowledged by memcache.
        """
        if not keys:
            return True

        if noreply is None:
            noreply = self.default_noreply

        # TODO: make this more performant by sending all keys first, then
        # waiting for all values.
        for key in keys:
            self.delete(key, noreply)

        return True

    delete_multi = delete_many

    def incr(self, key, value, noreply=False):
        """
        The memcached "incr" command.

        Args:
          key: str, see class docs for details.
          value: int, the amount by which to increment the value.
          noreply: optional bool, False to wait for the reply (the default).

        Returns:
          If noreply is True, always returns None. Otherwise returns the new
          value of the key, or None if the key wasn't found.
        """
        key = self.check_key(key)
        cmd = b'incr ' + key + b' ' + six.text_type(value).encode('ascii')
        if noreply:
            cmd += b' noreply'
        cmd += b'\r\n'
        result = self._misc_cmd(cmd, b'incr', noreply)
        if noreply:
            return None
        if result == b'NOT_FOUND':
            return None
        return int(result)

    def decr(self, key, value, noreply=False):
        """
        The memcached "decr" command.

        Args:
          key: str, see class docs for details.
          value: int, the amount by which to increment the value.
          noreply: optional bool, False to wait for the reply (the default).

        Returns:
          If noreply is True, always returns None. Otherwise returns the new
          value of the key, or None if the key wasn't found.
        """
        key = self.check_key(key)
        cmd = b'decr ' + key + b' ' + six.text_type(value).encode('ascii')
        if noreply:
            cmd += b' noreply'
        cmd += b'\r\n'
        result = self._misc_cmd(cmd, b'decr', noreply)
        if noreply:
            return None
        if result == b'NOT_FOUND':
            return None
        return int(result)

    def touch(self, key, expire=0, noreply=None):
        """
        The memcached "touch" command.

        Args:
          key: str, see class docs for details.
          expire: optional int, number of seconds until the item is expired
                  from the cache, or zero for no expiry (the default).
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          True if the expiration time was updated, False if the key wasn't
          found.
        """
        if noreply is None:
            noreply = self.default_noreply
        key = self.check_key(key)
        cmd = b'touch ' + key + b' ' + six.text_type(expire).encode('ascii')
        if noreply:
            cmd += b' noreply'
        cmd += b'\r\n'
        result = self._misc_cmd(cmd, b'touch', noreply)
        if noreply:
            return True
        return result == b'TOUCHED'

    def stats(self, *args):
        """
        The memcached "stats" command.

        The returned keys depend on what the "stats" command returns.
        A best effort is made to convert values to appropriate Python
        types, defaulting to strings when a conversion cannot be made.

        Args:
          *arg: extra string arguments to the "stats" command. See the
                memcached protocol documentation for more information.

        Returns:
          A dict of the returned stats.
        """
        result = self._fetch_cmd(b'stats', args, False)

        for key, value in six.iteritems(result):
            converter = STAT_TYPES.get(key, int)
            try:
                result[key] = converter(value)
            except Exception:
                pass

        return result

    def version(self):
        """
        The memcached "version" command.

        Returns:
            A string of the memcached version.
        """
        cmd = b"version\r\n"
        result = self._misc_cmd(cmd, b'version', False)

        if not result.startswith(b'VERSION '):
            raise MemcacheUnknownError("Received unexpected response: %s" % (result, ))

        return result[8:]

    def flush_all(self, delay=0, noreply=None):
        """
        The memcached "flush_all" command.

        Args:
          delay: optional int, the number of seconds to wait before flushing,
                 or zero to flush immediately (the default).
          noreply: optional bool, True to not wait for the reply (defaults to
                   self.default_noreply).

        Returns:
          True.
        """
        if noreply is None:
            noreply = self.default_noreply
        cmd = b'flush_all ' + six.text_type(delay).encode('ascii')
        if noreply:
            cmd += b' noreply'
        cmd += b'\r\n'
        result = self._misc_cmd(cmd, b'flush_all', noreply)
        if noreply:
            return True
        return result == b'OK'

    def quit(self):
        """
        The memcached "quit" command.

        This will close the connection with memcached. Calling any other
        method on this object will re-open the connection, so this object can
        be re-used after quit.
        """
        cmd = b"quit\r\n"
        self._misc_cmd(cmd, b'quit', True)
        self.close()

    def _raise_errors(self, line, name):
        if line.startswith(b'ERROR'):
            raise MemcacheUnknownCommandError(name)

        if line.startswith(b'CLIENT_ERROR'):
            error = line[line.find(b' ') + 1:]
            raise MemcacheClientError(error)

        if line.startswith(b'SERVER_ERROR'):
            error = line[line.find(b' ') + 1:]
            raise MemcacheServerError(error)

    def _fetch_cmd(self, name, keys, expect_cas):
        checked_keys = dict((self.check_key(k), k) for k in keys)
        cmd = name + b' ' + b' '.join(checked_keys) + b'\r\n'

        try:
            if not self.sock:
                self._connect()

            self.sock.sendall(cmd)

            buf = b''
            result = {}
            while True:
                buf, line = _readline(self.sock, buf)
                self._raise_errors(line, name)
                if line == b'END':
                    return result
                elif line.startswith(b'VALUE'):
                    if expect_cas:
                        _, key, flags, size, cas = line.split()
                    else:
                        try:
                            _, key, flags, size = line.split()
                        except Exception as e:
                            raise ValueError("Unable to parse line %s: %s"
                                             % (line, str(e)))

                    buf, value = _readvalue(self.sock, buf, int(size))
                    key = checked_keys[key]

                    if self.deserializer:
                        value = self.deserializer(key, value, int(flags))

                    if expect_cas:
                        result[key] = (value, cas)
                    else:
                        result[key] = value
                elif name == b'stats' and line.startswith(b'STAT'):
                    _, key, value = line.split()
                    result[key] = value
                else:
                    raise MemcacheUnknownError(line[:32])
        except Exception:
            self.close()
            if self.ignore_exc:
                return {}
            raise

    def _store_cmd(self, name, key, expire, noreply, data, cas=None):
        key = self.check_key(key)
        if not self.sock:
            self._connect()

        if self.serializer:
            data, flags = self.serializer(key, data)
        else:
            flags = 0

        if not isinstance(data, six.binary_type):
            try:
                data = six.text_type(data).encode('ascii')
            except UnicodeEncodeError as e:
                raise MemcacheIllegalInputError(str(e))

        extra = b''
        if cas is not None:
            extra += b' ' + cas
        if noreply:
            extra += b' noreply'

        cmd = (name + b' ' + key + b' ' + six.text_type(flags).encode('ascii')
               + b' ' + six.text_type(expire).encode('ascii')
               + b' ' + six.text_type(len(data)).encode('ascii') + extra
               + b'\r\n' + data + b'\r\n')

        try:
            self.sock.sendall(cmd)

            if noreply:
                return True

            buf = b''
            buf, line = _readline(self.sock, buf)
            self._raise_errors(line, name)

            if line in VALID_STORE_RESULTS[name]:
                if line == b'STORED':
                    return True
                if line == b'NOT_STORED':
                    return False
                if line == b'NOT_FOUND':
                    return None
                if line == b'EXISTS':
                    return False
            else:
                raise MemcacheUnknownError(line[:32])
        except Exception:
            self.close()
            raise

    def _misc_cmd(self, cmd, cmd_name, noreply):
        if not self.sock:
            self._connect()

        try:
            self.sock.sendall(cmd)

            if noreply:
                return

            _, line = _readline(self.sock, b'')
            self._raise_errors(line, cmd_name)

            return line
        except Exception:
            self.close()
            raise

    def __setitem__(self, key, value):
        self.set(key, value, noreply=True)

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError
        return value

    def __delitem__(self, key):
        self.delete(key, noreply=True)


class PooledClient(object):
    """A thread-safe pool of clients (with the same client api).

    Args:
      max_pool_size: maximum pool size to use (going about this amount
                     triggers a runtime error), by default this is 2147483648L
                     when not provided (or none).
      lock_generator: a callback/type that takes no arguments that will
                      be called to create a lock or sempahore that can
                      protect the pool from concurrent access (for example a
                      eventlet lock or semaphore could be used instead)

    Further arguments are interpreted as for :py:class:`.Client` constructor.
    """

    def __init__(self,
                 server,
                 serializer=None,
                 deserializer=None,
                 connect_timeout=None,
                 timeout=None,
                 no_delay=False,
                 ignore_exc=False,
                 socket_module=socket,
                 key_prefix=b'',
                 max_pool_size=None,
                 lock_generator=None):
        self.server = server
        self.serializer = serializer
        self.deserializer = deserializer
        self.connect_timeout = connect_timeout
        self.timeout = timeout
        self.no_delay = no_delay
        self.ignore_exc = ignore_exc
        self.socket_module = socket_module
        if isinstance(key_prefix, six.text_type):
            key_prefix = key_prefix.encode('ascii')
        if not isinstance(key_prefix, bytes):
            raise TypeError("key_prefix should be bytes.")
        self.key_prefix = key_prefix
        self.client_pool = pool.ObjectPool(
            self._create_client,
            after_remove=lambda client: client.close(),
            max_size=max_pool_size,
            lock_generator=lock_generator)

    def check_key(self, key):
        """Checks key and add key_prefix."""
        return _check_key(key, key_prefix=self.key_prefix)

    def _create_client(self):
        client = Client(self.server,
                        serializer=self.serializer,
                        deserializer=self.deserializer,
                        connect_timeout=self.connect_timeout,
                        timeout=self.timeout,
                        no_delay=self.no_delay,
                        # We need to know when it fails *always* so that we
                        # can remove/destroy it from the pool...
                        ignore_exc=False,
                        socket_module=self.socket_module,
                        key_prefix=self.key_prefix)
        return client

    def close(self):
        self.client_pool.clear()

    def set(self, key, value, expire=0, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.set(key, value, expire=expire, noreply=noreply)

    def set_many(self, values, expire=0, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.set_many(values, expire=expire, noreply=noreply)

    set_multi = set_many

    def replace(self, key, value, expire=0, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.replace(key, value, expire=expire, noreply=noreply)

    def append(self, key, value, expire=0, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.append(key, value, expire=expire, noreply=noreply)

    def prepend(self, key, value, expire=0, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.prepend(key, value, expire=expire, noreply=noreply)

    def cas(self, key, value, cas, expire=0, noreply=False):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.cas(key, value, cas,
                              expire=expire, noreply=noreply)

    def get(self, key):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            try:
                return client.get(key)
            except Exception:
                if self.ignore_exc:
                    return None
                else:
                    raise

    def get_many(self, keys):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            try:
                return client.get_many(keys)
            except Exception:
                if self.ignore_exc:
                    return {}
                else:
                    raise

    get_multi = get_many

    def gets(self, key):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            try:
                return client.gets(key)
            except Exception:
                if self.ignore_exc:
                    return (None, None)
                else:
                    raise

    def gets_many(self, keys):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            try:
                return client.gets_many(keys)
            except Exception:
                if self.ignore_exc:
                    return {}
                else:
                    raise

    def delete(self, key, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.delete(key, noreply=noreply)

    def delete_many(self, keys, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.delete_many(keys, noreply=noreply)

    delete_multi = delete_many

    def add(self, key, value, expire=0, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.add(key, value, expire=expire, noreply=noreply)

    def incr(self, key, value, noreply=False):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.incr(key, value, noreply=noreply)

    def decr(self, key, value, noreply=False):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.decr(key, value, noreply=noreply)

    def touch(self, key, expire=0, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.touch(key, expire=expire, noreply=noreply)

    def stats(self, *args):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            try:
                return client.stats(*args)
            except Exception:
                if self.ignore_exc:
                    return {}
                else:
                    raise

    def version(self):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.version()

    def flush_all(self, delay=0, noreply=True):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            return client.flush_all(delay=delay, noreply=noreply)

    def quit(self):
        with self.client_pool.get_and_release(destroy_on_fail=True) as client:
            try:
                client.quit()
            finally:
                self.client_pool.destroy(client)

    def __setitem__(self, key, value):
        self.set(key, value, noreply=True)

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError
        return value

    def __delitem__(self, key):
        self.delete(key, noreply=True)


def _readline(sock, buf):
    """Read line of text from the socket.

    Read a line of text (delimited by "\r\n") from the socket, and
    return that line along with any trailing characters read from the
    socket.

    Args:
        sock: Socket object, should be connected.
        buf: String, zero or more characters, returned from an earlier
            call to _readline or _readvalue (pass an empty string on the
            first call).

    Returns:
      A tuple of (buf, line) where line is the full line read from the
      socket (minus the "\r\n" characters) and buf is any trailing
      characters read after the "\r\n" was found (which may be an empty
      string).

    """
    chunks = []
    last_char = b''

    while True:
        # We're reading in chunks, so "\r\n" could appear in one chunk,
        # or across the boundary of two chunks, so we check for both
        # cases.

        # This case must appear first, since the buffer could have
        # later \r\n characters in it and we want to get the first \r\n.
        if last_char == b'\r' and buf[0:1] == b'\n':
            # Strip the last character from the last chunk.
            chunks[-1] = chunks[-1][:-1]
            return buf[1:], b''.join(chunks)
        elif buf.find(b'\r\n') != -1:
            before, sep, after = buf.partition(b"\r\n")
            chunks.append(before)
            return after, b''.join(chunks)

        if buf:
            chunks.append(buf)
            last_char = buf[-1:]

        buf = _recv(sock, RECV_SIZE)
        if not buf:
            raise MemcacheUnexpectedCloseError()


def _readvalue(sock, buf, size):
    """Read specified amount of bytes from the socket.

    Read size bytes, followed by the "\r\n" characters, from the socket,
    and return those bytes and any trailing bytes read after the "\r\n".

    Args:
        sock: Socket object, should be connected.
        buf: String, zero or more characters, returned from an earlier
            call to _readline or _readvalue (pass an empty string on the
            first call).
        size: Integer, number of bytes to read from the socket.

    Returns:
      A tuple of (buf, value) where value is the bytes read from the
      socket (there will be exactly size bytes) and buf is trailing
      characters read after the "\r\n" following the bytes (but not
      including the \r\n).

    """
    chunks = []
    rlen = size + 2
    while rlen - len(buf) > 0:
        if buf:
            rlen -= len(buf)
            chunks.append(buf)
        buf = _recv(sock, RECV_SIZE)
        if not buf:
            raise MemcacheUnexpectedCloseError()

    # Now we need to remove the \r\n from the end. There are two cases we care
    # about: the \r\n is all in the last buffer, or only the \n is in the last
    # buffer, and we need to remove the \r from the penultimate buffer.

    if rlen == 1:
        # replace the last chunk with the same string minus the last character,
        # which is always '\r' in this case.
        chunks[-1] = chunks[-1][:-1]
    else:
        # Just remove the "\r\n" from the latest chunk
        chunks.append(buf[:rlen - 2])

    return buf[rlen:], b''.join(chunks)


def _recv(sock, size):
    """sock.recv() with retry on EINTR"""
    while True:
        try:
            return sock.recv(size)
        except IOError as e:
            if e.errno != errno.EINTR:
                raise
