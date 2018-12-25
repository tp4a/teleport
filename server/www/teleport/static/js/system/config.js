"use strict";

$app.on_init = function (cb_stack) {
    //console.log($app.options);

    $app.dlg_result = $app.create_dlg_result();
    // cb_stack.add($app.dlg_result.init);

    $app.info = $app.create_info_table();
    cb_stack.add($app.info.init);
    
    $app.global = $app.create_config_global();
    cb_stack.add($app.global.init);

    $app.sess = $app.create_config_sess();
    cb_stack.add($app.sess.init);

    $app.smtp = $app.create_config_smtp();
    cb_stack.add($app.smtp.init);

    $app.sec = $app.create_config_sec();
    cb_stack.add($app.sec.init);

    $app.storage = $app.create_config_storage();
    cb_stack.add($app.storage.init);

    cb_stack.exec();
};

$app.create_info_table = function () {
    var _info = {};

    _info.dom = {
        web_info: $('#web-info-kv'),
        core_info: $('#core-info-kv')
    };

    _info.init = function (cb_stack) {
        var h = [];

        h.push(_info._make_info('WEB服务版本', $app.options.web_cfg.version));

        if ($app.options.web_cfg.db.type === DB_TYPE_SQLITE) {
            h.push(_info._make_info('数据库类型', 'SQLite'));
            h.push(_info._make_info('数据库文件', $app.options.web_cfg.db.sqlite_file));
        } else if ($app.options.web_cfg.db.type === DB_TYPE_MYSQL) {
            h.push(_info._make_info('数据库类型', 'MySQL'));
            h.push(_info._make_info('mysql-host', $app.options.web_cfg.db.mysql_host));
            h.push(_info._make_info('mysql-port', $app.options.web_cfg.db.mysql_port));
            h.push(_info._make_info('mysql-db', $app.options.web_cfg.db.mysql_db));
            h.push(_info._make_info('mysql-user', $app.options.web_cfg.db.mysql_user));
        } else {
            h.push(_info._make_info('数据库类型', '未知'));
        }

        h.push(_info._make_info('与核心服务通讯地址', $app.options.web_cfg.core_server_rpc));

        _info.dom.web_info.append(h.join(''));

        h = [];
        if (!$app.options.core_cfg.detected) {
            h.push(_info._make_info('核心服务信息', '<span class="error">无法获取，未能连接到核心服务</span>'));
        } else {
            h.push(_info._make_info('核心服务版本', $app.options.core_cfg.version));
            h.push(_info._make_info('与WEB服务通讯地址', $app.options.core_cfg.web_server_rpc));
            h.push(_info._make_protocol_info('RDP 端口', $app.options.core_cfg.rdp));
            h.push(_info._make_protocol_info('SSH 端口', $app.options.core_cfg.ssh));
            h.push(_info._make_protocol_info('TELNET 端口', $app.options.core_cfg.telnet));
            h.push(_info._make_info('录像文件路径', $app.options.core_cfg.replay_path));
        }

        _info.dom.core_info.append(h.join(''));

        cb_stack.exec();
    };

    _info._make_info = function (k, v) {
        if (_.isUndefined(v))
            v = '<span class="error">未能检测到</span>';
        return '<tr><td class="key">' + k + '：</td><td class="value">' + v + '</td></tr>';
    };
    _info._make_protocol_info = function (name, p) {
        if (_.isUndefined(p))
            return _info._make_info(name, '未能检测到');
        var val = p.port;
        if (!p.enable) {
            val = '<span class="disabled">' + val + '（未启用）</span>';
        }

        return _info._make_info(name, val);
    };

    return _info;
};

$app.create_config_global = function () {
    var _global = {};

    _global.dom = {
        btn_save: $('#btn-save-global-config'),

        btn_global_use_url_protocol: $('#global-use-url-protocol')
    };

    _global.init = function (cb_stack) {
        _global.update_dom_global_cfg($app.options.sys_cfg.glob);

        $('#tab-global').find('.tp-checkbox.tp-editable').click(function () {
            if ($(this).hasClass('tp-selected'))
                $(this).removeClass('tp-selected');
            else
                $(this).addClass('tp-selected');
        });

        _global.dom.btn_save.click(function () {
            _global.on_btn_save();
        });

        cb_stack.exec();
    };

    _global.update_dom_global_cfg = function (global) {
        _global.dom.btn_global_use_url_protocol.removeClass('tp-selected');
        if (global.url_proto)
            _global.dom.btn_global_use_url_protocol.addClass('tp-selected');

     };

    _global.on_btn_save = function () {
        
        var _url_proto = _global.dom.btn_global_use_url_protocol.hasClass('tp-selected'); // now we always need record replay.

        _global.dom.btn_save.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/save-cfg',
            {
                global: {
                    url_proto: _url_proto
                }
            },
            function (ret) {
                _global.dom.btn_save.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    $tp.notify_success('全局设置更新成功！');

                } else {
                    $tp.notify_error('全局设置更新失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                _global.dom.btn_save.removeAttr('disabled');
                $tp.notify_error('网路故障，全局连接控制设置更新失败！');
            }
        );

    };

    return _global;
};


$app.create_dlg_result = function () {
    var _dlg = {};

    _dlg.dom = {
        dlg: $('#dlg-result'),
        title: $('#dlg-result-title'),
        msg: $('#dlg-result-msg')
    };

    _dlg.show = function (title, msg) {
        _dlg.dom.title.text(title);
        _dlg.dom.msg.html(msg);
        _dlg.dom.dlg.modal();
    };

    return _dlg;
};

$app.create_config_smtp = function () {
    var _smtp = {};

    _smtp.dom = {
        server: $('#smtp-server-info'),
        port: $('#smtp-port-info'),
        ssl: $('#smtp-ssl-info'),
        sender: $('#smtp-sender-info'),
        btn_edit: $('#btn-edit-mail-config'),

        dlg_edit: $('#dlg-edit-smtp-config'),
        input_server: $('#edit-smtp-server'),
        input_port: $('#edit-smtp-port'),
        input_ssl: $('#edit-smtp-ssl'),
        input_sender: $('#edit-smtp-sender'),
        input_password: $('#edit-smtp-password'),
        input_recipient: $('#edit-smtp-test-recipient'),
        btn_send: $('#btn-send-test-mail'),
        msg_send: $('#msg-send-test-mail'),
        btn_save: $('#btn-save-mail-config')
    };

    _smtp.init = function (cb_stack) {
        _smtp.update_dom($app.options.sys_cfg.smtp);

        _smtp.dom.btn_edit.click(function () {
            _smtp.on_edit();
        });
        _smtp.dom.btn_send.click(function () {
            _smtp.on_btn_send();
        });
        _smtp.dom.btn_save.click(function () {
            _smtp.on_btn_save();
        });
        _smtp.dom.input_ssl.click(function () {
            if ($(this).hasClass('tp-selected'))
                $(this).removeClass('tp-selected');
            else
                $(this).addClass('tp-selected');
        });

        cb_stack.exec();
    };

    _smtp.update_dom = function (smtp) {
        if (0 === smtp.server.length) {
            var not_set = '<span class="error">未设置</span>';
            _smtp.dom.server.html(not_set);
            _smtp.dom.port.html(not_set);
            _smtp.dom.ssl.html(not_set);
            _smtp.dom.sender.html(not_set);
        } else {
            _smtp.dom.server.html(smtp.server);
            _smtp.dom.port.html(smtp.port);
            _smtp.dom.sender.html(smtp.sender);
            _smtp.dom.ssl.html(smtp.ssl ? '是' : '否');
        }
    };

    _smtp.on_edit = function () {
        var smtp = $app.options.sys_cfg.smtp;

        _smtp.dom.input_server.val(smtp.server);

        _smtp.dom.input_port.val(smtp.port);

        if (!smtp.ssl)
            _smtp.dom.input_ssl.removeClass('tp-selected');
        else
            _smtp.dom.input_ssl.removeClass('tp-selected').addClass('tp-selected');

        _smtp.dom.input_sender.val(smtp.sender);
        _smtp.dom.input_password.val('');

        _smtp.dom.dlg_edit.modal();
    };

    _smtp._check_input = function (_server, _port, _sender, _password) {
        if (_server.length === 0) {
            _smtp.dom.input_server.focus();
            $tp.notify_error('请填写SMTP服务器地址！');
            return false;
        }
        if (_port.length === 0) {
            _smtp.dom.input_port.focus();
            $tp.notify_error('请填写SMTP服务器端口！');
            return false;
        }
        if (_sender.length === 0) {
            _smtp.dom.input_sender.focus();
            $tp.notify_error('请填写发件人邮箱！');
            return false;
        }
        if (_password.length === 0) {
            _smtp.dom.input_password.focus();
            $tp.notify_error('请填写发件人邮箱密码！');
            return false;
        }

        return true;
    };

    _smtp.on_btn_send = function () {
        var _server = _smtp.dom.input_server.val();
        var _port = _smtp.dom.input_port.val();
        var _sender = _smtp.dom.input_sender.val();
        var _password = _smtp.dom.input_password.val();
        var _recipient = _smtp.dom.input_recipient.val();
        var _ssl = _smtp.dom.input_ssl.hasClass('tp-selected');

        if (!_smtp._check_input(_server, _port, _sender, _password))
            return;
        if (_recipient.length === 0) {
            _smtp.dom.input_recipient.focus();
            $tp.notify_error('请填写测试收件人邮箱！');
            return;
        }

        _smtp.dom.btn_send.attr('disabled', 'disabled');

        $tp.ajax_post_json('/system/send-test-mail',
            {
                server: _server,
                port: _port,
                ssl: _ssl,
                sender: _sender,
                password: _password,
                recipient: _recipient
            },
            function (ret) {
                _smtp.dom.btn_send.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    _smtp.dom.msg_send.slideDown('fast');
                } else {
                    $tp.notify_error(tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                _smtp.dom.btn_send.removeAttr('disabled');
                $tp.notify_error('网路故障，无法连接到服务器！');
            },
            15000
        );
    };

    _smtp.on_btn_save = function () {
        var _server = _smtp.dom.input_server.val();
        var _port = _smtp.dom.input_port.val();
        var _sender = _smtp.dom.input_sender.val();
        var _password = _smtp.dom.input_password.val();
        var _ssl = _smtp.dom.input_ssl.hasClass('tp-selected');

        if (!_smtp._check_input(_server, _port, _sender, _password))
            return;

        _smtp.dom.btn_save.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/save-cfg',
            {
                smtp: {
                    server: _server,
                    port: _port,
                    ssl: _ssl,
                    sender: _sender,
                    password: _password
                }
            },
            function (ret) {
                _smtp.dom.btn_save.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    $tp.notify_success('SMTP设置更新成功！');

                    _smtp.dom.input_password.val('');
                    // 更新一下界面上显示的配置信息
                    $app.options.sys_cfg.smtp.server = _server;
                    $app.options.sys_cfg.smtp.port = _port;
                    $app.options.sys_cfg.smtp.ssl = _ssl;
                    $app.options.sys_cfg.smtp.sender = _sender;
                    _smtp.update_dom($app.options.sys_cfg.smtp);

                    _smtp.dom.dlg_edit.modal('hide');

                } else {
                    $tp.notify_error('SMTP设置更新失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                _smtp.dom.btn_save.removeAttr('disabled');
                $tp.notify_error('网路故障，SMTP设置更新失败！');
            }
        );
    };

    return _smtp;
};

$app.create_config_sec = function () {
    var _sec = {};

    _sec.dom = {
        btn_save: $('#btn-save-secure-config'),

        btn_password_allow_reset: $('#sec-allow-reset-password'),
        btn_password_force_strong: $('#sec-force-strong-password'),
        input_password_timeout: $('#sec-password-timeout'),

        input_session_timeout: $('#sec-session-timeout'),
        input_login_retry: $('#sec-login-retry'),
        input_lock_timeout: $('#sec-lock-timeout'),
        // btn_auth_username_password: $('#sec-auth-username-password'),
        btn_auth_username_password_captcha: $('#sec-auth-username-password-captcha'),
        // btn_auth_username_oath: $('#sec-auth-username-oath'),
        btn_auth_username_password_oath: $('#sec-auth-username-password-oath'),

        btn_rebuild_ops_auz_map: $('#btn-rebuild-ops-auz-map'),
        btn_rebuild_audit_auz_map: $('#btn-rebuild-audit-auz-map')
    };

    _sec.init = function (cb_stack) {
        _sec.update_dom_password($app.options.sys_cfg.password);
        _sec.update_dom_login($app.options.sys_cfg.login);

        $('#tab-security').find('.tp-checkbox.tp-editable').click(function () {
            if ($(this).hasClass('tp-selected'))
                $(this).removeClass('tp-selected');
            else
                $(this).addClass('tp-selected');
        });

        _sec.dom.btn_save.click(function () {
            _sec.on_btn_save();
        });

        _sec.dom.btn_rebuild_ops_auz_map.click(function () {
            _sec.on_rebuild_ops_auz_map();
        });

        _sec.dom.btn_rebuild_audit_auz_map.click(function () {
            _sec.on_rebuild_audit_auz_map();
        });

        cb_stack.exec();
    };

    _sec.update_dom_password = function (password) {
        _sec.dom.btn_password_allow_reset.removeClass('tp-selected');
        if (password.allow_reset)
            _sec.dom.btn_password_allow_reset.addClass('tp-selected');

        _sec.dom.btn_password_force_strong.removeClass('tp-selected');
        if (password.force_strong)
            _sec.dom.btn_password_force_strong.addClass('tp-selected');

        _sec.dom.input_password_timeout.val(password.timeout);
    };

    _sec.update_dom_login = function (login) {
        _sec.dom.input_session_timeout.val(login.session_timeout);
        _sec.dom.input_login_retry.val(login.retry);
        _sec.dom.input_lock_timeout.val(login.lock_timeout);

        // _sec.dom.btn_auth_username_password.removeClass('tp-selected');
        // if (login.auth & TP_LOGIN_AUTH_USERNAME_PASSWORD)
        //     _sec.dom.btn_auth_username_password.addClass('tp-selected');
        _sec.dom.btn_auth_username_password_captcha.removeClass('tp-selected');
        if (login.auth & TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA)
            _sec.dom.btn_auth_username_password_captcha.addClass('tp-selected');
        // _sec.dom.btn_auth_username_oath.removeClass('tp-selected');
        // if (login.auth & TP_LOGIN_AUTH_USERNAME_OATH)
        //     _sec.dom.btn_auth_username_oath.addClass('tp-selected');
        _sec.dom.btn_auth_username_password_oath.removeClass('tp-selected');
        if (login.auth & TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH)
            _sec.dom.btn_auth_username_password_oath.addClass('tp-selected');
    };

    _sec.on_btn_save = function () {
        var _password_allow_reset = _sec.dom.btn_password_allow_reset.hasClass('tp-selected');
        var _password_force_strong = _sec.dom.btn_password_force_strong.hasClass('tp-selected');
        var _password_timeout = parseInt(_sec.dom.input_password_timeout.val());

        var _login_session_timeout = parseInt(_sec.dom.input_session_timeout.val());
        var _login_retry = parseInt(_sec.dom.input_login_retry.val());
        var _login_lock_timeout = parseInt(_sec.dom.input_lock_timeout.val());

        var _login_auth = 0;
        // if (_sec.dom.btn_auth_username_password.hasClass('tp-selected'))
        //     _login_auth |= TP_LOGIN_AUTH_USERNAME_PASSWORD;
        if (_sec.dom.btn_auth_username_password_captcha.hasClass('tp-selected'))
            _login_auth |= TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA;
        // if (_sec.dom.btn_auth_username_oath.hasClass('tp-selected'))
        //     _login_auth |= TP_LOGIN_AUTH_USERNAME_OATH;
        if (_sec.dom.btn_auth_username_password_oath.hasClass('tp-selected'))
            _login_auth |= TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH;

        if (_.isNaN(_password_timeout) || _password_timeout < 0 || _password_timeout > 180) {
            $tp.notify_error('密码有效期超出范围！');
            _sec.dom.input_password_timeout.focus();
            return;
        }
        if (_.isNaN(_login_session_timeout) || _login_session_timeout < 5 || _login_session_timeout > 1440) {
            $tp.notify_error('WEB会话超时超出范围！');
            _sec.dom.input_session_timeout.focus();
            return;
        }
        if (_.isNaN(_login_retry) || _login_retry < 0 || _login_retry > 10) {
            $tp.notify_error('密码尝试次数超出范围！');
            _sec.dom.input_login_retry.focus();
            return;
        }
        if (_.isNaN(_login_lock_timeout) || _login_lock_timeout < 0 || _login_lock_timeout > 9999) {
            $tp.notify_error('临时锁定时长超出范围！');
            _sec.dom.input_lock_timeout.focus();
            return;
        }

        _sec.dom.btn_save.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/save-cfg',
            {
                password: {
                    allow_reset: _password_allow_reset,
                    force_strong: _password_force_strong,
                    timeout: _password_timeout
                },
                login: {
                    session_timeout: _login_session_timeout,
                    retry: _login_retry,
                    lock_timeout: _login_lock_timeout,
                    auth: _login_auth
                }
            },
            function (ret) {
                _sec.dom.btn_save.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    $tp.notify_success('安全设置更新成功！');

                    // 更新一下界面上显示的配置信息
                    $app.options.sys_cfg.password.allow_reset = _password_allow_reset;
                    $app.options.sys_cfg.password.force_strong = _password_force_strong;
                    $app.options.sys_cfg.password.timeout = _password_timeout;

                    $app.options.sys_cfg.login.session_timeout = _login_session_timeout;
                    $app.options.sys_cfg.login.retry = _login_retry;
                    $app.options.sys_cfg.login.lock_timeout = _login_lock_timeout;
                    $app.options.sys_cfg.login.auth = _login_auth;

                    _sec.update_dom_password($app.options.sys_cfg.password);
                    _sec.update_dom_login($app.options.sys_cfg.login);
                } else {
                    $tp.notify_error('安全设置更新失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                _sec.dom.btn_save.removeAttr('disabled');
                $tp.notify_error('网路故障，安全设置更新失败！');
            }
        );

    };

    _sec.on_rebuild_ops_auz_map = function () {
        $tp.ajax_post_json('/system/rebuild-ops-auz-map', {},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('重建运维授权映射成功！');
                } else {
                    $tp.notify_error('重建运维授权映射失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，重建运维授权映射失败！');
            }
        );
    };

    _sec.on_rebuild_audit_auz_map = function () {
        $tp.ajax_post_json('/system/rebuild-audit-auz-map', {},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('重建审计授权映射成功！');
                } else {
                    $tp.notify_error('重建审计授权映射失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网络故障，重建审计授权映射失败！');
            }
        );
    };

    return _sec;
};

$app.create_config_sess = function () {
    var _sess = {};

    _sess.dom = {
        btn_save: $('#btn-save-session-config'),

        input_noop_timeout: $('#sess-noop-timeout'),

        btn_sess_rdp_allow_clipboard: $('#sess-rdp-allow-clipboard'),
        btn_sess_rdp_allow_disk: $('#sess-rdp-allow-disk'),
        btn_sess_rdp_allow_console: $('#sess-rdp-allow-console'),
        btn_sess_ssh_allow_shell: $('#sess-ssh-allow-shell'),
        btn_sess_ssh_allow_sftp: $('#sess-ssh-allow-sftp')
    };

    _sess.init = function (cb_stack) {
        _sess.update_dom_session_cfg($app.options.sys_cfg.session);

        $('#tab-session').find('.tp-checkbox.tp-editable').click(function () {
            if ($(this).hasClass('tp-selected'))
                $(this).removeClass('tp-selected');
            else
                $(this).addClass('tp-selected');
        });

        _sess.dom.btn_save.click(function () {
            _sess.on_btn_save();
        });

        cb_stack.exec();
    };

    _sess.update_dom_session_cfg = function (sess) {
        _sess.dom.btn_sess_rdp_allow_clipboard.removeClass('tp-selected');
        if (sess.flag_rdp & TP_FLAG_RDP_CLIPBOARD)
            _sess.dom.btn_sess_rdp_allow_clipboard.addClass('tp-selected');

        _sess.dom.btn_sess_rdp_allow_disk.removeClass('tp-selected');
        if (sess.flag_rdp & TP_FLAG_RDP_DISK)
            _sess.dom.btn_sess_rdp_allow_disk.addClass('tp-selected');

        _sess.dom.btn_sess_rdp_allow_console.removeClass('tp-selected');
        if (sess.flag_rdp & TP_FLAG_RDP_CONSOLE)
            _sess.dom.btn_sess_rdp_allow_console.addClass('tp-selected');

        _sess.dom.btn_sess_ssh_allow_shell.removeClass('tp-selected');
        if (sess.flag_rdp & TP_FLAG_SSH_SHELL)
            _sess.dom.btn_sess_ssh_allow_shell.addClass('tp-selected');

        _sess.dom.btn_sess_ssh_allow_sftp.removeClass('tp-selected');
        if (sess.flag_rdp & TP_FLAG_SSH_SFTP)
            _sess.dom.btn_sess_ssh_allow_sftp.addClass('tp-selected');

        _sess.dom.input_noop_timeout.val(sess.noop_timeout);
    };

    _sess.on_btn_save = function () {
        var flag_record = 0;
        flag_record |= TP_FLAG_RECORD_REPLAY; // now we always need record replay.
        flag_record |= TP_FLAG_RECORD_REAL_TIME; // not implement, set this flag for default.

        var flag_rdp = 0;
        flag_rdp |= TP_FLAG_RDP_DESKTOP; // before support remote-app, remote-desktop is the only way to access remote host.
        if(_sess.dom.btn_sess_rdp_allow_clipboard.hasClass('tp-selected'))
            flag_rdp |= TP_FLAG_RDP_CLIPBOARD;
        if(_sess.dom.btn_sess_rdp_allow_disk.hasClass('tp-selected'))
            flag_rdp |= TP_FLAG_RDP_DISK;
        if(_sess.dom.btn_sess_rdp_allow_console.hasClass('tp-selected'))
            flag_rdp |= TP_FLAG_RDP_CONSOLE;

        var flag_ssh = 0;
        if(_sess.dom.btn_sess_ssh_allow_shell.hasClass('tp-selected'))
            flag_ssh |= TP_FLAG_SSH_SHELL;
        if(_sess.dom.btn_sess_ssh_allow_sftp.hasClass('tp-selected'))
            flag_ssh |= TP_FLAG_SSH_SFTP;

        if (flag_ssh === 0) {
            $tp.notify_error('SSH选项都未选择，无法进行SSH连接哦！');
            return;
        }

        var _noop_timeout = parseInt(_sess.dom.input_noop_timeout.val());


        if (_.isNaN(_noop_timeout) || _noop_timeout < 0 || _noop_timeout > 60) {
            $tp.notify_error('会话超时设置超出范围！');
            _sess.dom.input_noop_timeout.focus();
            return;
        }

        _sess.dom.btn_save.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/save-cfg',
            {
                session: {
                    flag_record: flag_record,
                    flag_rdp: flag_rdp,
                    flag_ssh: flag_ssh,
                    noop_timeout: _noop_timeout
                }
            },
            function (ret) {
                _sess.dom.btn_save.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    $tp.notify_success('全局连接控制设置更新成功！');

                    // // 更新一下界面上显示的配置信息
                    // $app.options.sys_cfg.password.allow_reset = _password_allow_reset;
                    // $app.options.sys_cfg.password.force_strong = _password_force_strong;
                    // $app.options.sys_cfg.password.timeout = _password_timeout;
                    //
                    // $app.options.sys_cfg.login.session_timeout = _login_session_timeout;
                    // $app.options.sys_cfg.login.retry = _login_retry;
                    // $app.options.sys_cfg.login.lock_timeout = _login_lock_timeout;
                    // $app.options.sys_cfg.login.auth = _login_auth;
                    //
                    // _sec.update_dom_password($app.options.sys_cfg.password);
                    // _sec.update_dom_login($app.options.sys_cfg.login);
                } else {
                    $tp.notify_error('全局连接控制设置更新失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                _sess.dom.btn_save.removeAttr('disabled');
                $tp.notify_error('网路故障，全局连接控制设置更新失败！');
            }
        );

    };

    return _sess;
};

$app.create_config_storage = function () {
    var _sto = {};

    _sto.dom = {
        storage_size: $('#storage-size'),
        btn_save: $('#btn-save-storage-config'),
        btn_cleanup: $('#btn-clear-storage'),

        input_keep_log: $('#storage-keep-log'),
        input_keep_record: $('#storage-keep-record'),
        select_cleanup_hour: $('#select-cleanup-storage-hour'),
        select_cleanup_minute: $('#select-cleanup-storage-minute')
    };

    _sto.init = function (cb_stack) {
        // 当前会话录像存储空间：总 123.35GB，可用空间 85.17GB。
        var _info = [];
        if (!$app.options.core_cfg.detected) {
            _sto.dom.storage_size.removeClass().addClass('alert alert-danger');
            _info.push('未能连接到核心服务，无法获取存储空间信息！');
        } else {
            _sto.dom.storage_size.removeClass().addClass('alert alert-info');
            _info.push('<p>会话录像存储路径：<span class="mono">' + $app.options.core_cfg.replay_path + '</span></p>');
            _info.push('<p>会话录像存储空间：总 ' + tp_size2str($app.options.total_size, 2) + '，' + '可用 ' + tp_size2str($app.options.free_size, 2) + '。</p>');
        }
        _sto.dom.storage_size.html(_info.join(''));

        _sto.update_dom($app.options.sys_cfg.storage);

        _sto.dom.btn_save.click(function () {
            _sto.on_btn_save();
        });
        _sto.dom.btn_cleanup.click(function () {
            _sto.on_btn_cleanup();
        });

        cb_stack.exec();
    };

    _sto.update_dom = function (storage) {
        _sto.dom.input_keep_log.val(storage.keep_log);
        _sto.dom.input_keep_record.val(storage.keep_record);
        _sto.dom.select_cleanup_hour.val(storage.cleanup_hour);
        _sto.dom.select_cleanup_minute.val(storage.cleanup_minute);
    };

    _sto.on_btn_save = function () {
        var _keep_log = parseInt(_sto.dom.input_keep_log.val());
        var _keep_record = parseInt(_sto.dom.input_keep_record.val());

        var _cleanup_hour = parseInt(_sto.dom.select_cleanup_hour.val());
        var _cleanup_minute = parseInt(_sto.dom.select_cleanup_minute.val());

        if (!(_keep_log === 0 || (_keep_log >= 30 && _keep_log <= 365))) {
            $tp.notify_error('日志保留时间超出范围！');
            _sto.dom.input_keep_log.focus();
            return;
        }
        if (!(_keep_record === 0 || (_keep_record >= 30 && _keep_record <= 365))) {
            $tp.notify_error('会话录像保留时间超出范围！');
            _sto.dom.input_keep_record.focus();
            return;
        }

        _sto.dom.btn_save.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/save-cfg',
            {
                storage: {
                    keep_log: _keep_log,
                    keep_record: _keep_record,
                    cleanup_hour: _cleanup_hour,
                    cleanup_minute: _cleanup_minute
                }
            },
            function (ret) {
                _sto.dom.btn_save.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    $tp.notify_success('存储设置更新成功！');

                    // 更新一下界面上显示的配置信息
                    $app.options.sys_cfg.storage.keep_log = _keep_log;
                    $app.options.sys_cfg.storage.keep_record = _keep_record;
                    $app.options.sys_cfg.storage.cleanup_hour = _cleanup_hour;
                    $app.options.sys_cfg.storage.cleanup_minute = _cleanup_minute;

                    _sto.update_dom($app.options.sys_cfg.storage);
                } else {
                    $tp.notify_error('存储设置更新失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                _sto.dom.btn_save.removeAttr('disabled');
                $tp.notify_error('网路故障，存储设置更新失败！');
            }
        );
    };

    _sto.on_btn_cleanup = function () {
        var _keep_log = parseInt(_sto.dom.input_keep_log.val());
        var _keep_record = parseInt(_sto.dom.input_keep_record.val());

        if ($app.options.sys_cfg.storage.keep_log !== _keep_log || $app.options.sys_cfg.storage.keep_record !== _keep_record) {
            $tp.notify_error('您已经修改了设置，请先保存设置，再进行清理！');
            return;
        }
        if ($app.options.sys_cfg.storage.keep_log === 0 && $app.options.sys_cfg.storage.keep_record === 0) {
            $tp.notify_error('根据设置，没有需要清理的内容！');
            return;
        }

        _sto.dom.btn_cleanup.attr('disabled', 'disabled');
        $tp.ajax_post_json('/system/cleanup-storage', {},
            function (ret) {
                _sto.dom.btn_cleanup.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    console.log(ret);
                    $tp.notify_success('清理存储空间成功！');

                    var msg = [];
                    for (var i = 0; i < ret.data.length; ++i) {
                        msg.push('<p>' + ret.data[i] + '</p>');
                    }

                    $app.dlg_result.show('清理存储空间', msg.join(''));
                } else {
                    $tp.notify_error('清理存储空间失败：' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                _sto.dom.btn_cleanup.removeAttr('disabled');
                $tp.notify_error('网路故障，清理存储空间失败！');
            },
            120000
        );
    };

    return _sto;
};
