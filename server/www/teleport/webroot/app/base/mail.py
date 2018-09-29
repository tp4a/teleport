# -*- coding: utf-8 -*-

import smtplib
import socket
import ssl
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr

import tornado.gen
from app.base.configs import tp_cfg
from app.base.logger import log
from app.const import *


def _sanitize_address(addr, encoding='utf-8'):
    name, addr = parseaddr(addr)

    name = Header(name, encoding).encode()
    addr.encode('ascii')
    return formataddr((name, addr))


def _sanitize_addresses(addresses, encoding='utf-8'):
    return [_sanitize_address(addr, encoding) for addr in addresses]


def _sanitize_subject(subject, encoding='utf-8'):
    try:
        subject.encode('ascii')
    except UnicodeEncodeError:
        try:
            subject = Header(subject, encoding).encode()
        except UnicodeEncodeError:
            subject = Header(subject, 'utf-8').encode()
    return subject


def _has_newline(line):
    """Used by has_bad_header to check for \\r or \\n"""
    if line and ('\r' in line or '\n' in line):
        return True
    return False


@tornado.gen.coroutine
def tp_send_mail(recipient, message, subject=None, sender=None, cc=None, bcc=None, server=None, port=None, use_ssl=None, username=None, password=None):
    """
    :type recipient: str | list[str]
    :type message: str
    :type subject: str | None
    :type sender: str | None
    :type cc: str | list[str] | None
    :type bcc: str | list[str] | None
    :type server: str | None
    :type port: int | None
    :type use_ssl: bool | None
    :type username: string | None
    :type password: string | None
    :rtype: dict
    """
    sys_smtp = tp_cfg().sys.smtp
    sys_smtp_password = tp_cfg().sys_smtp_password

    _subject = subject if subject is not None else '系统消息'
    _sender = sender if sender is not None else sys_smtp.sender
    _server = server if server is not None else sys_smtp.server
    _port = port if port is not None else sys_smtp.port
    if use_ssl is None:
        _ssl = True if sys_smtp.ssl else False
    else:
        _ssl = use_ssl
    _username = username if username is not None else sys_smtp.sender
    _password = password if password is not None else sys_smtp_password
    _recipients = recipient if type(recipient) == list else [recipient]

    _subject = '[TELEPORT] {}'.format(_subject)

    _smtp = None

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = _sanitize_subject(_subject)
        msg['From'] = _sender
        msg['To'] = ', '.join(_recipients)
        if cc is not None:
            _cc = cc if type(cc) == list else [cc]
            _recipients.extend(_cc)
            msg['Cc'] = ', '.join(_cc)
        if bcc is not None:
            _bcc = bcc if type(bcc) == list else [bcc]
            _recipients.extend(_bcc)
            msg['Bcc'] = ', '.join(_bcc)

        msg.attach(MIMEText(message, 'plain'))
        # msg.attach(MIMEText(html_string, 'html'))

        # 收件人去重
        _recipients = list(set(_recipients))

        dbg_mode, _ = tp_cfg().get_bool('common::debug-mode', False)

        if _ssl:
            _smtp = smtplib.SMTP_SSL(_server, _port, timeout=10.0)
            if dbg_mode:
                _smtp.set_debuglevel(1)
            _smtp.ehlo()
            if (_port == 25 or _port == 587) and _smtp.has_extn("starttls"):
                _smtp.starttls()
        else:
            _smtp = smtplib.SMTP(_server, _port, timeout=10.0)
            if dbg_mode:
                _smtp.set_debuglevel(1)
            _smtp.ehlo()
            if _smtp.has_extn("starttls"):
                try:
                    _smtp.starttls()
                except:
                    pass

        _smtp.login(_username, _password)

        _smtp.set_debuglevel(0)
        send_errors = _smtp.sendmail(
            _sanitize_address(_sender),
            _sanitize_addresses(_recipients),
            msg.as_string())

        if len(send_errors) != 0:
            log.e('not all mail send:\n')
            for i in send_errors:
                log.e('  {}, [{}]{}\n'.format(i, send_errors[i][0], send_errors[i][1]))
            return TPE_FAILED, '无法将邮件发送给部分收件人！'

        return TPE_OK, ''

    except (socket.timeout, socket.gaierror, ConnectionRefusedError, smtplib.SMTPServerDisconnected):
        return TPE_FAILED, '无法连接SMTP邮件服务器，请检查服务器地址、端口以及SSL设置！'

    except ssl.SSLError:
        return TPE_FAILED, '无法连接SMTP邮件服务器，请检查服务器端口及SSL设置是否匹配！'

    except smtplib.SMTPAuthenticationError:
        return TPE_FAILED, '无法验证发件人身份，请检查发件人邮箱和密码！'

    except smtplib.SMTPRecipientsRefused as e:
        # {'i.think.there.are.no.such.ussssser@qq.com': (550, b'Mailbox not found or access denied')}
        x = e.args[0]
        msg = ['发送邮件失败！']
        for i in x:
            msg.append('{}: [{}] {}'.format(i, x[i][0], x[i][1].decode()))
        return TPE_FAILED, '<br/>'.join(msg)

    except smtplib.SMTPException as e:
        return TPE_FAILED, '无法发送邮件：{}'.format(e.__str__())

    except Exception:
        log.e('send mail failed.\n')
        return TPE_FAILED, '无法发送邮件！'

    # finally:
    #     if _smtp is not None:
    #         _smtp.quit()
