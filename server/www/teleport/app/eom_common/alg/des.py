# -*- coding: utf-8 -*-

"""DES"""

import os
from ctypes import *

use_alg = True

try:
    # Try to locate the .so file in the same directory as this file
    _file = 'alg.dll'
    _path = os.path.join(*(os.path.split(__file__)[:-1] + (_file,)))
    _mod = cdll.LoadLibrary(_path)

    _des3_cbc_encrypt = _mod.des3_cbc_encrypt
    _des3_cbc_encrypt.argtypes = (c_void_p, c_int, c_void_p, c_int, c_void_p)
    _des3_cbc_encrypt.restype = c_int

    _des3_cbc_decrypt = _mod.des3_cbc_decrypt
    _des3_cbc_decrypt.argtypes = (c_void_p, c_int, c_void_p, c_int, c_void_p)
    _des3_cbc_decrypt.restype = c_int

    _free_buffer = _mod.free_buffer
    _free_buffer.argtypes = (c_void_p,)

except OSError as e:
    use_alg = False
    from eom_common.eomcore.algorithm import pyDes
    # raise RuntimeError('kx')
    # print('xxxxxxxxxx')
    # pass


def print_bin(data):
    for i in range(len(data)):
        print('%02X ' % data[i], end='')
        if (i + 1) % 16 == 0:
            print('')
    print('')


def des3_cbc_encrypt(key, plain_data):
    if use_alg:

        out = POINTER(c_ubyte)()
        out_len = _des3_cbc_encrypt(key, len(key), plain_data, len(plain_data), byref(out))
        if out_len < 0:
            return None

        ret = bytes(cast(out, POINTER(c_ubyte * out_len)).contents)
        _free_buffer(out)

        return ret
    else:
        try:
            return pyDes.triple_des(key, pyDes.CBC, b'\x00'*8).encrypt(plain_data, None, pyDes.PAD_PKCS5)
        except Exception:
            return None


def des3_cbc_decrypt(key, enc_data):
    if use_alg:

        out = POINTER(c_ubyte)()
        out_len = _des3_cbc_decrypt(key, len(key), enc_data, len(enc_data), byref(out))
        if out_len < 0:
            return None

        ret = bytes(cast(out, POINTER(c_ubyte * out_len)).contents)
        _free_buffer(out)

        return ret
    else:
        try:
            return pyDes.triple_des(key, pyDes.CBC, b'\x00'*8).decrypt(enc_data, None, pyDes.PAD_PKCS5)
        except Exception:
            return None


if __name__ == '__main__':
    key = b'\x00' * 24
    plain_data = os.urandom(110)
    print_bin(plain_data)

    try:
        enc = des3_cbc_encrypt(key, plain_data)
        print('==========================')
        print_bin(enc)
        print('==========================')
        dec = des3_cbc_decrypt(key, enc)
        print('==========================')
        print_bin(dec)
        print('==========================')
    except Exception:
        print('error')
        raise
