# -*- coding: utf-8 -*-

import os
import io
import qrcode
import base64
import binascii
import hmac
import time
import hashlib
import struct

__all__ = ['tp_oath_generate_secret', 'tp_oath_verify_code', 'tp_oath_generate_qrcode']


def tp_oath_generate_secret():
    return _convert_secret_to_base32(binascii.b2a_hex(os.urandom(16))).replace('=', '')


def tp_oath_verify_code(secret, code):
    cur_input = int(time.time()) // 30
    window = 3
    for i in range(cur_input - (window - 1) // 2, cur_input + window // 2 + 1):  # [cur_input-(window-1)//2, cur_input + window//2]
        if _get_totp_token(secret, i) == code:
            return True
    return False


def tp_oath_generate_qrcode(username, secret):
    msg = 'otpauth://totp/{}?secret={}&issuer=teleport'.format(username, secret)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=4,
    )
    qr.add_data(msg)
    qr.make(fit=True)
    img = qr.make_image()

    out = io.BytesIO()
    img.save(out, "jpeg", quality=100)
    return out.getvalue()


def _convert_secret_to_base32(secret):
    return base64.b32encode(base64.b16decode(secret.upper())).decode()


def _get_totp_token(secret, factor=None):
    # 通过secret和运算因子（默认为当前时间戳模除30，也就是每30秒更新一次）计算6位数字

    # 需要对padding符进行处理
    _len = len(secret)
    _pad = 8 - (_len % 8)
    if _pad > 0:
        secret += '=' * _pad

    key = base64.b32decode(secret)
    if factor is None:
        factor = int(time.time()) // 30  # input 为次数, 30为默认密码刷新间隔值
    msg = struct.pack(">Q", factor)

    # 然后使用 HMAC-SHA1算法计算hash
    hsh = hmac.new(key, msg, hashlib.sha1).digest()

    # 将hsh转换成数字(默认为6位)
    i = hsh[-1] & 0xf  # 以最后一个字节的后4个bits为数字，作为接下来的索引
    f = hsh[i:i + 4]  # 以i为索引, 取hsh中的4个字节
    n = struct.unpack('>I', f)[0] & 0x7fffffff  # 将4个字节按big-endian转换为无符号整数, 转换时去掉最高位的符号位
    # 等价于 n = ((f[0] & 0x7f) << 24) | ((f[1] & 0xff) << 16) | ((f[2] & 0xff) << 8) | (f[3] & 0xff)

    # 将 n % 1000000 得到6位数字, 不足补零
    r = '%06d' % (n % 1000000)  # r 即为 生成的动态密码

    return r
