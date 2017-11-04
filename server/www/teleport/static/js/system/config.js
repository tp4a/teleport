"use strict";

$app.on_init = function (cb_stack) {
    console.log($app.options);

    //=========================================
    // 邮件系统配置相关
    //=========================================
    $app.smtp = $app.create_config_smtp();
    cb_stack.add($app.smtp.init);

    $app.sec = $app.create_config_sec();
    cb_stack.add($app.sec.init);

    cb_stack.exec();
};

$app.create_config_smtp = function () {
    var _smtp = {};

    _smtp.dom = {
        server: $('#smtp-server-info'),
        port: $('#smtp-port-info'),
        ssl: $('#smtp-ssl-info'),
        sender: $('#smtp-sender-info'),
        btn_edit: $('#btn-edit-mail-config'),

        dlg_edit: $('#dlg-edit-mail-config'),
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
        $tp.ajax_post_json('/system/save-cfg-smtp',
            {
                server: _server,
                port: _port,
                ssl: _ssl,
                sender: _sender,
                password: _password
            },
            function (ret) {
                _smtp.dom.btn_save.removeAttr('disabled');
                if (ret.code === TPE_OK) {
                    _smtp.dom.input_password.val('');
                    // 更新一下界面上显示的配置信息
                    $app.options.sys_cfg.smtp.server = _server;
                    $app.options.sys_cfg.smtp.port = _port;
                    $app.options.sys_cfg.smtp.ssl = _ssl;
                    $app.options.sys_cfg.smtp.sender = _sender;
                    _smtp.update_dom($app.options.sys_cfg.smtp);

                    _smtp.dom.dlg_edit.modal('hide');
                } else {
                    $tp.notify_error(tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                _smtp.dom.btn_save.removeAttr('disabled');
                $tp.notify_error('网路故障，无法连接到服务器！');
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
        btn_auth_username_password: $('#sec-auth-username-password'),
        btn_auth_username_password_captcha: $('#sec-auth-username-password-captcha'),
        btn_auth_username_oath: $('#sec-auth-username-oath'),
        btn_auth_username_password_oath: $('#sec-auth-username-password-oath')
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

        _sec.dom.btn_auth_username_password.removeClass('tp-selected');
        if (login.auth & TP_LOGIN_AUTH_USERNAME_PASSWORD)
            _sec.dom.btn_auth_username_password.addClass('tp-selected');
        if (login.auth & TP_LOGIN_AUTH_USERNAME_PASSWORD_CAPTCHA)
            _sec.dom.btn_auth_username_password_captcha.addClass('tp-selected');
        if (login.auth & TP_LOGIN_AUTH_USERNAME_OATH)
            _sec.dom.btn_auth_username_oath.addClass('tp-selected');
        if (login.auth & TP_LOGIN_AUTH_USERNAME_PASSWORD_OATH)
            _sec.dom.btn_auth_username_password_oath.addClass('tp-selected');
    };

    _sec.on_btn_save = function() {
        var _password_allow_reset = _sec.dom.btn_password_allow_reset.hasClass('tp-selected');

    };

    return _sec;
};
