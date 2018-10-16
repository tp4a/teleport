"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        title: $('#title'),
        icon_bg: $('#icon-bg'),

        op_message: null,

        error: {
            area: $('#area-error'),
            message: $('#area-error [data-field="message"]')
        },

        find: {
            area: $('#area-find-password'),
            captcha_image: $('#area-find-password [data-field="captcha-image"]'),
            input_username: $('#area-find-password [data-field="input-username"]'),
            input_email: $('#area-find-password [data-field="input-email"]'),
            input_captcha: $('#area-find-password [data-field="input-captcha"]'),
            btn_submit: $('#area-find-password [data-field="btn-submit"]'),
            message: $('#area-find-password [data-field="message"]')
        },

        set_password: {
            area: $('#area-set-password'),
            info: $('#area-set-password [data-field="info"]'),
            input_password: $('#area-set-password [data-field="input-password"]'),
            btn_switch_password: $('#area-set-password [data-field="btn-switch-password"]'),
            btn_switch_password_icon: $('#area-set-password [data-field="btn-switch-password"] i'),
            btn_submit: $('#area-set-password [data-field="btn-submit"]'),
            message: $('#area-set-password [data-field="message"]')
        }
    };

    $app.dom.find.captcha_image.click(function () {
        $(this).attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
        $app.dom.find.input_captcha.focus().val('');
    });

    $app.dom.find.btn_submit.click(function () {
        $app.on_send_find_password_email();
    });

    $app.dom.find.input_username.keydown(function (event) {
        if (event.which === 13) {
            $app.dom.find.input_email.focus();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });
    $app.dom.find.input_email.keydown(function (event) {
        if (event.which === 13) {
            $app.dom.find.input_captcha.focus();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });
    $app.dom.find.input_captcha.keydown(function (event) {
        if (event.which === 13) {
            $app.on_send_find_password_email();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });

    $app.dom.set_password.btn_submit.click(function () {
        $app.on_set_new_password();
    });

    $app.dom.set_password.input_password.keydown(function (event) {
        if (event.which === 13) {
            $app.on_set_new_password();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });

    $app.dom.set_password.btn_switch_password.click(function () {
        if ('password' === $app.dom.set_password.input_password.attr('type')) {
            $app.dom.set_password.input_password.attr('type', 'text');
            $app.dom.set_password.btn_switch_password_icon.removeClass('fa-eye').addClass('fa-eye-slash')
        } else {
            $app.dom.set_password.input_password.attr('type', 'password');
            $app.dom.set_password.btn_switch_password_icon.removeClass('fa-eye-slash').addClass('fa-eye')
        }
    });

    if ($app.options.mode === 1) {
        // show 'find-my-password' page
        $app.dom.op_message = $app.dom.find.message;
        $app.dom.title.text('重置密码');
        $app.dom.icon_bg.addClass('fas fa-search-plus').css('color', '#286090');
        $app.dom.find.captcha_image.attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
        $app.dom.find.area.show();
        $app.dom.find.input_username.focus();
    } else if ($app.options.mode === 2) {
        // show 'error' page
        $app.dom.icon_bg.addClass('fas fa-exclamation-triangle').css('color', '#ff6242');
        if ($app.options.code === TPE_NOT_EXISTS) {
            $app.dom.title.text('链接无效');
            $app.dom.error.message.html('当前使用的密码重置链接无效，可能已经因过期而被清除！密码重置链接仅在24小时内有效，请及时设置您的新密码！');
        } else if ($app.options.code === TPE_EXPIRED) {
            $app.dom.title.text('链接已过期');
            $app.dom.error.message.html('当前使用的密码重置链接已经过期！密码重置链接仅在24小时内有效，请及时设置您的新密码！');
        } else if ($app.options.code === TPE_NETWORK) {
            $app.dom.title.text('功能未启用');
            $app.dom.error.message.html('系统尚未配置邮件发送功能，无法进行密码找回操作！');
        } else if ($app.options.code === TPE_PRIVILEGE) {
            $app.dom.title.text('功能已禁用');
            $app.dom.error.message.html('根据系统配置，禁止进行密码找回操作！');
        } else {
            $app.dom.title.text('发生错误！');
            $app.dom.error.message.html('很抱歉发生了错误：' + tp_error_msg($app.options.code));
        }
        $app.dom.error.area.show();
    } else if ($app.options.mode === 3) {
        // show 'set-new-password' page
        $app.dom.op_message = $app.dom.set_password.message;
        $app.dom.title.text('重置密码');
        $app.dom.icon_bg.addClass('fa fa-info-circle').css('color', '#357a3c');
        if ($app.options.force_strong)
            $app.dom.set_password.info.show();
        $app.dom.set_password.area.show();
    }

    cb_stack.exec();
};

$app.hide_op_box = function () {
    $app.dom.op_message.hide();
};

$app.show_op_box = function (op_type, op_msg) {
    $app.dom.op_message.html(op_msg);
    $app.dom.op_message.removeClass().addClass('op_box op_' + op_type);
    $app.dom.op_message.show();
};

$app.on_send_find_password_email = function () {
    $app.hide_op_box();
    var str_username = $app.dom.find.input_username.val();
    var str_email = $app.dom.find.input_email.val();
    var str_captcha = $app.dom.find.input_captcha.val();

    if (str_username.length === 0) {
        $app.show_op_box('error', '用户名未填写！');
        $app.dom.find.input_username.attr('data-content', "请填写您的用户名！").focus().popover('show');
        return;
    }

    if (str_email.length === 0) {
        $app.show_op_box('error', '电子邮件地址未填写！');
        $app.dom.find.input_email.attr('data-content', "请填写您的电子邮件地址！").focus().popover('show');
        return;
    }

    if (!tp_is_email(str_email)) {
        $app.show_op_box('error', '无效的电子邮件地址！');
        $app.dom.find.input_email.attr('data-content', "请检查输入的电子邮件地址！").focus().popover('show');
        return;
    }

    if (str_captcha.length !== 4) {
        $app.show_op_box('error', '验证码错误！');
        $app.dom.find.input_captcha.attr('data-content', "验证码为4位数字和字母的组合，请重新填写！").focus().select().popover('show');
        return;
    }

    $app.dom.find.btn_submit.attr('disabled', 'disabled');
    $tp.ajax_post_json('/auth/verify-captcha', {captcha: str_captcha},
        function (ret) {
            if (ret.code === TPE_OK) {
                // 验证成功
                $app.hide_op_box();
                $app.show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在发送密码重置确认函，请稍候...');
                $app.do_send_reset_email(str_username, str_email, str_captcha);
            }
            else {
                $app.dom.find.btn_submit.removeAttr('disabled');
                $app.hide_op_box();
                $app.show_op_box('error', tp_error_msg(ret.code, ret.message));
                $app.dom.captcha_image.attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
                $app.dom.input_captcha.focus().select().val('');
            }
        },
        function () {
            $app.hide_op_box();
            $app.show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
            $app.dom.find.btn_submit.removeAttr('disabled');
        }
    );
};

$app.do_send_reset_email = function (str_username, str_email, str_captcha) {
    $tp.ajax_post_json('/user/do-reset-password', {
            mode: 3,
            username: str_username,
            email: str_email,
            captcha: str_captcha
        },
        function (ret) {
            if (ret.code === TPE_OK) {
                $app.dom.find.btn_submit.slideUp('fast');
                $app.show_op_box('success', '密码重置确认函已发送，请注意查收！');
            } else {
                $app.dom.find.btn_submit.removeAttr('disabled');
                $app.hide_op_box();
                var msg = '';
                if (ret.code === TPE_NOT_EXISTS)
                    msg = tp_error_msg(ret.code, '用户不存在，请检查输入的用户和电子邮件地址是否匹配！');
                else
                    msg = tp_error_msg(ret.code, ret.message);
                $app.show_op_box('error', msg);
            }
        },
        function () {
            $app.dom.find.btn_submit.removeAttr('disabled');
            $app.hide_op_box();
            $app.show_op_box('error', '网络故障，密码重置确认函发送失败！');
        },
        15000
    );
};

$app.on_set_new_password = function () {
    $app.hide_op_box();
    var str_password = $app.dom.set_password.input_password.val();

    if (str_password.length === 0) {
        $app.show_op_box('error', '密码未填写！');
        $app.dom.set_password.input_password.attr('data-content', "请设置您的新密码！").focus().popover('show');
        return;
    }

    if ($app.options.force_strong) {
        if (!tp_check_strong_password(str_password)) {
            $app.show_op_box('error', tp_error_msg(TPE_FAILED, '抱歉，不能使用弱密码！'));
            $app.dom.set_password.input_password.attr('data-content', "请设置强密码：至少8位，必须包含大写字母、小写字母以及数字！").focus().popover('show');
            return;
        }
    }

    $tp.ajax_post_json('/user/do-reset-password', {
            mode: 4,
            token: $app.options.token,
            password: str_password
        },
        function (ret) {
            $app.dom.find.btn_submit.removeAttr('disabled');
            if (ret.code === TPE_OK) {
                $app.show_op_box('success', '密码已重置，正在转到登录界面！');
                setTimeout(function () {
                    window.location.href = '/';
                }, 2000);
            } else {
                var msg = '';
                if (ret.code === TPE_NOT_EXISTS)
                    msg = tp_error_msg(ret.code, '无效的密码重置链接！');
                else
                    msg = tp_error_msg(ret.code, ret.message);
                $app.show_op_box('error', msg);
            }
        },
        function () {
            $app.dom.find.btn_submit.removeAttr('disabled');
            $app.hide_op_box();
            $app.show_op_box('error', '网络故障，密码重置失败！');
        }
    );
};
