"use strict";

$app.on_init = function (cb_stack) {
    console.log($app.options);

    $app.dom = {

        // 邮件系统设置
        mail: {
            smtp_server: $('#smtp-server-info'),
            smtp_port: $('#smtp-port-info'),
            smtp_ssl: $('#smtp-ssl-info'),
            smtp_sender: $('#smtp-sender-info'),
            btn_edit_mail_config: $('#btn-edit-mail-config'),

            dlg_edit_mail_config: $('#dlg-edit-mail-config'),
            edit_smtp_server: $('#edit-smtp-server'),
            edit_smtp_port: $('#edit-smtp-port'),
            edit_smtp_ssl: $('#edit-smtp-ssl'),
            edit_smtp_sender: $('#edit-smtp-sender'),
            edit_smtp_password: $('#edit-smtp-password'),
            edit_smtp_test_recipient: $('#edit-smtp-test-recipient'),
            btn_send_test_mail: $('#btn-send-test-mail'),
            msg_send_test_mail: $('#msg-send-test-mail'),
            btn_save_mail_config: $('#btn-save-mail-config')
        }
    };

    $app.smtp = $app.create_config_smtp();
    cb_stack.add($app.smtp.init);

    //=========================================
    // 邮件系统配置相关
    //=========================================
    // $app.update_mail_info = function (smtp) {
    //     if (0 === smtp.server.length) {
    //         var not_set = '<span class="error">未设置</span>';
    //         $app.dom.mail.smtp_server.html(not_set);
    //         $app.dom.mail.smtp_port.html(not_set);
    //         $app.dom.mail.smtp_ssl.html(not_set);
    //         $app.dom.mail.smtp_sender.html(not_set);
    //     } else {
    //         $app.dom.mail.smtp_server.html(smtp.server);
    //         $app.dom.mail.smtp_port.html(smtp.port);
    //         $app.dom.mail.smtp_sender.html(smtp.sender);
    //
    //         if (smtp.ssl)
    //             $app.dom.mail.smtp_ssl.html('是');
    //         else
    //             $app.dom.mail.smtp_ssl.html('否');
    //     }
    // };
    //
    // $app.update_mail_info($app.options.sys_cfg.smtp);

    // $app.dom.mail.btn_edit_mail_config.click(function () {
    //     var smtp = $app.options.sys_cfg.smtp;
    //
    //     $app.dom.mail.edit_smtp_server.val(smtp.server);
    //
    //     $app.dom.mail.edit_smtp_port.val(smtp.port);
    //
    //     if (!smtp.ssl)
    //         $app.dom.mail.edit_smtp_ssl.removeClass('tp-selected');
    //     else
    //         $app.dom.mail.edit_smtp_ssl.removeClass('tp-selected').addClass('tp-selected');
    //
    //     $app.dom.mail.edit_smtp_sender.val(smtp.sender);
    //     $app.dom.mail.edit_smtp_password.val('');
    //
    //     $app.dom.mail.dlg_edit_mail_config.modal();
    // });
    // $app.dom.mail.btn_edit_mail_config.trigger('click');
    // $app.dom.mail.edit_smtp_ssl.click(function () {
    //     if ($app.dom.mail.edit_smtp_ssl.hasClass('tp-selected'))
    //         $app.dom.mail.edit_smtp_ssl.removeClass('tp-selected');
    //     else
    //         $app.dom.mail.edit_smtp_ssl.addClass('tp-selected');
    // });
    // $app.dom.mail.btn_send_test_mail.click($app._on_btn_send_test_mail);
    // $app.dom.mail.btn_save_mail_config.click($app._on_btn_save_mail_config);

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
            //
            // if (smtp.ssl)
            //     _smtp.dom.ssl.html('是');
            // else
            //     _smtp.dom.ssl.html('否');
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


