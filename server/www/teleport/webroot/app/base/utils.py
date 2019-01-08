# -*- coding: utf-8 -*-

import os
import stat
import time
import datetime
import hashlib
import threading
import random


class AttrDict(dict):
    """
    可以像属性一样访问字典的 Key，var.key 等同于 var['key']
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError("'dict' object has no attribute '{}'".format(name))
            # return None

    def __setattr__(self, name, val):
        self[name] = val

    def is_exists(self, name):
        try:
            self.__getattr__(name)
            return True
        except AttributeError:
            return False


def tp_convert_to_attr_dict(d):
    if type(d) is not dict:
        return None
    ret = AttrDict()
    for k in d:
        if type(d[k]) is dict:
            ret[k] = tp_convert_to_attr_dict(d[k])
        else:
            ret[k] = d[k]
    return ret


def tp_make_dir(path):
    """
    创建目录

    如果父目录不存在，则同时也创建之，目标是保证整个目录层次都存在，如果指定的目录已经存在，则视为成功（目的就是让这个目录存在）

    :param path: str
    :return: boolean
    """
    abs_path = os.path.abspath(path)

    if os.path.exists(abs_path):
        if os.path.isdir(abs_path):
            return True
        else:
            # log.e(u'An object named "%s" already exists. Can not create such directory.\n' % abs_path)
            return False

    base_name = os.path.basename(abs_path)
    parent_path = abs_path[:len(abs_path) - len(base_name)]
    if parent_path == path:
        return False

    if not os.path.exists(parent_path):
        # log.v('make_dir: %s\n' % parent_path)
        if not tp_make_dir(parent_path):
            return False
        os.mkdir(abs_path)
        # os.mkdir(abs_path, 0o777)
        os.chmod(abs_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
    else:
        if os.path.isdir(parent_path):
            os.mkdir(abs_path)
            # os.mkdir(abs_path, 0o777)
            os.chmod(abs_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        else:
            # log.e(u'An object named "%s" already exists. Can not create such directory.\n' % parent_path)
            return False

    return True


def tp_generate_random(n):
    """
    产生n字节的随机数，然后输出为16进制字符串

    :param n: int
    :return : str
    """
    ret = ''
    data = os.urandom(n)
    for i in data:
        ret += '%02X' % i
    return ret


def tp_bytes2human(n):
    """
    将字节数转换为易读的字符串

    http://code.activestate.com/recipes/578019
    bytes2human(10000)        '9.8K'
    bytes2human(100001221)    '95.4M'

    :type n: int
    :rtype : str
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n


def tp_second2human(n):
    """
    将经过的时间（秒）转换为易读的字符串

    :type n: int
    :rtype : str
    """
    _sec = n

    ret = ''
    d = int(_sec / 86400)  # 86400 = 24*60*60秒 一天
    if d > 0:
        ret = '%dd' % d

    _sec %= 86400
    h = int(_sec / 3600)  # 3600 = 60*60秒 一小时
    if h > 0:
        if len(ret) > 0:
            ret = '%s %dh' % (ret, h)
        else:
            ret = '%dh' % h

    _sec %= 3600
    m = int(_sec / 60)  # 3600 = 60*60秒 一小时
    if len(ret) > 0:
        ret = '%s %dm' % (ret, m)
    elif m > 0:
        ret = '%dm' % m

    _sec %= 60
    if len(ret) > 0:
        ret = '%s %ds' % (ret, _sec)
    else:
        ret = '%ds' % _sec

    return ret


def tp_timestamp_local_to_utc(t):
    return int(datetime.datetime.utcfromtimestamp(time.mktime(time.localtime(t))).timestamp())


def tp_timestamp_utc_now():
    return int(datetime.datetime.utcnow().timestamp())


def tp_utc_timestamp_ms():
    return int(datetime.datetime.utcnow().timestamp() * 1000)


def tp_bytes2string(b, encode='utf8'):
    for c in range(len(b)):
        if b[c] == 0:
            ret = b[0:c].decode(encode)
            return ret

    return b.decode(encode)


def tp_md5file(file_name):
    if not os.path.exists(file_name) or not os.path.isfile(file_name):
        raise ValueError

    f = open(file_name, 'rb')
    m = hashlib.md5()

    while 1:
        x = f.read(4096)
        m.update(x)
        if len(x) < 4096:
            break

    f.close()
    return m.hexdigest()


def tp_gen_password(length=8):
    random.seed()

    # 生成一个随机密码
    _chars = ['ABCDEFGHJKMNPQRSTWXYZ', 'abcdefhijkmnprstwxyz', '2345678']  # 默认去掉了容易混淆的字符oO,Ll,9gq,Vv,Uu,I1

    have_CHAR = False
    have_char = False
    have_num = False
    while True:
        ret = []
        for i in range(length):
            idx = random.randint(0, len(_chars) - 1)
            if idx == 0:
                have_CHAR = True
            elif idx == 1:
                have_char = True
            else:
                have_num = True
            ret.append(random.choice(_chars[idx]))

        if have_CHAR and have_char and have_num:
            break

    return ''.join(ret)


def tp_check_strong_password(p):
    s = 0
    if len(p) < 8:
        return False

    for i in range(len(p)):
        c = ord(p[i])
        if 48 <= c <= 57:  # 数字
            s |= 1
        elif 65 <= c <= 90:  # 大写字母
            s |= 2
        elif 97 <= c <= 122:  # 小写字母
            s |= 4
        else:
            s |= 8

    if (s & 1) and (s & 2) and (s & 4):
        return True
    else:
        return False


class UniqueId:
    def __init__(self):
        import builtins
        if '__tp_unique_id__' in builtins.__dict__:
            raise RuntimeError('UniqueId object exists, can not create more than one instance.')

        self._id = tp_timestamp_utc_now()
        self._locker = threading.RLock()

    def generate(self):
        with self._locker:
            self._id += 1
            return self._id


def tp_unique_id():
    import builtins
    if '__tp_unique_id__' not in builtins.__dict__:
        builtins.__dict__['__tp_unique_id__'] = UniqueId()
    return builtins.__dict__['__tp_unique_id__'].generate()
