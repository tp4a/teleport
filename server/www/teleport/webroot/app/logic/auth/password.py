# -*- coding: utf-8 -*-

import random
import hashlib


_hex_chars = '0123456789abcdef'


def tp_password_generate_secret(password):
    """
    根据设置的password，计算一个加盐的散列，用于保存到数据库
    @param password: string
    @return: string
    """

    _hash_type = '3'  # 1 = md5, 2 = sha1, 3 = sha256

    _salt_data = list()
    for i in range(16):
        _salt_data.append(random.choice(_hex_chars))
    _salt = ''.join(_salt_data)

    h = hashlib.sha256()
    h.update(_hash_type.encode())
    h.update(_salt.encode())
    h.update(password.encode())
    _val = h.hexdigest()

    ret = '{}:{}:{}'.format(_hash_type, _salt, _val)

    return ret


def tp_password_verify(password, sec_password):
    _sec = sec_password.split(':')
    if len(_sec) != 3:
        return False

    if _sec[0] == '1':
        h = hashlib.md5()
    elif _sec[0] == '2':
        h = hashlib.sha1()
    elif _sec[0] == '3':
        h = hashlib.sha256()
    else:
        return False

    h.update(_sec[0].encode())
    h.update(_sec[1].encode())
    h.update(password.encode())
    _val = h.hexdigest()

    return _val == _sec[2]
