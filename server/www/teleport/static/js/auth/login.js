"use strict";

var BLUR_BG_COUNT = 8;
var SLOGAN = [
    '我感谢那段时光，<br/>因为不曾把我打倒的，<br/>最终让我变得更加强大！',
    '宁愿在做事中犯错，<br/>也不要为了不犯错而什么都不做。',
    '从出生到死，<br/>只有900个月，<br/>所以虚耗每一分钟，<br/>都是巨大的浪费！',
    '没有播种，何来收获；<br/>没有辛劳，何来成功；<br/>没有磨难，何来荣耀；<br/>没有挫折，何来辉煌。',
    '宝剑锋从磨砺出，<br/>梅花香自苦寒来。',
    '不登高山，不知天之高也；<br/>不临深溪，不知地之厚也。',
    '追求进步，<br/>不求完美。'
];


// $app.on_init = function (cb_stack, cb_args) {
$app.on_init = function (cb_stack) {
    $app.login_type = LOGIN_TYPE_PASSWORD_CAPTCHA;
    $app.dom = {
        slogan: $('#msg-slogan'),
        btn_login_type_password: $('#login-type-password'),
        btn_login_type_oath: $('#login-type-oath'),
        area_captcha: $('#login-area-captcha'),
        area_oath: $('#login-area-oath'),
        captcha_image: $('#captcha-image'),

        input_username: $('#login-area-username [data-field="username"]'),
        input_password: $('#login-area-username [data-field="password"]'),
        input_captcha: $('#captcha'),
        input_oath: $('#oath-code'),

        remember: $('#remember-me'),
        btn_login: $('#btn-login'),

        message: $('#message')
    };

    console.log($app.options);
    if ($app.options.username.length > 0) {
        $app.dom.input_username.val($app.options.username);
    }

    $app.dom.captcha_image.attr('src', '/auth/captcha?' + Math.random());

    window.onresize = $app.on_screen_resize;
    $app.init_blur_bg();
    $app.init_slogan();

    $app.dom.btn_login_type_password.click(function () {
        $app.login_type = LOGIN_TYPE_PASSWORD_CAPTCHA;
        $app.dom.btn_login_type_oath.removeClass('selected');
        $(this).addClass('selected');
        $app.dom.area_oath.slideUp(100);
        $app.dom.area_captcha.slideDown(100);
    });
    $app.dom.btn_login_type_oath.click(function () {
        $app.login_type = LOGIN_TYPE_PASSWORD_OATH;
        $app.dom.btn_login_type_password.removeClass('selected');
        $(this).addClass('selected');
        $app.dom.area_oath.slideDown(100);
        $app.dom.area_captcha.slideUp(100);
    });


    $app.dom.btn_login.click($app.login_account);

    $app.dom.captcha_image.click(function () {
        $(this).attr('src', '/auth/captcha?' + Math.random());
        $app.dom.input_captcha.focus().val('');
    });
    $app.dom.input_username.keydown(function (event) {
        $('[data-toggle="popover"]').popover('hide');
        if (event.which === 13) {
            $app.dom.input_password.focus();
        }
    });
    $app.dom.input_password.keydown(function (event) {
        $('[data-toggle="popover"]').popover('hide');
        if (event.which === 13) {
            if ($app.login_type === LOGIN_TYPE_PASSWORD_CAPTCHA)
                $app.dom.input_captcha.focus();
            else if ($app.login_type === LOGIN_TYPE_PASSWORD_OATH)
                $app.dom.input_oath.focus();
        }
    });
    $app.dom.input_captcha.keydown(function (event) {
        $('[data-toggle="popover"]').popover('hide');
        if (event.which === 13) {
            $app.login_account();
        }
    });
    $app.dom.input_oath.keydown(function (event) {
        $('[data-toggle="popover"]').popover('hide');
        if (event.which === 13) {
            $app.login_account();
        }
    });

    cb_stack.exec();
};

$app.hide_op_box = function () {
    $app.dom.message.hide();
};

$app.show_op_box = function (op_type, op_msg) {
    $app.dom.message.html(op_msg);
    $app.dom.message.removeClass().addClass('op_box op_' + op_type);
    $app.dom.message.show();
};

$app.login_account = function () {
    var str_username = $app.dom.input_username.val();
    var str_password = $app.dom.input_password.val();
    var str_captcha = $app.dom.input_captcha.val();
    var str_oath = $app.dom.input_oath.val();
    var is_remember = $app.dom.remember.is(':checked');

    if (str_username.length === 0) {
        $app.show_op_box('error', '缺少账号！');
        $app.dom.input_username.attr('data-content', "请填写您的账号！").popover('show');
        $app.dom.input_username.focus();
        return;
    }

    if (str_password.length === 0) {
        $app.show_op_box('error', '缺少密码！');
        $app.dom.input_password.attr('data-content', "请填写密码！").popover('show');
        $app.dom.input_password.focus();
        return;
    }

    if ($app.login_type === LOGIN_TYPE_PASSWORD_CAPTCHA) {
        if (str_captcha.length !== 4) {
            $app.show_op_box('error', '验证码错误！');
            setTimeout(function () {
                $app.dom.input_captcha.attr('data-content', "验证码为4位数字和字母的组合，请重新填写！").focus().select().popover('show');
            }, 150);
            return;
        }
    } else if ($app.login_type === LOGIN_TYPE_PASSWORD_OATH) {
        if (str_oath.length !== 6 || ('' + parseInt(str_oath)) !== str_oath) {
            $app.show_op_box('error', '身份验证器动态验证码错误！');
            setTimeout(function () {
                $app.dom.input_oath.attr('data-content', "身份验证器动态验证码为6位数字，请重新填写！").focus().select().popover('show');
            }, 150);
            return;
        }
    }

    $app.dom.btn_login.attr('disabled', 'disabled');
    $app.show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在进行身份认证，请稍候...');

    // 先判断一下captcha是否正确，如果不正确，拒绝登录
    if ($app.login_type === LOGIN_TYPE_PASSWORD_CAPTCHA) {
        $tp.ajax_post_json('/auth/verify-captcha', {captcha: str_captcha},
            function (ret) {
                if (ret.code === TPE_OK) {
                    // 验证成功
                    $app.hide_op_box();
                    $app.show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在登录TELEPORT，请稍候...');
                    $app.do_account_login(str_username, str_password, str_captcha, str_oath, is_remember);
                }
                else {
                    $app.hide_op_box();
                    $app.show_op_box('error', tp_error_msg(ret.code, ret.message));
                    $app.dom.captcha_image.attr('src', '/auth/captcha?' + Math.random());
                    $app.dom.input_captcha.focus().select().val('');
                }

                $app.dom.btn_login.removeAttr('disabled');
            },
            function () {
                $app.hide_op_box();
                $app.show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
                $app.dom.btn_login.removeAttr('disabled');
            }
        );
    } else {
        $app.do_account_login(str_username, str_password, str_captcha, str_oath, is_remember);
    }
};

$app.do_account_login = function (username, password, captcha, oath, is_remember) {
    var args = {type: $app.login_type, username: username, password: password, captcha: captcha, oath: oath, remember: is_remember};
    $tp.ajax_post_json('/auth/do-login', args,
        function (ret) {
            if (ret.code === TPE_OK) {
                window.location.href = $app.options.ref;
            } else {
                $app.hide_op_box();
                $app.show_op_box('error', '无法登录TELEPORT：' + tp_error_msg(ret.code, ret.message));
                console.log(ret);
            }

            $app.dom.btn_login.removeAttr('disabled');
        },
        function () {
            $app.hide_op_box();
            $app.show_op_box('error', '很抱歉，无法连接服务器！请稍后再试！');
            $app.dom.btn_login.removeAttr('disabled');
        }
    );
};

$app.on_screen_resize = function () {
    $('body').backgroundBlur('resize');
};

$app.init_blur_bg = function () {
    var img_id = Math.floor(Math.random() * (BLUR_BG_COUNT));
    $('body').backgroundBlur({
        imageURL: '/static/img/login/login-bg-' + img_id + '.png?' + Math.random(),
        blurAmount: 10,
        duration: 1000,
        imageClass: 'bg-blur',
        overlayClass: 'bg-blur-overlay'
    });

    setInterval($app._update_blur_bg, 20000);
};

$app._update_blur_bg = function () {
    var img_id = Math.floor(Math.random() * (BLUR_BG_COUNT));
    $('body').backgroundBlur('/static/img/login/login-bg-' + img_id + '.png?' + Math.random());
};

$app.init_slogan = function () {
    $app._update_slogan();
    setInterval($app._update_slogan, 8000);
};

$app._update_slogan = function () {
    var msg_id = Math.floor(Math.random() * SLOGAN.length);
    $app.dom.slogan.fadeOut(1000, function () {
        $(this).html(SLOGAN[msg_id]).fadeIn(1000);
    });
};
