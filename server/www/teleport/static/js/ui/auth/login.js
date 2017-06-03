"use strict";

var LOGIN_TYPE_PASSWORD = 1; // 使用用户名密码登录（额外需要验证码）
var LOGIN_TYPE_OATH = 2;    // 使用用户名密码登录（额外需要身份验证器的动态验证码）

ywl.on_init = function (cb_stack, cb_args) {
    if (ywl.page_options.user_name.length > 0) {
        $('#username-account').val(ywl.page_options.user_name);
    }

    $('#captcha-image').attr('src', '/auth/get-captcha?' + Math.random());

    ywl.app = ywl.create_app();
    cb_stack
        .add(ywl.app.init)
        .exec();
};

ywl.create_app = function () {
    var _app = {};

    _app.login_type = LOGIN_TYPE_PASSWORD;

    _app.dom = {
        btn_login_type_password: $('#login-type-password'),
        btn_login_type_oath: $('#login-type-oath'),
        area_captcha: $('#login-area-captcha'),
        area_oath: $('#login-area-oath'),
        captcha_image: $('#captcha-image'),

        input_username: $('#username-account'),
        input_password: $('#password-account'),
        input_captcha: $('#captcha'),
        input_oath: $('#oath-code'),

        remember: $('#remember-me'),
        btn_login: $('#btn-login'),

        message: $('#message')
    };


//    _app.dom_login_account = null;
//    _app.dom_login_google = null;

    _app.init = function (cb_stack, cb_args) {
//        _app.dom_login_account = $('#login-type-account');
//        _app.dom_login_google = $('#login-type-google');

        _app.dom.btn_login_type_password.click(function () {
            _app.login_type = LOGIN_TYPE_PASSWORD;
            _app.dom.btn_login_type_oath.removeClass('selected');
            $(this).addClass('selected');
            _app.dom.area_oath.slideUp(100);
            _app.dom.area_captcha.slideDown(100);
        });
        _app.dom.btn_login_type_oath.click(function () {
            _app.login_type = LOGIN_TYPE_OATH;
            _app.dom.btn_login_type_password.removeClass('selected');
            $(this).addClass('selected');
            _app.dom.area_oath.slideDown(100);
            _app.dom.area_captcha.slideUp(100);
        });


        _app.dom.btn_login.click(_app.login_account);

        _app.dom.captcha_image.click(function () {
            $(this).attr('src', '/auth/get-captcha?' + Math.random());
            _app.dom.input_captcha.focus().val('');
        });
        _app.dom.input_username.keydown(function (event) {
            $('[data-toggle="popover"]').popover('hide');
            if (event.which === 13) {
                _app.dom.input_password.focus();
            }
        });
        _app.dom.input_password.keydown(function (event) {
            $('[data-toggle="popover"]').popover('hide');
            if (event.which === 13) {
                if(_app.login_type === LOGIN_TYPE_PASSWORD)
                    _app.dom.input_captcha.focus();
                else if(_app.login_type === LOGIN_TYPE_OATH)
                    _app.dom.input_oath.focus();
            }
        });
        _app.dom.input_captcha.keydown(function (event) {
            $('[data-toggle="popover"]').popover('hide');
            if (event.which === 13) {
                _app.login_account();
            }
        });

        cb_stack.exec();
    };

    _app.login_account = function () {
//        var str_username = '';
//        var str_password = '';
//        var str_captcha = '';
//        var str_gcode = '';
//        var is_remember = false;
//
//        var dom_username = $('#username-account');
//        var dom_password = $('#password-account');
//        var dom_captcha = $('#captcha');
//        var dom_gcode = $('#oath-code');
//        var dom_remember = $('#remember-me');

        var str_username = _app.dom.input_username.val();
        var str_password = _app.dom.input_password.val();
        var str_captcha = _app.dom.input_captcha.val();
        var str_oath = _app.dom.input_oath.val();
        var is_remember = _app.dom.remember.is(':checked');

        if (str_username.length === 0) {
            show_op_box('error', '缺少账号！');
            _app.dom.input_username.attr('data-content', "请填写您的账号！").popover('show');
            _app.dom.input_username.focus();
            return;
        }

        if (str_password.length === 0) {
            show_op_box('error', '缺少密码！');
            _app.dom.input_password.attr('data-content', "请填写密码！").popover('show');
            _app.dom.input_password.focus();
            return;
        }

        if (_app.login_type === 'account') {
            if (str_captcha.length !== 4) {
                show_op_box('error', '验证码错误！');
                _app.dom.input_captcha.attr('data-content', "验证码为4位数字和字母的组合，请重新填写！").popover('show').focus();
                return;
            }
        } else if (_app.login_type === 'google') {
            if (str_oath.length !== 6) {
                show_op_box('error', '身份验证器动态验证码错误！');
                _app.dom.input_oath.attr('data-content', "身份验证器动态验证码为6位数字，请重新填写！").popover('show').focus();
                return;
            }
        }

        _app.dom.btn_login.attr('disabled', 'disabled');
        _app.show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在进行身份认证，请稍候...');

        // 先判断一下captcha是否正确，如果不正确，拒绝登录
        if (_app.login_type === LOGIN_TYPE_PASSWORD) {
            ywl.ajax_post_json('/auth/verify-captcha', {captcha: str_captcha},
                function (ret) {
                    if (ret.code === TPE_OK) {
                        // 验证成功
                        _app.hide_op_box();
                        _app.show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在登录TELEPORT，请稍候...');
                        _app.do_account_login(str_username, str_password, str_captcha, str_oath, is_remember);
                    }
                    else {
                        _app.hide_op_box();
                        _app.show_op_box('error', '验证码错误！');
                        _app.dom.captcha_image.attr('src', '/auth/get-captcha?' + Math.random());
                        _app.dom.input_captcha.focus().val('');
                    }

                    _app.dom.btn_login.removeAttr('disabled');
                },
                function () {
                    _app.hide_op_box();
                    _app.show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
                    _app.dom.btn_login.removeAttr('disabled');
                }
            );
        } else {
            _app.do_account_login(str_username, str_password, str_captcha, str_oath, is_remember);
        }
    };

    _app.do_account_login = function (username, password, captcha, oath, is_remember) {
        var login_type = '';
        if(_app.login_type === LOGIN_TYPE_PASSWORD) {
            login_type = 'password';
        } else if(_app.login_type === LOGIN_TYPE_OATH) {
            login_type = 'oath';
        }
        var args = {type:login_type, username: username, password: password, captcha: captcha, oath: oath, remember: is_remember};
        console.log(args);
        ywl.ajax_post_json('/auth/verify-user', args,
            function (ret) {
                if (ret.code === TPE_OK) {
                    window.location.href = ywl.page_options.ref;
                } else {
                    _app.hide_op_box();
                    _app.show_op_box('error', '无法登录TELEPORT：' + ret.message);
                    console.log(ret);
                }

                _app.dom.btn_login.removeAttr('disabled');
            },
            function () {
                _app.hide_op_box();
                _app.show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
                _app.dom.btn_login.removeAttr('disabled');
            }
        );
    };

    _app.hide_op_box = function() {
        _app.dom.message.hide();
    };

    _app.show_op_box = function(op_type, op_msg) {
        _app.dom.message.html(op_msg);
        _app.dom.message.removeClass().addClass('op_box op_' + op_type);
        _app.dom.message.show();
    };

    return _app;
};

