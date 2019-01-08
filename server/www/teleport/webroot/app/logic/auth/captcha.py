# -*- coding: utf-8 -*-

import io
import os
import random

from app.base.configs import tp_cfg
from wheezy.captcha.image import background
from wheezy.captcha.image import captcha
from wheezy.captcha.image import curve
from wheezy.captcha.image import noise
from wheezy.captcha.image import offset
from wheezy.captcha.image import rotate
from wheezy.captcha.image import smooth
from wheezy.captcha.image import text
from wheezy.captcha.image import warp


# _captcha_chars = 'AaCDdEeFfHJjKkLMmNnPpQRTtVvWwXxYy34679'
_captcha_chars = 'AaCDdEeFfHJKkLMmNnPpRTtVvWwXYy2379'


def _random_color_font():
    colors = ['#152cea', '#0b7700', '#5431d4', '#0e78ca']
    return random.choice(colors)


def _random_color_line():
    colors = ['#ce3714', '#de35bc']
    return random.choice(colors)


def tp_captcha_generate_image(h):
    if h >= 32:
        captcha_image_t = captcha(
            width=136,
            height=36,
            drawings=[
                background(color='#eeeeee'),
                curve(color='#bbbbbb', width=6, number=12),
                curve(color=_random_color_line, width=2, number=30),
                curve(color='#cccccc', width=7, number=13),
                curve(color='#dddddd', width=8, number=14),
                text(fonts=[
                    os.path.join(tp_cfg().res_path, 'fonts', '001.ttf')
                ],
                    font_sizes=(h-5, h-2, h, h+2),
                    color=_random_color_font,
                    squeeze_factor=1.05,
                    drawings=[
                        warp(dx_factor=0.03, dy_factor=0.03),
                        rotate(angle=20),
                        offset()
                    ]),
                smooth(),
            ])
    else:
        captcha_image_t = captcha(
            width=int(h*3)+8,
            height=h,
            drawings=[
                background(color='#eeeeee'),
                noise(number=40, color='#dddddd', level=3),
                smooth(),
                text(fonts=[
                    os.path.join(tp_cfg().res_path, 'fonts', '001.ttf')
                ],
                    font_sizes=(h-3, h-2, h-1, h),
                    color=_random_color_font,
                    squeeze_factor=0.95,
                    drawings=[
                        warp(dx_factor=0.03, dy_factor=0.03),
                        rotate(angle=15),
                        offset()
                    ]),
                smooth(),
            ])

    chars_t = random.sample(_captcha_chars, 4)
    image = captcha_image_t(chars_t)

    out = io.BytesIO()
    image.save(out, "jpeg", quality=80)
    return ''.join(chars_t), out.getvalue()


def tp_captcha_generate_image_v1(h):
    if h >= 32:
        captcha_image_t = captcha(
            width=136,
            height=36,
            drawings=[
                background(color='#eeeeee'),
                # curve(color='#4388d5', width=1, number=10),
                curve(color='#4388d5', width=1, number=10),
                curve(color='#af6fff', width=3, number=16),
                noise(number=80, color='#eeeeee', level=3),
                smooth(),
                text(fonts=[
                    os.path.join(tp_cfg().res_path, 'fonts', '001.ttf')
                ],
                    # font_sizes=(28, 34, 36, 32),
                    font_sizes=(h-4, h-2, h, h+1),
                    color='#63a8f5',
                    # squeeze_factor=1.2,
                    squeeze_factor=0.9,
                    drawings=[
                        # warp(dx_factor=0.05, dy_factor=0.05),
                        warp(dx_factor=0.03, dy_factor=0.03),
                        rotate(angle=20),
                        offset()
                    ]),
                curve(color='#af6fff', width=3, number=16),
                noise(number=20, color='#eeeeee', level=2),
                smooth(),
            ])
    else:
        captcha_image_t = captcha(
            width=int(h*3)+8,
            height=h,
            drawings=[
                background(color='#eeeeee'),
                # curve(color='#4388d5', width=1, number=10),
                curve(color='#4388d5', width=1, number=10),
                curve(color='#af6fff', width=3, number=16),
                noise(number=40, color='#eeeeee', level=2),
                smooth(),
                text(fonts=[
                    os.path.join(tp_cfg().res_path, 'fonts', '001.ttf')
                ],
                    # font_sizes=(28, 34, 36, 32),
                    font_sizes=(h-2, h-1, h, h+1),
                    color='#63a8f5',
                    # squeeze_factor=1.2,
                    squeeze_factor=0.9,
                    drawings=[
                        # warp(dx_factor=0.05, dy_factor=0.05),
                        warp(dx_factor=0.03, dy_factor=0.03),
                        rotate(angle=20),
                        offset()
                    ]),
                curve(color='#4388d5', width=1, number=8),
                noise(number=10, color='#eeeeee', level=1),
                # smooth(),
            ])

    chars_t = random.sample(_captcha_chars, 4)
    image = captcha_image_t(chars_t)

    out = io.BytesIO()
    image.save(out, "jpeg", quality=100)
    return ''.join(chars_t), out.getvalue()
