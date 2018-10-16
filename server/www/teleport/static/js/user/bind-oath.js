"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        // title: $('#title'),
        // icon_bg: $('#icon-bg'),
        tp_time: $('#teleport-time')

        , op_message: $('#area-auth [data-field="message"]')

        , btn_show_oath_app: $('#btn-show-oath-app')
        , dlg_oath_app: $('#dlg-oath-app')

        , qrcode: {
            area: $('#area-qrcode')
            , name: $('#area-qrcode [data-field="name"]')
            , image: $('#area-qrcode [data-field="qrcode"]')
            , desc: $('#area-qrcode [data-field="desc"]')
        }

        , auth: {
            area: $('#area-auth')
            , input_username: $('#area-auth [data-field="input-username"]')
            , input_password: $('#area-auth [data-field="input-password"]')
            , btn_submit: $('#area-auth [data-field="btn-submit"]')
            , message: $('#area-auth [data-field="message"]')
        }

        , bind: {
            dlg: $('#dlg-bind-oath')
            , qrcode_img: $('#dlg-bind-oath [data-field="oath-secret-qrcode"]')
            , tmp_secret: $('#dlg-bind-oath [data-field="tmp-oath-secret"]')
            , input_oath_code: $('#dlg-bind-oath [data-field="oath-code"]')
            , btn_submit: $('#dlg-bind-oath [data-field="btn-submit"]')
            , message: $('#dlg-bind-oath [data-field="message"]')
        }
    };

    $app.tp_time = 0;
    $app.dom.op_message = $app.dom.auth.message;
    $app.dom.bind.dlg.on('shown.bs.modal', function () {
        $app.dom.op_message = $app.dom.bind.message;
    });
    $app.dom.bind.dlg.on('hidden.bs.modal', function () {
        $app.dom.op_message = $app.dom.auth.message;
    });

    // $app.show_bind_dlg();

    // $app.dom.icon_bg.addClass('fa fa-crosshairs').css('color', '#8140f1');
    $app.dom.btn_show_oath_app.click(function () {
        $app.dom.dlg_oath_app.modal();
    });

    $('[data-switch]').click(function () {
        var n = $(this).attr('data-switch');
        console.log(n);

        var name, img, desc;
        if (n === 'g-ios-appstore') {
            name = '<i class="fab fa-apple"></i> 谷歌身份验证器';
            img = 'img/qrcode/google-oath-appstore.png';
            desc = '适用于 iOS，从 Apple Store 安装';
        } else if (n === 'g-android-baidu') {
            name = '<i class="fab fa-android"></i> 谷歌身份验证器';
            img = 'img/qrcode/google-oath-baidu.png';
            desc = '适用于 Android，从百度手机助手安装';
        } else if (n === 'g-android-google') {
            name = '<i class="fab fa-android"></i> 谷歌身份验证器';
            img = 'img/qrcode/google-oath-googleplay.png';
            desc = '适用于 Android，从 Google Play 安装';
        } else if (n === 'mi-ios-appstore') {
            name = '<i class="fab fa-apple"></i> 小米安全令牌';
            img = 'img/qrcode/xiaomi-oath-appstore.png';
            desc = '适用于 iOS，从 Apple Store 安装';
        } else if (n === 'mi-android-mi') {
            name = '<i class="fab fa-android"></i> 小米安全令牌';
            img = 'img/qrcode/xiaomi-oath-xiaomi.png';
            desc = '适用于 Android，从小米应用商店安装';
        } else if (n === 'wechat') {
            name = '<i class="fab fa-wexin"></i> 微信 · 小程序';
            img = 'img/qrcode/wechat.png';
            desc = '适用于 iOS/Android，在微信小程序中搜索“二次验证码”即可';
        }

        $app.dom.qrcode.name.html(name);
        $app.dom.qrcode.image.attr('src', '/static/' + img);
        $app.dom.qrcode.desc.html(desc);
        if (!$app.dom.qrcode.image.hasClass('selected'))
            $app.dom.qrcode.image.addClass('selected');
    });

    $app.dom.auth.btn_submit.click(function () {
        $app.on_auth_user();
    });

    $app.dom.auth.input_username.keydown(function (event) {
        if (event.which === 13) {
            $app.dom.auth.input_password.focus();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });
    $app.dom.auth.input_password.keydown(function (event) {
        if (event.which === 13) {
            $app.on_auth_user();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });

    $app.dom.bind.input_oath_code.keydown(function (event) {
        if (event.which === 13) {
            $app.on_save();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });

    $app.dom.bind.btn_submit.click(function(){
        $app.on_save();
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

$app.hide_op_box = function () {
    $app.dom.op_message.hide();
};

$app.show_op_box = function (op_type, op_msg) {
    $app.dom.op_message.html(op_msg);
    $app.dom.op_message.removeClass().addClass('op_box op_' + op_type);
    $app.dom.op_message.show();
};

$app.on_auth_user = function () {
    $app.hide_op_box();
    var str_username = $app.dom.auth.input_username.val();
    var str_password = $app.dom.auth.input_password.val();

    if (str_username.length === 0) {
        $app.show_op_box('error', '用户名未填写！');
        $app.dom.auth.input_username.attr('data-content', "请输入您的用户名！").focus().popover('show');
        return;
    }

    if (str_password.length === 0) {
        $app.show_op_box('error', '密码未填写！');
        $app.dom.auth.input_password.attr('data-content', "请输入您的密码！").focus().popover('show');
        return;
    }

    $app.dom.auth.btn_submit.attr('disabled', 'disabled');
    $tp.ajax_post_json('/user/verify-user', {username: str_username, password: str_password, check_bind_oath: true},
        function (ret) {
            $app.dom.auth.btn_submit.removeAttr('disabled');
            if (ret.code === TPE_OK) {
                // 验证成功
                $app.hide_op_box();

                // 显示绑定对话框
                $app.show_bind_dlg();
            }
            else {
                $app.hide_op_box();
                $app.show_op_box('error', tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $app.hide_op_box();
            $app.show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
            $app.dom.auth.btn_submit.removeAttr('disabled');
        }
    );
};

$app.show_bind_dlg = function () {
    var str_username = $app.dom.auth.input_username.val();
    $tp.ajax_post_json('/user/gen-oath-secret', {},
        function (ret) {
            if (ret.code === TPE_OK) {
                $app.dom.bind.qrcode_img.attr('src', '/user/oath-secret-qrcode?u=' + str_username + '&rnd=' + Math.random());
                $app.dom.bind.tmp_secret.text(ret.data.tmp_oath_secret);
                $app.dom.bind.dlg.modal({backdrop: 'static'});
            } else {
                $tp.notify_error('无法绑定身份验证器：' + tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $tp.notify_error('网路故障，无法连接到服务器！');
        }
    );
};

$app.on_save = function () {
    var str_username = $app.dom.auth.input_username.val();
    var str_password = $app.dom.auth.input_password.val();
    var oath_code = $app.dom.bind.input_oath_code.val();

    if (oath_code.length === 0) {
        $app.show_op_box('error', '动态验证码未填写！');
        $app.dom.bind.input_oath_code.attr('data-content', "请输入动态验证码！").focus().popover('show');
        return;
    }
    if (oath_code.length !== 6) {
        $app.show_op_box('error', '动态验证码错误！');
        $app.dom.bind.input_oath_code.attr('data-content', "动态验证码为 6 位数字！").focus().popover('show');
        return;
    }

    $tp.ajax_post_json('/user/do-bind-oath', {username: str_username, password: str_password, oath_code: oath_code},
        function (ret) {
            $app.dom.auth.btn_submit.removeAttr('disabled');
            if (ret.code === TPE_OK) {
                // 验证成功
                $app.hide_op_box();
                $app.show_op_box('success', '绑定成功，正在转到登录界面！');
                setTimeout(function(){
                    window.location.href = '/';
                }, 3000);
            }
            else {
                $app.hide_op_box();
                $app.show_op_box('error', tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $app.hide_op_box();
            $app.show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
            $app.dom.auth.btn_submit.removeAttr('disabled');
        }
    );
};

// $app.on_send_find_password_email = function () {
//     $app.hide_op_box();
//     var str_username = $app.dom.find.input_username.val();
//     var str_email = $app.dom.find.input_email.val();
//     var str_captcha = $app.dom.find.input_captcha.val();
//
//     if (str_username.length === 0) {
//         $app.show_op_box('error', '账号未填写！');
//         $app.dom.find.input_username.attr('data-content', "请填写您的账号！").focus().popover('show');
//         return;
//     }
//
//     if (str_email.length === 0) {
//         $app.show_op_box('error', '电子邮件地址未填写！');
//         $app.dom.find.input_email.attr('data-content', "请填写您的电子邮件地址！").focus().popover('show');
//         return;
//     }
//
//     if (!tp_is_email(str_email)) {
//         $app.show_op_box('error', '无效的电子邮件地址！');
//         $app.dom.find.input_email.attr('data-content', "请检查输入的电子邮件地址！").focus().popover('show');
//         return;
//     }
//
//     if (str_captcha.length !== 4) {
//         $app.show_op_box('error', '验证码错误！');
//         $app.dom.find.input_captcha.attr('data-content', "验证码为4位数字和字母的组合，请重新填写！").focus().select().popover('show');
//         return;
//     }
//
//     $app.dom.find.btn_submit.attr('disabled', 'disabled');
//     $tp.ajax_post_json('/auth/verify-captcha', {captcha: str_captcha},
//         function (ret) {
//             if (ret.code === TPE_OK) {
//                 // 验证成功
//                 $app.hide_op_box();
//                 $app.show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在发送密码重置确认函，请稍候...');
//                 $app.do_send_reset_email(str_username, str_email, str_captcha);
//             }
//             else {
//                 $app.dom.find.btn_submit.removeAttr('disabled');
//                 $app.hide_op_box();
//                 $app.show_op_box('error', tp_error_msg(ret.code, ret.message));
//                 $app.dom.captcha_image.attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
//                 $app.dom.input_captcha.focus().select().val('');
//             }
//         },
//         function () {
//             $app.hide_op_box();
//             $app.show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
//             $app.dom.find.btn_submit.removeAttr('disabled');
//         }
//     );
// };
//
// $app.do_send_reset_email = function (str_username, str_email, str_captcha) {
//     $tp.ajax_post_json('/user/do-reset-password', {
//             mode: 3,
//             username: str_username,
//             email: str_email,
//             captcha: str_captcha
//         },
//         function (ret) {
//             if (ret.code === TPE_OK) {
//                 $app.dom.find.btn_submit.slideUp('fast');
//                 $app.show_op_box('success', '密码重置确认函已发送，请注意查收！');
//             } else {
//                 $app.dom.find.btn_submit.removeAttr('disabled');
//                 $app.hide_op_box();
//                 var msg = '';
//                 if (ret.code === TPE_NOT_EXISTS)
//                     msg = tp_error_msg(ret.code, '用户不存在，请检查输入的用户和电子邮件地址是否匹配！');
//                 else
//                     msg = tp_error_msg(ret.code, ret.message);
//                 $app.show_op_box('error', msg);
//             }
//         },
//         function () {
//             $app.dom.find.btn_submit.removeAttr('disabled');
//             $app.hide_op_box();
//             $app.show_op_box('error', '网络故障，密码重置确认函发送失败！');
//         },
//         15000
//     );
// };
//
// $app.on_set_new_password = function () {
//     $app.hide_op_box();
//     var str_password = $app.dom.set_password.input_password.val();
//
//     if (str_password.length === 0) {
//         $app.show_op_box('error', '密码未填写！');
//         $app.dom.set_password.input_password.attr('data-content', "请设置您的新密码！").focus().popover('show');
//         return;
//     }
//
//     if ($app.options.force_strong) {
//         if (!tp_check_strong_password(str_password)) {
//             $app.show_op_box('error', tp_error_msg(TPE_FAILED, '抱歉，不能使用弱密码！'));
//             $app.dom.set_password.input_password.attr('data-content', "请设置强密码：至少8位，必须包含大写字母、小写字母以及数字！").focus().popover('show');
//             return;
//         }
//     }
//
//     $tp.ajax_post_json('/user/do-reset-password', {
//             mode: 4,
//             token: $app.options.token,
//             password: str_password
//         },
//         function (ret) {
//             $app.dom.find.btn_submit.removeAttr('disabled');
//             if (ret.code === TPE_OK) {
//                 $app.show_op_box('success', '密码已重置，正在转到登录界面！');
//                 setTimeout(function () {
//                     window.location.href = '/';
//                 }, 2000);
//             } else {
//                 var msg = '';
//                 if (ret.code === TPE_NOT_EXISTS)
//                     msg = tp_error_msg(ret.code, '无效的密码重置链接！');
//                 else
//                     msg = tp_error_msg(ret.code, ret.message);
//                 $app.show_op_box('error', msg);
//             }
//         },
//         function () {
//             $app.dom.find.btn_submit.removeAttr('disabled');
//             $app.hide_op_box();
//             $app.show_op_box('error', '网络故障，密码重置失败！');
//         }
//     );
// };


