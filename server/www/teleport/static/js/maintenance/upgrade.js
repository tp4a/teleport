"use strict";

$app.on_init = function (cb_stack, cb_args) {
    $app.dom = {
        btn_upgrade: $('#btn-upgrade'),
        steps_detail: $('#steps-detail'),
        // db_info: $('#db-info'),
        // account: $('#sysadmin-account'),
        // email: $('#sysadmin-email'),
        // password: $('#password'),
        // password2: $('#password-again'),
        message: $('#message'),
        step2: $('#step2')
    };

    $app._make_info = function (key, value) {
        return '<tr><td class="key">' + key + '：</td><td class="value">' + value + '</td></tr>';
    };

    // var html = [];
    // if ($app.options.db.type === DB_TYPE_SQLITE) {
    //     html.push($app._make_info('数据库类型', 'SQLite'));
    //     html.push($app._make_info('数据库文件', $app.options.db.sqlite_file));
    // } else if ($app.options.db.type === DB_TYPE_MYSQL) {
    //     html.push($app._make_info('数据库类型', 'MySQL'));
    //     html.push($app._make_info('MySQL主机', $app.options.db.mysql_host));
    //     html.push($app._make_info('MySQL端口', $app.options.db.mysql_port));
    //     html.push($app._make_info('数据库名称', $app.options.db.mysql_db));
    //     html.push($app._make_info('用户名', $app.options.db.mysql_user));
    //
    //     var _t = [];
    //     _t.push('<div class="alert alert-warning">');
    //     _t.push('<i class="fas fa-exclamation-triangle"></i> 注意：请确保您在执行后续创建操作之前，已经在MySQL中使用 <span class="bold">UTF8字符集</span> 创建了库“');
    //     _t.push($app.options.db.mysql_db);
    //     _t.push('”，并且用户“');
    //     _t.push($app.options.db.mysql_user);
    //     _t.push('”拥有在此库创建表的权限！');
    //     _t.push('</div>');
    //     $app.dom.db_info.after(_t.join(''));
    // } else {
    //     html.push($app._make_info('数据库类型', '<span class="error">未知的数据库类型，请检查您的配置文件！</span>'));
    //     $app.dom.btn_upgrade.attr('disabled', 'disabled').hide();
    // }
    // $app.dom.db_info.append(html.join(''));

    $app.hide_op_box = function () {
        $app.dom.message.hide();
    };

    $app.show_op_box = function (op_type, op_msg) {
        $app.dom.message.html(op_msg);
        $app.dom.message.removeClass().addClass('op_box op_' + op_type);
        $app.dom.message.show();
    };

    $app.dom.btn_upgrade.click(function () {
        // var str_account = $app.dom.account.val();
        // var str_email = $app.dom.email.val();
        // var str_password = $app.dom.password.val();
        // var str_password2 = $app.dom.password2.val();
        //
        // if (str_account.length === 0) {
        //     $app.show_op_box('error', '请填写系统管理员登录账号名称！');
        //     $app.dom.account.focus();
        //     return;
        // }
        // if (str_email.length === 0) {
        //     $app.show_op_box('error', '请填写系统管理员的电子邮件地址！');
        //     $app.dom.email.focus();
        //     return;
        // }
        // if (!tp_is_email(str_email)) {
        //     $app.show_op_box('error', '电子邮件地址格式错啦，你会收不到邮件的！');
        //     $app.dom.email.focus();
        //     return;
        // }
        // if (str_password.length === 0) {
        //     $app.show_op_box('error', '请设置系统管理员登录密码！');
        //     $app.dom.password.focus();
        //     return;
        // }
        // if (str_password2.length === 0) {
        //     $app.show_op_box('error', '请再次输入系统管理员登录密码！');
        //     $app.dom.password.focus();
        //     return;
        // }
        // if (str_password !== str_password2) {
        //     $app.show_op_box('error', '两次输入的密码不一致！');
        //     $app.dom.password2.focus().select();
        //     return;
        // }

        $app.dom.btn_upgrade.attr('disabled', 'disabled').hide();
        $app.hide_op_box();
        $app.dom.steps_detail.show();

        $tp.ajax_post_json('/maintenance/rpc', {cmd: 'upgrade_db'},
            function (ret) {
                if (ret.code === TPE_OK) {

                    var cb_stack = CALLBACK_STACK.create();
                    cb_stack
                        .add_delay(500, $app.get_task_ret, {task_id: ret.data.task_id})
                        .exec();
                }

            },
            function () {
//                $app.show_message('error', '无法连接到服务器！');
                $app.show_op_box('error', '无法连接到服务器！');
            }
        );

    });

    $app.get_task_ret = function (cb_stack, cb_args) {
        var task_id = cb_args.task_id || 0;
        if (task_id === 0) {
            console.log('task-id', task_id);
            return;
        }

        $tp.ajax_post_json('/maintenance/rpc', {cmd: 'get_task_ret', 'tid': task_id},
            function (ret) {
                if (ret.code === TPE_OK) {

                    // show step progress.
                    var all_ok = true;
                    var steps = ret.data.steps;
                    $app.dom.steps_detail.empty();

                    var html = [];
                    var icon_class = '';
                    var err_class = '';
                    for (var i = 0; i < steps.length; ++i) {
                        if (steps[i].stat === 0)
                            icon_class = 'fa-check';
                        else
                            icon_class = 'fa-cog fa-spin';

                        if (steps[i].code !== 0) {
                            icon_class = 'fa-exclamation-circle';
                            err_class = ' class="error"';
                            steps[i].msg += ' 失败！';
                            all_ok = false;
                        }
                        else {
                            err_class = '';
                        }

                        html.push('<p');
                        html.push(err_class);
                        html.push('><i class="fa ');
                        html.push(icon_class);
                        html.push('"></i> ');
                        html.push(steps[i].msg);
                        html.push('</p>')
                    }
                    $app.dom.steps_detail.html(html.join(''));
                    $('html').animate({scrollTop: $(document).height()}, 300);

                    if (!ret.data.running) {
                        if (all_ok) {

                            $tp.ajax_post_json('/auth/do-logout', {},
                                function () {
                                },
                                function () {
                                }
                            );

                            $app.dom.step2.show('fast', function () {
                                // 确保页面滚动到最低端，使得下一步提示能够被看到。
                                $('html').animate({scrollTop: $(document).height()}, 300);
                            });
                        }
                        return;
                    }

                    cb_stack
                        .add_delay(500, $app.get_task_ret, {task_id: task_id})
                        .exec();
                }

            },
            function () {
                $app.show_op_box('error', '无法连接到服务器！');
            }
        );

    };

    cb_stack.exec();
};

























        ywl.on_init = function (cb_stack, cb_args) {
            ywl.dom = {
                btn_upgrade_db: $('#btn-upgrade-db'),
                steps_detail: $('#steps-detail')
            };

            ywl.dom.btn_upgrade_db.click(function () {

                ywl.dom.btn_upgrade_db.attr('disabled', 'disabled').hide();
                ywl.dom.steps_detail.show();

                console.log('upgrade-db-click');
                ywl.ajax_post_json('/maintenance/rpc', {cmd: 'upgrade_db'},
                        function (ret) {
                            console.log('upgrade-db:', ret);
                            if (ret.code === 0) {

                                var cb_stack = CALLBACK_STACK.create();
                                cb_stack
                                        .add(ywl.get_task_ret, {task_id: ret.data.task_id})
                                        .add(ywl.delay_exec, {delay_ms: 500})
                                        .exec();
                            }

                        },
                        function () {
                            ywl.show_message('error', '无法连接到服务器！');
                        }
                );

            });

            ywl.get_task_ret = function (cb_stack, cb_args) {
                var task_id = cb_args.task_id || 0;
                if (task_id === 0) {
                    console.log('task-id', task_id);
                    return;
                }

                ywl.ajax_post_json('/maintenance/rpc', {cmd: 'get_task_ret', 'tid': task_id},
                        function (ret) {
                            console.log('get_task_ret:', ret);
                            if (ret.code === 0) {

                                // show step progress.
                                var steps = ret.data.steps;
                                ywl.dom.steps_detail.empty();

                                var html = [];
                                var icon_class = '';
                                var err_class = '';
                                for(var i = 0; i < steps.length; ++i) {
                                    if(steps[i].code !== 0) {
                                        err_class = ' class="error"';
                                        icon_class = 'fa-times-circle';
                                    }
                                    else {
                                        err_class = '';
                                        icon_class = 'fa-check';
                                    }

                                    if(steps[i].stat === 0)
                                        ;//icon_class = 'fa-check';
                                    else
                                        icon_class = 'fa-cog fa-spin';

                                    html.push('<p');
                                    html.push(err_class);
                                    html.push('><i class="fa ');
                                    html.push(icon_class);
                                    html.push('"></i> ');
                                    html.push(steps[i].msg);
                                    html.push('</p>')
                                }
                                ywl.dom.steps_detail.html(html.join(''));


                                if (!ret.data.running) {
                                    $('#step2').show('fast');
                                    return;
                                }

                                cb_stack
                                        .add(ywl.get_task_ret, {task_id: task_id})
                                        .add(ywl.delay_exec, {delay_ms: 500})
                                        .exec();
                            }

                        },
                        function () {
                            ywl.show_message('error', '无法连接到服务器！');
                        }
                );

            };

            cb_stack.exec();
        };
