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

import logging
import pickle

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


FLAG_PICKLE = 1 << 0
FLAG_INTEGER = 1 << 1
FLAG_LONG = 1 << 2


def python_memcache_serializer(key, value):
    flags = 0

    if isinstance(value, str):
        pass
    elif isinstance(value, int):
        flags |= FLAG_INTEGER
        value = "%d" % value
    elif isinstance(value, long):
        flags |= FLAG_LONG
        value = "%d" % value
    else:
        flags |= FLAG_PICKLE
        output = StringIO()
        pickler = pickle.Pickler(output, 0)
        pickler.dump(value)
        value = output.getvalue()

    return value, flags


def python_memcache_deserializer(key, value, flags):
    if flags == 0:
        return value

    if flags & FLAG_INTEGER:
        return int(value)

    if flags & FLAG_LONG:
        return long(value)

    if flags & FLAG_PICKLE:
        try:
            buf = StringIO(value)
            unpickler = pickle.Unpickler(buf)
            return unpickler.load()
        except Exception:
            logging.info('Pickle error', exc_info=True)
            return None

    return value
