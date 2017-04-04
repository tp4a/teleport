/*! ywl_assist v1.0.1, (c)2015 eomsoft.net */
"use strict";


ywl.create_assist = function () {
    var _assist = {};

    _assist.option_page_id = '';
    _assist.option_cache_type = [];
    _assist.option_cache_cookie = [];

    _assist.cache_data = {};
    _assist.cookie_data = {};

    _assist.url = 'http://127.0.0.1:50021';
    _assist.jsonp_callback = 'callback';
    _assist.exists = false;
    _assist.ver_major = 0;
    _assist.ver_minor = 0;
    _assist.is_logon = false;
    _assist.ticket = '';
    _assist.user_id = 0;
    _assist.user_name = '';

    _assist.init = function (cb_stack, cb_args) {
        _assist._make_message_box();

        _assist.option_page_id = cb_args.page_id || '';
        _assist.option_cache_type = cb_args.cache_type || [];
        _assist.option_cache_cookie = cb_args.cookie || [];

        _assist.option_cache_cookie.push('host_group');
        _assist.option_cache_cookie.push('system_group');
        _assist.option_cache_cookie.push('app_group');
        _assist.option_cache_cookie.push('count_per_page');
        _assist.option_cache_cookie.push('show_online_host_only');

        if (_.isUndefined(_.find(_assist.option_cache_type, function (_type) {
                return _type == CACHE_TYPE_GROUP;
            }))) {
            _assist.option_cache_type.push(CACHE_TYPE_GROUP);
        }

        cb_stack
        //.add(_assist._init_load_cache)
        //.add(_assist._init_check_version)
        //.add(_assist.check)
            .exec();
    };

    _assist._make_message_box = function () {
        var _html = [
            '<div class="modal fade" id="dialog-need-ywl-assist" tabindex="-1" role="dialog">',
            '<div class="modal-dialog" role="document">',
            '<div class="modal-content">',
            '<div class="modal-header">',
            '<h4 class="modal-title">未检测到TELEPORT助手！</h4>',
            '</div>',
            '<div class="modal-body">',
            '<div class="alert alert-info" role="alert">',
            '<p>需要TELEPORT助手来辅助远程连接，请确认本机运行了TELEPORT助手！</p>',
            '</div>',
            '<p>如果您尚未运行TELEPORT助手，请 <a href="http://teleport.eomsoft.net/download" target="_blank"><strong>下载最新版TELEPORT助手</strong></a> 并安装。一旦运行了TELEPORT助手，即可重新进行远程连接。</p>',
//			'<p>如果您已经运行了TELEPORT助手，仍然出现此提示，请 <a href="https://127.0.0.1:50022/" target="_blank"><strong>诊断TELEPORT助手状态</strong></a>，如果浏览器提示连接不安全，请添加安全例外，确保可以与TELEPORT正常通讯！</p>',
//			'<ul>',
//			'<li>Chrome浏览器：点击“高级”，然后点击“<strong>继续前往127.0.0.1</strong>”。</li>',
//			'<li>Firefox浏览器：点击“高级”，然后点击“添加例外”，然后点击“确认安全例外”。</li>',
//			'</ul>',
//			'<p>如果诊断显示TELEPORT助手工作正常，但仍然出现此提示，请与我们联系，谢谢。</p>',
            '</div>',
            '<div class="modal-footer">',
            '<button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-close fa-fw"></i> 我知道了</button>',
            '</div>',
            '</div>',
            '</div>',
            '</div>',
            '</div>'
        ].join('\n');
        $('body').append($(_html));
    };

    _assist.ajax_error = function (cb_stack, cb_args) {
        var error = cb_args.error || null;
        if (!_.isNull(error)) {
            log.e('assist-ajax-error:', error);
        }

        // check if assist not exists or user not login.

        cb_stack.add(function (cb_stack) {
            if (!_assist.exists) {
                _assist.alert_assist_not_found();
            } else if (!_assist.is_logon) {
                console.warn('[assist] user not login.');
                cb_stack.exec();
            }
        });

        cb_stack.add(_assist.check);
        cb_stack.exec();
    };

    _assist.alert_assist_not_found = function () {
        log.v('alert_assist_not_found');
//        $('#dialog-need-ywl-assist').modal({backdrop: 'static', keyboard: false});
		$('#dialog-need-ywl-assist').modal();
    };

    _assist._init_check_version = function (cb_stack) {

        //_assist.exists = true;

        if (!_assist.exists) {
            _assist.alert_assist_not_found();
        } else {
            if (!_assist.is_logon) {
                //log.v(window.location.pathname);
                //var _url = window.location.href.split('?', 1);
                //log.v(_url);
                if (window.location.pathname == '/auth/login') {
                    cb_stack.exec();
                } else {
                    window.location.href = '/auth/login?ref=' + window.location.href;
                }
            } else {
                cb_stack.exec();
            }
        }
    };

    _assist.check = function (cb_stack) {
        $.ajax({
            type: 'GET',
            timeout: 1000,
            url: _assist.url + '/check',
            jsonp: _assist.jsonp_callback,
            data: {},
            dataType: 'jsonp',
            success: function (ret) {

                if (ret.code == 0) {
                    _assist.exists = true;
                    _assist.ver_major = ret.data.ver.major;
                    _assist.ver_minor = ret.data.ver.minor;

                    if (ret.data.auth.logon) {
                        _assist.is_logon = true;
                        _assist.ticket = ret.data.auth.ticket;
                        _assist.user_id = ret.data.auth.id;
                        _assist.user_name = ret.data.auth.name;
                    } else {
                        _assist.is_logon = false;
                    }
                }

                var arg = ret.data;
                _assist.exists = true;
                _assist.ver_major = arg.major;
                _assist.ver_minor = arg.minor;
                cb_stack.exec();
            },
            error: function () {
                _assist.exists = false;
                cb_stack.exec();
                //_assist.alert_assist_not_found();
            }
        });
    };

//    _assist.logout = function (cb_stack) {
//        $.ajax({
//            type: 'GET',
//            timeout: 1000,
//            url: _assist.url + '/logout',
//            jsonp: _assist.jsonp_callback,
//            data: {},
//            dataType: 'jsonp',
//            success: function (ret) {
//                cb_stack.exec();
//            },
//            error: function () {
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.do_task = function (cb_stack, cb_args) {
//
//        var is_multi_step = cb_args.is_multi_step || 0;
//        var host_id = cb_args.host_id || 0;
//        var cmd = cb_args.cmd || 0;
//        var args = cb_args.args || {};
//        var cb_exec_arg = cb_args.cb_exec_arg || null;
//
//        var cb_exec = cb_args.cb_exec || null;
//        var cb_error = cb_args.cb_error || null;
//
//
//        if ((!_.isNull(cb_exec) && !_.isFunction(cb_exec)) ||
//            (!_.isNull(cb_error) && !_.isFunction(cb_error))
//        ) {
//            log.e('Invalid Param.');
//            return;
//        }
//
//        var args_ = encodeURIComponent(JSON.stringify(args));
//        log.v('do_task: args:', args_);
//
//
//        $.ajax({
//            type: 'GET',
//            timeout: 2000,
//            url: 'http://127.0.0.1:50031/do_task/' + is_multi_step + '/' + host_id + '/' + cmd + '?arg=' + args_,
//            jsonp: _assist.jsonp_callback,
//            //data: {arg: args_},
//            dataType: 'jsonp',
//            success: function (ret) {
//                log.v('do task return:', ret);
//                if (ret.code != 0) {
//                    log.e('load failed. maybe you not login.');
//                    cb_stack.exec({});
//                } else {
//                    var task_id = ret.data.task_id;
//                    if (cb_stack != null) {
//                        cb_stack.add(_assist.get_task_ret, {task_id: task_id, cb_exec: cb_exec, cb_exec_arg: cb_exec_arg, cb_error: cb_error});
//                        cb_stack.add(ywl.delay_exec, {delay_ms: 500});
//
//                        cb_stack.exec();
//                    }
//                }
//            },
//            error: function (jqXhr, error, e) {
//                log.e('do task failed.');
//                _assist.ajax_error(cb_stack, {error: error});
//                //cb_stack.exec([]);
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.do_task_time_out = function (cb_stack, cb_args, time_out) {
//
//        var is_multi_step = cb_args.is_multi_step || 0;
//        var host_id = cb_args.host_id || 0;
//        var cmd = cb_args.cmd || 0;
//        var args = cb_args.args || {};
//        var cb_exec = cb_args.cb_exec || null;
//        var cb_error = cb_args.cb_error || null;
//
//        if ((!_.isNull(cb_exec) && !_.isFunction(cb_exec)) ||
//            (!_.isNull(cb_error) && !_.isFunction(cb_error))
//        ) {
//            log.e('Invalid Param.');
//            return;
//        }
//
//        var args_ = encodeURIComponent(JSON.stringify(args));
//        log.v('do_task: args:', args_);
//
//
//        $.ajax({
//            type: 'GET',
//            timeout: time_out,
//            url: 'http://127.0.0.1:50031/do_task/' + is_multi_step + '/' + host_id + '/' + cmd + '?arg=' + args_,
//            jsonp: _assist.jsonp_callback,
//            //data: {arg: args_},
//            dataType: 'jsonp',
//            success: function (ret) {
//                log.v('do task return:', ret);
//                if (ret.code != 0) {
//                    log.e('load failed. maybe you not login.');
//                    cb_stack.exec({});
//                } else {
//                    var task_id = ret.data.task_id;
//                    if (cb_stack != null) {
//                        cb_stack.add(_assist.get_task_ret_time_out, {task_id: task_id, time_out: time_out, cb_exec: cb_exec, cb_error: cb_error});
//                        cb_stack.add(ywl.delay_exec, {delay_ms: 500});
//
//                        cb_stack.exec();
//                    }
//                }
//            },
//            //error: function () {
//            //	log.e('do task ret failed. maybe assist not start.');
//            //	//cb_stack.exec([]);
//            //	_assist.alert_assist_not_found();
//            //}
//            error: function (jqXhr, error, e) {
//                log.e('do task with timeout failed.');
//                _assist.ajax_error(cb_stack, {error: error});
//                //cb_stack.exec([]);
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.get_task_ret = function (cb_stack, cb_args) {
//
//        var task_id = cb_args.task_id || 0;
//        var cb_exec = cb_args.cb_exec || null;
//        var cb_error = cb_args.cb_error || null;
//        var cb_exec_arg = cb_args.cb_exec_arg || null;
//        $.ajax({
//            type: 'GET',
//            timeout: 2000,
//            url: 'http://127.0.0.1:50031/get_task_ret/' + task_id,
//            jsonp: _assist.jsonp_callback,
//            data: {},
//            dataType: 'jsonp',
//            success: function (ret) {
//                //log.v('get task ret, status:', ret.data.task_status, ret);
//
//                if (ret.code != 0) {
//                    if (_.isFunction(cb_error)) {
//                        cb_error(cb_stack, {err_code: ret.code});
//                    } else {
//                        log.e('load failed. maybe you not login.');
//                        //cb_stack.exec({});
//                        ywl.notify_error('执行本地任务时发生错误，错误码：' + ret.code + '。');
//                    }
//                    //log.e('load failed. maybe you not login.');
//                    //cb_stack.exec({});
//                } else {
//                    //log.v('task-status:', ret.data.task_status);
//                    // 如果返回值为“尚未执行完成”，那么就将get_task_ret加入堆栈，继续调用。
//
//                    if (ret.data.task_status != 4) {
//                        cb_stack
//                            .add(_assist.get_task_ret, cb_args)
//                            .add(ywl.delay_exec, {delay_ms: 500});
//
//                        if (_.isFunction(cb_exec)) {
//                            cb_exec(cb_stack, cb_exec_arg, {data: ret.data});
//                        } else {
//                            cb_stack.exec();
//                        }
//                    } else {
//                        cb_stack.exec(ret.data);
//                    }
//                }
//            },
//            error: function (jqXhr, error, e) {
//                log.e('get task result failed.');
//                _assist.ajax_error(cb_stack, {error: error});
//                //cb_stack.exec([]);
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.get_task_ret_time_out = function (cb_stack, cb_args) {
//
//        var task_id = cb_args.task_id || 0;
//        var time_out = cb_args.time_out || 2000;
//        var cb_exec = cb_args.cb_exec || null;
//        var cb_error = cb_args.cb_error || null;
//
//        $.ajax({
//            type: 'GET',
//            timeout: time_out,
//            url: 'http://127.0.0.1:50031/get_task_ret/' + task_id,
//            jsonp: _assist.jsonp_callback,
//            data: {},
//            dataType: 'jsonp',
//            success: function (ret) {
//                log.v('get task ret:', ret);
//
//                if (ret.code != 0) {
//                    if (_.isFunction(cb_error)) {
//                        cb_error(cb_stack, {err_code: ret.code});
//                    } else {
//                        log.e('load failed. maybe you not login.');
//                        //cb_stack.exec({});
//                        ywl.notify_error('执行本地任务时发生错误，错误码：' + ret.code + '。');
//                    }
//                } else {
//                    log.v('task-status:', ret.data.task_status);
//                    // 如果返回值为“尚未执行完成”，那么就将get_task_ret加入堆栈，继续调用。
//
//                    if (ret.data.task_status != 4) {
//                        cb_stack
//                            .add(_assist.get_task_ret_time_out, cb_args)
//                            .add(ywl.delay_exec, {delay_ms: 500});
//
//                        if (_.isFunction(cb_exec)) {
//                            cb_exec(cb_stack, {data: ret.data});
//                        } else {
//                            cb_stack.exec();
//                        }
//                    } else {
//                        cb_stack.exec(ret.data);
//                    }
//                }
//            },
//            //error: function () {
//            //	log.e('get task ret failed. maybe assist not start.');
//            //	//cb_stack.exec([]);
//            //	_assist.alert_assist_not_found();
//            //}
//            error: function (jqXhr, error, e) {
//                log.e('get task result with timeout failed.');
//                _assist.ajax_error(cb_stack, {error: error});
//                //cb_stack.exec([]);
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.select_local_path = function (cb_stack, cb_args) {
//        var arg = cb_args.args || {};
//        arg = encodeURIComponent(JSON.stringify(arg));
//        log.v('select_local_path: args:', arg);
//
//        $.ajax({
//            type: 'GET',
//            //timeout: 1000,
//            url: _assist.url + '/select_path?arg=' + arg,
//            jsonp: _assist.jsonp_callback,
//            //data: _args,
//            dataType: 'jsonp',
//            success: function (ret) {
//                if (ret.code == 0) {
//                    log.v('select-local-file return:', ret.data);
//                    cb_stack.exec(ret.data);
//                }
//
//            },
//            //error: function () {
//            //	//self.alert_assist_not_found();
//            //	log.e('select-local-file failed');
//            //}
//            error: function (jqXhr, error, e) {
//                log.e('select local path failed.');
//                _assist.ajax_error(cb_stack, {error: error});
//                //cb_stack.exec([]);
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.read_local_file = function (cb_stack, cb_args) {
//        var arg = cb_args.args || {};
//        arg = encodeURIComponent(JSON.stringify(arg));
//        log.v('read_local_file: args:', arg);
//
//        $.ajax({
//            type: 'GET',
//            //timeout: 1000,
//            url: _assist.url + '/read_local_file?arg=' + arg,
//            jsonp: _assist.jsonp_callback,
//            //data: _args,
//            dataType: 'jsonp',
//            success: function (ret) {
//                if (ret.code == 0) {
//                    log.v('read_local_file return:', ret.data);
//                    cb_stack.exec(ret.data);
//                }
//
//            },
//            //error: function () {
//            //	//self.alert_assist_not_found();
//            //	log.e('read_local_file failed');
//            //}
//            error: function (jqXhr, error, e) {
//                log.e('read local file failed.');
//                _assist.ajax_error(cb_stack, {error: error});
//                //cb_stack.exec([]);
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.get_file_task_list = function (cb_stack, cb_args) {
//        var arg = cb_args.args || {};
//        arg = encodeURIComponent(JSON.stringify(arg));
//        log.v('select_local_path: args:', arg);
//
//        $.ajax({
//            type: 'GET',
//            timeout: 0,
//            url: _assist.url + '/get_file_task_list?arg=' + arg,
//            jsonp: _assist.jsonp_callback,
//            //data: _args,
//            dataType: 'jsonp',
//            success: function (ret) {
//                if (ret.code == 0) {
//                    log.v('select-local-file return:', ret.data);
//                    cb_stack.exec(ret.data);
//                }
//            },
//            //error: function () {
//            //	log.e('select-local-file failed');
//            //}
//            error: function (jqXhr, error, e) {
//                log.e('get file task list failed.');
//                _assist.ajax_error(cb_stack, {error: error});
//                //cb_stack.exec([]);
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.jsonp = function (cb_stack, cb_args) {
//        var _timeout = _.isUndefined(cb_args.timeout) ? 1000 : cb_args.timeout;// cb_args.timeout || 1000;
//        var _uri = cb_args.uri;
//        var _retry = cb_args.retry || false;
//        var _retry_interval = cb_args.retry_interval || 5000;
//        var _args = cb_args.args || {};
//        _args = encodeURIComponent(JSON.stringify(_args));
//
//        $.ajax({
//            type: 'GET',
//            timeout: _timeout,
//            url: _assist.url + _uri + '?arg=' + _args,
//            jsonp: _assist.jsonp_callback,
//            dataType: 'jsonp',
//            success: function (ret) {
//                //log.v('ajax_get_jsonp return:', ret);
//                cb_stack.exec(ret)
//            },
//            error: function (xhr, error) {
//                // if (xhr.status == 404)
//
//                // 可能此时assist关停了，我们等待一会儿再重试
//                if (_retry) {
//                    cb_stack
//                        .add(_assist.jsonp, cb_args)
//                        .add(ywl.delay_exec, {delay_ms: _retry_interval})
//                        .exec();
//                }
//            }
//        });
//    };
//
//    _assist.local_task = function (cb_stack, cb_args) {
//        var timeout = cb_args.timeout || 1000 * 5;
//        var cmd = cb_args.cmd || 0;
//        var args = cb_args.args || {};
//        var cb_exec_arg = cb_args.cb_exec_arg || null;
//        var cb_exec = cb_args.cb_exec || null;
//        var cb_error = cb_args.cb_error || null;
//
//        if ((!_.isNull(cb_exec) && !_.isFunction(cb_exec)) ||
//            (!_.isNull(cb_error) && !_.isFunction(cb_error))
//        ) {
//            log.e('Invalid Param.');
//            return;
//        }
//
//        var args_ = encodeURIComponent(JSON.stringify(args));
//        log.v('local_task: args:', args_);
//        if (timeout === -1) {
//            timeout = 0;
//        }
//        $.ajax({
//            type: 'GET',
//            timeout: timeout,
//            url: 'http://127.0.0.1:50021/do_task/' + cmd + '?arg=' + args_,
//            jsonp: _assist.jsonp_callback,
//            //data: {arg: args_},
//            dataType: 'jsonp',
//            success: function (ret) {
//                log.v('local task return:', ret);
//                if (ret.code != 0) {
//                    log.e('load failed. maybe you not login.');
//                    //cb_stack.exec({});
//                } else {
//                    //var task_id = ret.data.task_id;
//                    if (cb_stack != null) {
//                        //cb_stack.add(_assist.local_task_ret, {task_id: task_id, cb_exec_arg:cb_exec_arg, cb_exec: cb_exec, cb_error: cb_error});
//                        //cb_stack.add(ywl.delay_exec, {delay_ms: 2000});
//                        cb_stack.exec();
//                    }
//                }
//            },
//            //error: function () {
//            //	log.e('do task ret failed. maybe assist not start.');
//            //	//cb_stack.exec([]);
//            //	_assist.alert_assist_not_found();
//            //}
//            error: function (jqXhr, error, e) {
//                log.e('do local task failed.');
//                _assist.ajax_error(cb_stack, {error: error});
//                //cb_stack.exec([]);
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.local_task_ret = function (cb_stack, cb_args) {
//        log.v('local_task_ret before send req.');
//
//        var task_id = cb_args.task_id || 0;
//        var cb_exec = cb_args.cb_exec || null;
//        var cb_error = cb_args.cb_error || null;
//        var cb_exec_arg = cb_args.cb_exec_arg || null;
//
//        $.ajax({
//            type: 'GET',
//            timeout: 0,
//            url: 'http://127.0.0.1:50021/get_ret/' + task_id,
//            jsonp: _assist.jsonp_callback,
//            //data: {},
//            dataType: 'jsonp',
//            success: function (ret) {
//                log.v('local task ret:', ret);
//
//                if (ret.code != 0) {
//                    if (_.isFunction(cb_error)) {
//                        cb_error(cb_stack, {err_code: ret.code});
//                    } else {
//                        log.e('load failed. maybe you not login.');
//                        ywl.notify_error('执行本地任务时发生错误，错误码：' + ret.code + '。');
//                    }
//                } else {
//                    log.v('task-status:', ret.data.status);
//                    // 如果返回值为“尚未执行完成”，那么就将local_task_ret加入堆栈，继续调用。
//
//                    // TODO: 只能通过轮询的方式进行吗？能否启动任务后立即去获取结果，设置一个超时
//                    // 如果超时了，则立即再次发送获取结果的请求，这样，一旦结果返回了，就会立即得到响应。
//
//                    if (ret.data.status != 4) {
//                        cb_stack
//                            .add(_assist.local_task_ret, cb_args)
//                            .add(ywl.delay_exec, {delay_ms: 2000});
//
//                        if (_.isFunction(cb_exec)) {
//                            cb_exec(cb_stack, cb_exec_arg, {data: ret.data});
//                        } else {
//                            cb_stack.exec();
//                        }
//                    } else {
//                        cb_stack.exec(ret.data);
//                    }
//                }
//            },
//            //error: function () {
//            //	log.e('get task ret failed. maybe assist not start.');
//            //	//cb_stack.exec([]);
//            //	_assist.alert_assist_not_found();
//            //}
//            error: function (jqXhr, error, e) {
//                log.e('get local task result failed.');
//                _assist.ajax_error(cb_stack, {error: error});
//                //cb_stack.exec([]);
//                //_assist.alert_assist_not_found();
//            }
//        });
//    };
//
//    _assist.start_event_handler = function (func_event_handler) {
//        // TODO: 使用Comet方式进行数据推送，避免页面总是处于加载状态
//        // 参考：http://www.bitscn.com/school/Javascript/201604/683480.html
//
//        var _internal_starter = function () {
//            _assist._event_last_index = 0;
//            var cb_stack = CALLBACK_STACK.create();
//
//
//            var chk_event = function (cb_stack, cb_args, ex_args) {
//                //log.v('wait-event return:', ex_args);
//
//                if (ex_args.code != 0) {
//                    // 除非格式不正确，否则不会执行到这里的
//                    log.e('can not communicate with assist.');
//                } else {
//                    func_event_handler(ex_args.data);
//
//                    if (ex_args.data.length == 0) {
//                        // no event.
//                    } else {
//                        _assist._event_last_index = ex_args.data[ex_args.data.length - 1].index;
//                        //log.v('got event. last event index:', _assist._event_last_index);
//                    }
//                }
//
//                cb_stack.add(chk_event);
//
//                var options = {
//                    timeout: 60000,
//                    uri: '/wait-event',
//                    retry: true,
//                    retry_interval: 5000,
//                    args: {idx: _assist._event_last_index}
//                };
//                _assist.jsonp(cb_stack, options);
//
//            };
//
//            cb_stack.add(chk_event);
//
//            var options = {
//                timeout: 60000,
//                uri: '/wait-event',
//                retry: true,
//                retry_interval: 5000,
//                args: {idx: 0}
//            };
//            _assist.jsonp(cb_stack, options);
//        };
//
//        // 暂时的，使用settimeout的方式来启动，可以避免页面总是处于加载状态
//        setTimeout(_internal_starter, 1);
//    };

    return _assist;
};

