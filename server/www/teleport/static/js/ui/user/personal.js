"use strict";

ywl.on_init = function (cb_stack, cb_args) {
    ywl.dom = {
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
    };

//    ywl.dom.tmp_oath_secret.text(ywl.page_options.tmp_oath_secret);

    ywl.clear_password_input = function () {
        ywl.dom.input_current_password.val('');
        ywl.dom.input_new_password.val('');
        ywl.dom.input_new_password_confirm.val('');
    };

    ywl.dom.btn_modify_password.click(function () {
        var old_pwd = ywl.dom.input_current_password.val();
        var new_pwd_1 = ywl.dom.input_new_password.val();
        var new_pwd_2 = ywl.dom.input_new_password_confirm.val();
        if (old_pwd.length === 0) {
            ywl.notify_error('请输入当前密码！');
            ywl.dom.input_current_password.focus();
            return;
        }
        if (new_pwd_1.length === 0) {
            ywl.notify_error('请设置新密码！');
            ywl.dom.input_new_password.focus();
            return;
        }
        if (new_pwd_1 !== new_pwd_2) {
            ywl.notify_error('两次密码输入不一致！');
            ywl.dom.input_new_password_confirm.focus();
            return;
        }
        ywl.ajax_post_json('/auth/modify-pwd', {o_pwd: old_pwd, n_pwd: new_pwd_1, callback: 1},
            function (ret) {
                if (ret.code === TPE_OK) {
                    ywl.notify_success('密码修改成功！');
                    ywl.clear_password_input();
                } else if (ret.code === -101) {
                    ywl.notify_error('密码错误！');
                } else {
                    ywl.notify_error('密码修改失败：' + ret.message);
                }

            },
            function () {
                ywl.notify_error('密码修改失败！');
            }
        );
    });

    ywl.dom.btn_toggle_oath_download.click(function () {
        if (ywl.dom.oath_app_download_box.is(':hidden')) {
            ywl.dom.oath_app_download_box.slideDown('fast', function () {
                ywl.dom.btn_toggle_oath_download.html('收起 <i class="fa fa-angle-up"></i>');
            });
        } else {
            ywl.dom.oath_app_download_box.slideUp('fast', function () {
                ywl.dom.btn_toggle_oath_download.html('显示下载地址 <i class="fa fa-angle-down"></i>');
            });
        }
    });

    ywl.dom.btn_verify_oath_code.click(function () {
        var code = ywl.dom.input_oath_code.val().trim();
        if (code.length !== 6) {
            ywl.notify_error('动态验证码错误：应该是6位数字！');
            ywl.dom.input_oath_code_verify.focus();
            return;
        }

        ywl.ajax_post_json('/auth/oath-verify', {code: code},
            function (ret) {
                if (ret.code === TPE_OK) {
                    ywl.notify_success('动态验证码验证成功！');
                } else if (ret.code === -3) {
                    ywl.notify_error('动态验证码验证失败！');
                } else {
                    ywl.notify_error('发生内部错误！' + ret.code + ret.message);
                }
            },
            function () {
                ywl.notify_error('网路故障，无法连接到服务器！');
            }
        );
    });

    ywl.dom.btn_reset_oath_code.click(function () {
        ywl.ajax_post_json('/auth/oath-secret-reset', {},
            function (ret) {
                if (ret.code === TPE_OK) {
                    ywl.dom.oath_secret_image.attr('src', '/auth/oath-secret-qrcode?' + Math.random());
                    ywl.dom.tmp_oath_secret.text(ret.data.tmp_oath_secret);
                    ywl.dom.dlg_reset_oath_code.modal({backdrop: 'static'});
                } else {
                    ywl.notify_error('发生内部错误！');
                }
            },
            function () {
                ywl.notify_error('网路故障，无法连接到服务器！');
            }
        );
    });

    ywl.dom.btn_verify_oath_code_and_save.click(function () {
        var code = ywl.dom.input_oath_code_verify.val().trim();
        if (code.length !== 6) {
            ywl.notify_error('动态验证码错误：应该是6位数字！');
            ywl.dom.input_oath_code_verify.focus();
            return;
        }

        ywl.ajax_post_json('/auth/oath-update-secret', {code: code},
            function (ret) {
                if (ret.code === TPE_OK) {
                    ywl.notify_success('身份验证器绑定成功！您可以用此身份验证器登录系统了！');
                    ywl.dom.dlg_reset_oath_code.modal('hide');
                } else {
                    ywl.notify_error('发生内部错误！');
                }
            },
            function () {
                ywl.notify_error('网路故障，无法连接到服务器！');
            }
        );
    });

};