"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        title: $('#title'),
        icon_bg: $('#icon-bg'),

        err_area: $('#error-area'),
        err_message: $('#err-message'),
        err_actions: $('#err-actions'),

        find_password_area: $('#find-my-password'),
        username: $('#username'),
        email: $('#email'),
        captcha_image: $('#captcha-image'),
        captcha: $('#captcha'),
        btn_send_email: $('#btn-send-email'),
        send_result:$('#send-result'),

        password_area: $('#password-area')
    };

    $app.dom.captcha_image.click(function () {
        $(this).attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
        $app.dom.captcha.focus().val('');
    });

    $app.dom.btn_send_email.click(function() {
        $app.on_send_email();
    });

    $app.options.mode = 3;

    if ($app.options.mode === 1) {
        // show 'find-my-password' page
        $app.dom.title.text('重置密码');
        $app.dom.icon_bg.addClass('fa fa-search-plus').css('color', '#4366de');
        $app.dom.captcha_image.attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
        $app.dom.find_password_area.show();
        $app.dom.username.focus();
    } else if ($app.options.mode === 2) {
        // show 'password-expired' page
        $app.dom.icon_bg.addClass('fa fa-warning').css('color', '#ff6242');
        if ($app.options.code === TPE_NOT_EXISTS) {
            $app.dom.title.text('链接无效');
            $app.dom.err_message.html('当前使用的密码重置链接无效，可能已经因过期而被清除！密码重置链接仅在24小时内有效，请及时设置您的新密码！');
        } else if ($app.options.code === TPE_EXPIRED) {
            $app.dom.title.text('链接已过期');
            $app.dom.err_message.html('当前使用的密码重置链接已经过期！密码重置链接仅在24小时内有效，请及时设置您的新密码！');
        } else {
            $app.dom.title.text('更新密码');
        }
        $app.dom.err_area.show();
    } else if ($app.options.mode === 3) {
        // show 'set-new-password' page
        $app.dom.title.text('重置密码');
        $app.dom.icon_bg.addClass('fa fa-info-circle').css('color', '#357a3c');
        $app.dom.password_area.show();
    }

    cb_stack.exec();
};

$app.on_send_email = function() {

};
