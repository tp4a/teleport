"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        count_user: $('#count-user')
        , count_host: $('#count-host')
        , count_acc: $('#count-acc')
        , count_conn: $('#count-conn')
    };

    // refresh basic info every 1m.
    $app.load_basic_info();
    // refresh overload info every 5m.
    $app.load_overload_info();

    cb_stack.exec();
};

$app.load_basic_info = function () {
    $tp.ajax_post_json('/dashboard/do-get-basic', {},
        function (ret) {
            console.log(ret);
            if (ret.code === TPE_OK) {
                $app.dom.count_user.text(ret.data.count_user);
                $app.dom.count_host.text(ret.data.count_host);
                $app.dom.count_acc.text(ret.data.count_acc);
                $app.dom.count_conn.text(ret.data.count_conn);
            } else {
                console.log('do-get-basic failed：' + tp_error_msg(ret.code, ret.message));
            }

        },
        function () {
            console.log('can not connect to server.');
        }
    );

    setTimeout($app.load_basic_info, 60*1000);
};

$app.load_overload_info = function () {
};
