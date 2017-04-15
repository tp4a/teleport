"use strict";

ywl.on_init = function (cb_stack, cb_args) {
    if (ywl.page_options.user_name.length > 0) {
        $('#username_account').val(ywl.page_options.user_name);
    }

    $('#captcha_image').attr('src', '/auth/get-captcha?' + Math.random());

    ywl.app = ywl.create_app();
    cb_stack
        .add(ywl.app.init)
        .exec();
};

ywl.create_app = function () {
    var _app = {};

    _app.dom_login_account = null;

    _app.init = function (cb_stack, cb_args) {
        _app.dom_login_account = $('#login-type-account');

        $('#btn-login-account').click(_app.login_account);

        $('#captcha_image').click(function () {
            $(this).attr('src', '/auth/get-captcha?' + Math.random());
            $('#captcha').focus().val('');
        });
        $('#username_account').keydown(function (event) {
            $('[data-toggle="popover"]').popover('hide');
            if (event.which === 13) {
                $('#password_account').focus();
            }
        });
        $('#password_account').keydown(function (event) {
            $('[data-toggle="popover"]').popover('hide');
            if (event.which === 13) {
                $('#captcha').focus();
            }
        });
        $('#captcha').keydown(function (event) {
            $('[data-toggle="popover"]').popover('hide');
            if (event.which === 13) {
                _app.login_account();
            }
        });

        cb_stack.exec();
    };

    _app.login_account = function () {
        var str_username = '';
        var str_password = '';
        var str_captcha = '';
        var is_remember = false;

        var dom_username = $('#username_account');
        var dom_password = $('#password_account');
        var dom_captcha = $('#captcha');
        var dom_remember = $('#remember-me');

        str_username = dom_username.val();
        str_password = dom_password.val();
        str_captcha = dom_captcha.val();
        is_remember = dom_remember.is(':checked');

        if (str_username.length === 0) {
            show_op_box('error', '缺少账号！');
            dom_username.attr('data-content', "请填写您的账号！").popover('show');
            dom_username.focus();
            return;
        }

        if (str_password.length === 0) {
            show_op_box('error', '缺少密码！');
            dom_password.attr('data-content', "请填写密码！").popover('show');
            dom_password.focus();
            return;
        }

        if (str_captcha.length !== 4) {
            show_op_box('error', '验证码错误！');
            dom_captcha.attr('data-content', "验证码为4位数字和字母的组合，请重新填写！").popover('show').focus();
            return;
        }

        $('#btn_login').attr('disabled', 'disabled');
        show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在进行身份认证，请稍候...');

        // 先判断一下captcha是否正确，如果不正确，拒绝登录
        ywl.ajax_post_json('/auth/verify-captcha', {captcha: str_captcha},
            function (ret) {
                if (ret.code === TPE_OK) {
                    // 验证成功
                    hide_op_box();
                    show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在登录TELEPORT，请稍候...');
                    _app.do_account_login(str_username, str_password, str_captcha, is_remember);
                }
                else {
                    hide_op_box();
                    show_op_box('error', '验证码错误！');
                    $('#captcha_image').attr('src', '/auth/get-captcha?' + Math.random());
                    $('#captcha').focus().val('');
                }

                $('#btn_login').removeAttr('disabled');
            },
            function () {
                hide_op_box();
                show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
                $('#btn_login').removeAttr('disabled');
            }
        );
    };

    _app.do_account_login = function (username, userpwd, captcha, is_remember) {
        ywl.ajax_post_json('/auth/verify-user', {username: username, userpwd: userpwd, captcha: captcha, remember: is_remember},
            function (ret) {
                if (ret.code === TPE_OK) {
                    window.location.href = ywl.page_options.ref;
                } else {
                    hide_op_box();
                    show_op_box('error', '无法登录TELEPORT：' + ret.message);
                    console.log(ret);
                }

                $('#btn_login').removeAttr('disabled');
            },
            function () {
                hide_op_box();
                show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
                $('#btn_login').removeAttr('disabled');
            }
        );
    };

    return _app;
};

function hide_op_box() {
    $('#login_message').hide();
}

function show_op_box(op_type, op_msg) {
    var obj_box = $('#login_message');

    obj_box.html(op_msg);
    obj_box.removeClass().addClass('op_box op_' + op_type);
    obj_box.show();
}
