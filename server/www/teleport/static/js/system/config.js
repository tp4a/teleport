"use strict";

$app.on_init = function () {
    $app.dom = {
        // btn_reset_oath_code: $('#btn-reset-oath-code'),
        // btn_verify_oath_code: $('#btn-verify-oath-code'),
        // btn_verify_oath_code_and_save: $('#btn-verify-oath-and-save'),
        // btn_modify_password: $('#btn-modify-password'),
        // btn_toggle_oath_download: $('#toggle-oath-download'),
        //
        // oath_app_download_box: $('#oath-app-download-box'),
        //
        // input_current_password: $('#current-password'),
        // input_new_password: $('#new-password-1'),
        // input_new_password_confirm: $('#new-password-2'),
        // input_oath_code: $('#oath-code'),
        // input_oath_code_verify: $('#oath-code-verify'),
        //
        // dlg_reset_oath_code: $('#dialog-reset-oath-code'),
        // oath_secret_image: $('#oath-secret-qrcode'),
        // tmp_oath_secret: $('#tmp-oath-secret'),

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

//    $app.dom.tmp_oath_secret.text($app.page_options.tmp_oath_secret);

    //=========================================
    // 邮件系统配置相关
    //=========================================
    $app.update_mail_info = function (smtp_info) {
        var not_set = '<span class="error">未设置</span>';
        if (0 === smtp_info.server.length)
            $app.dom.mail.smtp_server.html(not_set);
        else
            $app.dom.mail.smtp_server.html(smtp_info.server);

        if (-1 === smtp_info.port)
            $app.dom.mail.smtp_port.html(not_set);
        else
            $app.dom.mail.smtp_port.html(smtp_info.port);

        if (-1 === smtp_info.ssl)
            $app.dom.mail.smtp_ssl.html(not_set);
        else if (0 === smtp_info.ssl)
            $app.dom.mail.smtp_ssl.html('否');
        else
            $app.dom.mail.smtp_ssl.html('是');

        if (0 === smtp_info.sender.length)
            $app.dom.mail.smtp_sender.html(not_set);
        else
            $app.dom.mail.smtp_sender.html(smtp_info.sender);
    };

    $app.update_mail_info($app.options.sys_cfg.smtp);

    $app.dom.mail.btn_edit_mail_config.click(function () {
        var smtp_info = $app.options.sys_cfg.smtp;

        $app.dom.mail.edit_smtp_server.val(smtp_info.server);

        if(smtp_info.port === -1)
            $app.dom.mail.edit_smtp_port.val('');
        else
            $app.dom.mail.edit_smtp_port.val(smtp_info.port);

        if (-1 === smtp_info.ssl || 0 === smtp_info.ssl)
            $app.dom.mail.edit_smtp_ssl.removeClass('tp-selected');
        else
            $app.dom.mail.edit_smtp_ssl.removeClass('tp-selected').addClass('tp-selected');

        $app.dom.mail.edit_smtp_sender.val(smtp_info.sender);
        $app.dom.mail.edit_smtp_password.val('');

        $app.dom.mail.dlg_edit_mail_config.modal();
    });
    // $app.dom.mail.btn_edit_mail_config.trigger('click');
    $app.dom.mail.edit_smtp_ssl.click(function () {
        if ($app.dom.mail.edit_smtp_ssl.hasClass('tp-selected'))
            $app.dom.mail.edit_smtp_ssl.removeClass('tp-selected');
        else
            $app.dom.mail.edit_smtp_ssl.addClass('tp-selected');
    });
    $app.dom.mail.btn_send_test_mail.click($app._on_btn_send_test_mail);
    $app.dom.mail.btn_save_mail_config.click($app._on_btn_save_mail_config);
};

$app._edit_mail_config_check = function (_server, _port, _sender, _password) {
       if(_server.length === 0) {
        $app.dom.mail.edit_smtp_server.focus();
        $tp.notify_error('请填写SMTP服务器地址！');
        return false;
    }
    if(_port.length === 0) {
        $app.dom.mail.edit_smtp_port.focus();
        $tp.notify_error('请填写SMTP服务器端口！');
        return false;
    }
    if(_sender.length === 0) {
        $app.dom.mail.edit_smtp_sender.focus();
        $tp.notify_error('请填写发件人邮箱！');
        return false;
    }
    if(_password.length === 0) {
        $app.dom.mail.edit_smtp_password.focus();
        $tp.notify_error('请填写发件人邮箱密码！');
        return false;
    }

    return true;
};

$app._on_btn_send_test_mail = function () {
    var _server = $app.dom.mail.edit_smtp_server.val();
    var _port = $app.dom.mail.edit_smtp_port.val();
    var _sender = $app.dom.mail.edit_smtp_sender.val();
    var _password = $app.dom.mail.edit_smtp_password.val();
    var _recipient = $app.dom.mail.edit_smtp_test_recipient.val();
    var _ssl = ($app.dom.mail.edit_smtp_ssl.hasClass('tp-selected')) ? 1 : 0;

    if(!$app._edit_mail_config_check(_server, _port, _sender, _password))
        return;
    if(_recipient.length === 0) {
        $app.dom.mail.edit_smtp_test_recipient.focus();
        $tp.notify_error('请填写测试收件人邮箱！');
        return;
    }

    $app.dom.mail.btn_send_test_mail.attr('disabled', 'disabled');

    $tp.ajax_post_json('/system/send-test-mail',
        {
            smtp_server: _server,
            smtp_port: _port,
            smtp_ssl: _ssl,
            smtp_sender: _sender,
            smtp_password: _password,
            smtp_recipient: _recipient
        },
        function (ret) {
            $app.dom.mail.btn_send_test_mail.removeAttr('disabled');
            if (ret.code === TPE_OK) {
                $app.dom.mail.msg_send_test_mail.slideDown('fast');
            } else {
                $tp.notify_error(tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $app.dom.mail.btn_send_test_mail.removeAttr('disabled');
            $tp.notify_error('网路故障，无法连接到服务器！');
        },
        15000
    );
};

$app._on_btn_save_mail_config = function () {
    var _server = $app.dom.mail.edit_smtp_server.val();
    var _port = $app.dom.mail.edit_smtp_port.val();
    var _sender = $app.dom.mail.edit_smtp_sender.val();
    var _password = $app.dom.mail.edit_smtp_password.val();
    var _ssl = ($app.dom.mail.edit_smtp_ssl.hasClass('tp-selected')) ? 1 : 0;

    if(!$app._edit_mail_config_check(_server, _port, _sender, _password))
        return;

    $app.dom.mail.btn_save_mail_config.attr('disabled', 'disabled');
    $tp.ajax_post_json('/system/save-mail-config',
        {
            smtp_server: _server,
            smtp_port: _port,
            smtp_ssl: _ssl,
            smtp_sender: _sender,
            smtp_password: _password
        },
        function (ret) {
            $app.dom.mail.btn_save_mail_config.removeAttr('disabled');
            if (ret.code === TPE_OK) {
                $app.dom.mail.edit_smtp_password.val('');
                // 更新一下界面上显示的配置信息
                $app.options.sys_cfg.smtp.server = _server;
                $app.options.sys_cfg.smtp.port = _port;
                $app.options.sys_cfg.smtp.ssl = _ssl;
                $app.options.sys_cfg.smtp.sender = _sender;
                $app.update_mail_info($app.options.sys_cfg.smtp);

                $app.dom.mail.dlg_edit_mail_config.modal('hide');
            } else {
                $tp.notify_error(tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $app.dom.mail.btn_save_mail_config.removeAttr('disabled');
            $tp.notify_error('网路故障，无法连接到服务器！');
        }
    );
};
