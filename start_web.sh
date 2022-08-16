#!/bin/bash

# python -B ./server/www/teleport/app_bootstrap.py

#

pyexec=/usr/local/bin/python3
pipexec=/usr/local/bin/pip3

# ${pipexec} install --upgrade pip
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ tornado
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ mako
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ psutil
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ pymysql
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ qrcode
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ ldap3
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ pillow
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ wheezy.captcha
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ pyasn1
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ cryptography
# ${pipexec} --trusted-host mirrors.aliyun.com install -i http://mirrors.aliyun.com/pypi/simple/ cffi


${pyexec} -B ./server/www/teleport/app_bootstrap.py
