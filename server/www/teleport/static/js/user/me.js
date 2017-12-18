"use strict";

$app.on_init = function (cb_stack, cb_args) {
    $app.dom = {
        btn_modify_password: $('#btn-modify-password'),

        input_current_password: $('#current-password'),
        input_new_password: $('#new-password-1'),
        input_new_password_confirm: $('#new-password-2')
    };

    $app.fix_time_display = function(selector) {
        var obj = $('[data-field="'+selector+'"]');
        var val = parseInt(obj.attr('data-value'));
        if (val === 0)
            obj.text('-');
        else
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
        $tp.ajax_post_json('/user/do-reset-password', {mode: 5, current_password: old_pwd, password: new_pwd_1},
            function (ret) {
                if (ret.code === TPE_OK) {
                    $tp.notify_success('密码修改成功！');
                    $app.clear_password_input();
                } else if (ret.code === -101) {
                    $tp.notify_error('密码错误！');
                } else {
                    $tp.notify_error('密码修改失败：' + tp_error_msg(ret.code, ret.message));
                }

            },
            function () {
                $tp.notify_error('密码修改失败！');
            }
        );
    });

    cb_stack.exec();
};
