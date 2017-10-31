"use strict";

$app.on_init = function (cb_stack, cb_args) {
    $app.dom = {
        btn_reset_oath_code: $('#btn-reset-oath-code'),
        btn_verify_oath_code: $('#btn-verify-oath-code'),
        btn_verify_oath_code_and_save: $('#btn-verify-oath-and-save'),
        btn_modify_password: $('#btn-modify-password'),
        btn_toggle_oath_download: $('#toggle-oath-download'),

        oath_app_download_box: $('#oath-app-download-box'),

        input_current_password: $('#current-password'),
        input_new_password: $('#new-password-1'),
        input_new_password_confirm: $('#new-password-2'),
        input_oath_code: $('#oath-code'),
        input_oath_code_verify: $('#oath-code-verify'),

        dlg_reset_oath_code: $('#dialog-reset-oath-code'),
        oath_secret_image: $('#oath-secret-qrcode'),
        tmp_oath_secret: $('#tmp-oath-secret'),

        tp_time: $('#teleport-time')
    };

    $app.tp_time = 0;

    $app.fix_time_display = function(selector) {
        var obj = $('[data-field="'+selector+'"]');
        var val = parseInt(obj.attr('data-value'));
        obj.text(tp_format_datetime(tp_utc2local(val)));
    };

    $app.fix_time_display('create-time');
    $app.fix_time_display('last-login');

    $app.clear_password_input = function () {
        $app.dom.input_current_password.val('');
        $app.dom.input_new_password.val('');
        $app.dom.input_new_password_confirm.val('');
    };

    $app.dom.btn_modify_password.click(function () {
        var old_pwd = $app.dom.input_current_password.val();
        var new_pwd_1 = $app.dom.input_new_password.val();
        var new_pwd_2 = $app.dom.input_new_password_confirm.val();
        if (old_pwd.length === 0) {
            $tp.notify_error('请输入当前密码！');
            $app.dom.input_current_password.focus();
            return;
        }
        if (new_pwd_1.length === 0) {
            $tp.notify_error('请设置新密码！');
            $app.dom.input_new_password.focus();
            return;
        }
        if (new_pwd_1 !== new_pwd_2) {
            $tp.notify_error('两次密码输入不一致！');
            $app.dom.input_new_password_confirm.focus();
            return;
        }
        $tp.ajax_post_json('/auth/modify-pwd', {o_pwd: old_pwd, n_pwd: new_pwd_1, callback: 1},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('密码修改成功！');
                    $app.clear_password_input();
                } else if (ret.code === -101) {
                    $tp.notify_error('密码错误！');
                } else {
                    $tp.notify_error('密码修改失败：' + ret.message);
                }

            },
            function () {
                $tp.notify_error('密码修改失败！');
            }
        );
    });

    $app.dom.btn_toggle_oath_download.click(function () {
        if ($app.dom.oath_app_download_box.is(':hidden')) {
            $app.dom.oath_app_download_box.slideDown('fast', function () {
                $app.dom.btn_toggle_oath_download.html('收起 <i class="fa fa-angle-up"></i>');
            });
        } else {
            $app.dom.oath_app_download_box.slideUp('fast', function () {
                $app.dom.btn_toggle_oath_download.html('显示下载地址 <i class="fa fa-angle-down"></i>');
            });
        }
    });

    $app.dom.btn_verify_oath_code.click(function () {
        var code = $app.dom.input_oath_code.val().trim();
        if (code.length !== 6) {
            $tp.notify_error('动态验证码错误：应该是6位数字！');
            $app.dom.input_oath_code_verify.focus();
            return;
        }

        $tp.ajax_post_json('/auth/oath-verify', {code: code},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('动态验证码验证成功！');
                } else if (ret.code === -3) {
                    $tp.notify_error('动态验证码验证失败！');
                } else {
                    $tp.notify_error('发生内部错误！' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网路故障，无法连接到服务器！');
            }
        );
    });

    $app.dom.btn_reset_oath_code.click(function () {
        $tp.ajax_post_json('/auth/oath-secret-reset', {},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $app.dom.oath_secret_image.attr('src', '/auth/oath-secret-qrcode?' + Math.random());
                    $app.dom.tmp_oath_secret.text(ret.data.tmp_oath_secret);
                    $app.dom.dlg_reset_oath_code.modal({backdrop: 'static'});
                } else {
                    $tp.notify_error('发生内部错误！' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网路故障，无法连接到服务器！');
            }
        );
    });

    $app.dom.btn_verify_oath_code_and_save.click(function () {
        var code = $app.dom.input_oath_code_verify.val().trim();
        if (code.length !== 6) {
            $tp.notify_error('动态验证码错误：应该是6位数字！');
            $app.dom.input_oath_code_verify.focus();
            return;
        }

        $tp.ajax_post_json('/auth/oath-update-secret', {code: code},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('身份验证器绑定成功！您可以用此身份验证器登录系统了！');
                    $app.dom.dlg_reset_oath_code.modal('hide');
                } else {
                    $tp.notify_error('发生内部错误！' + tp_error_msg(ret.code, ret.message));
                }
            },
            function () {
                $tp.notify_error('网路故障，无法连接到服务器！');
            }
        );
    });

    // 获取服务器时间
    $app.sync_tp_time = function () {
        $tp.ajax_post_json('/system/get-time', {},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $app.tp_time = tp_utc2local(ret.data);
                    $app.show_tp_time();
                }
            },
            function () {
            }
        );
    };

    $app.sync_tp_time();

    $app.show_tp_time = function () {
        if ($app.tp_time === 0)
            return;
        $app.dom.tp_time.text(tp_format_datetime($app.tp_time));
        $app.tp_time += 1;
    };

    setInterval($app.show_tp_time, 1000);
    // 每五分钟同步一次服务器时间，避免长时间误差积累导致显示不正确
    setInterval($app.sync_tp_time, 1000 * 60 * 5);

    cb_stack.exec();
};
