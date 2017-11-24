"use strict";

$tp.assist = {
    running: false,
    version: '',
    api_url: 'http://localhost:50022/api',
    teleport_ip: window.location.hostname
};

// $assist 是 $tp.assist 的别名，方便使用。
var $assist = $tp.assist;

$assist.init = function (cb_stack) {

    $assist._make_message_box();

    // var data = {};
    // var args_ = encodeURIComponent(JSON.stringify(data));
    $.ajax({
        type: 'GET',
        timeout: 3000,
        //url: 'http://localhost:50022/ts_get_version/' + args_,
        url: $assist.api_url + '/get_version',
        jsonp: 'callback',
        dataType: 'json',
        success: function (ret) {
            $assist.running = true;
            $assist.version = ret.version;

            if(_.isFunction($tp.assist_checked)) {
                $tp.assist_checked();
            }
            // if (version_compare()) {
            //     error_process(ret, func_success, func_error);
            // } else {
            //     func_error(ret, TPE_OLD_ASSIST, '助手版本太低，请<a style="color:#aaaaff;" target="_blank" href="http://teleport.eomsoft.net/download">下载最新版本</a>！');
            // }
        },
        error: function () {
            $assist.running = false;
            if(_.isFunction($tp.assist_checked)) {
                $tp.assist_checked();
            }
            // func_error({}, TPE_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
            // $tp.notify_error('无法连接到teleport助手，可能尚未启动！');
            // $assist.alert_assist_not_found();
            console.error('无法连接到teleport助手，可能其尚未运行！');
        }
    });

    cb_stack.exec();
};

$assist.alert_assist_not_found = function () {
    $('#dialog-need-assist').modal();
};

$assist._make_message_box = function () {
    var _html = [
        '<div class="modal fade" id="dialog-need-assist">',
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

$assist.do_teleport = function (args, func_success, func_error) {
    // 第一步：将参数传递给web服务，准备获取一个远程连接会话ID
    var args_ = JSON.stringify(args);
    $.ajax({
        url: '/ops/get-session-id',
        type: 'POST',
        timeout: 5000,
        //data: {_xsrf: get_cookie('_xsrf'), args: args_},
        data: {args: args_},
        dataType: 'json',
        success: function (ret) {
            console.log('get-session-id:', ret);
            if (ret.code === TPE_OK) {
                // 第二步：获取到临时会话ID后，将此ID传递给助手，准备开启一次远程会话
                var session_id = ret.data.session_id;
                var remote_host_ip = ret.data.host_ip;
                var teleport_port = ret.data.teleport_port;
                var data = {
                    //server_ip: g_host_name,	//args.server_ip,
                    //server_port: parseInt(args.server_port),
                    teleport_ip: $assist.teleport_ip,
                    teleport_port: teleport_port,
                    remote_host_ip: remote_host_ip,
                    // remote_host_port: args.host_port,
                    size: 0, //parseInt(args.size),
                    console: 0, //args.console,
                    session_id: session_id,
                    protocol_type: parseInt(args.protocol_type),
                    protocol_sub_type: parseInt(args.protocol_sub_type)
                };
                console.log('---', data);
                var args_ = encodeURIComponent(JSON.stringify(data));
                $.ajax({
                    type: 'GET',
                    timeout: 5000,
                    //url: 'http://localhost:50022/ts_op/' + args_,
                    url: $assist.api_url + '/run/' + args_,
                    jsonp: 'callback',
                    dataType: 'json',
                    success: function (ret) {
                        if(ret.code === TPE_OK) {
                            func_success();
                        } else {
                            func_error(ret.code, ret.message);
                        }
                    },
                    error: function () {
                        func_error(TPE_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
                    }
                });
            } else {
                if (ret.code === TPE_NO_CORE_SERVER) {
                    func_error(ret.code, '远程连接请求失败，可能teleport核心服务尚未启动！' + ret.message);
                } else {
                    func_error(ret.code, ret.message);
                }
            }
        },
        error: function () {
            func_error(TPE_NETWORK, '远程网络通讯失败！');
        }
    });
};


/*
var g_req_version = "";
var g_last_version = "";
var g_current_version = "";

var g_host_name = window.location.hostname;

var error_process = function (ret, func_success, func_error) {
    var code = ret.code;
    if (code === TPE_OK) {
        func_success(ret);
        return;
    }

    if (code === TPE_START_CLIENT) {
        func_error(TPE_START_CLIENT, '启动本地客户端进程失败，请检查命令行是否正确：' + ret.path);
        console.log('启动本地进程失败，命令行：', ret.path);
    } else if (code === TPE_JSON_FORMAT || code === TPE_PARAM) {
        func_error(TPE_START_CLIENT, "启动本地客户端进程失败：启动参数错误！");
    } else if (code === TPE_OLD_ASSIST) {
        func_error(TPE_OLD_ASSIST, '助手版本太低，请下载最新版本！');
    }
    else {
        func_error(TPE_START_CLIENT, '启动本地客户端失败，错误代码：' + ret.code);
    }
};

var teleport_init = function (last_version, req_version, func_success, func_error) {

    g_req_version = req_version;
    g_last_version = last_version;
    var data = {};
    var args_ = encodeURIComponent(JSON.stringify(data));
    $.ajax({
        type: 'GET',
        timeout: 5000,
        url: 'http://127.0.0.1:50022/ts_get_version/' + args_,
        jsonp: 'callback',
        dataType: 'json',
        success: function (ret) {
            g_current_version = ret.version;
            if (version_compare()) {
                error_process(ret, func_success, func_error);
            } else {
                func_error(ret, TPE_OLD_ASSIST, '助手版本太低，请<a style="color:#aaaaff;" target="_blank" href="http://teleport.eomsoft.net/download">下载最新版本</a>！');
            }
        },
        error: function () {
            func_error({}, TPE_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
        }
    });
};

var version_compare = function () {
    var cur_version = parseInt(g_current_version.split(".")[2]);
    var req_version = parseInt(g_req_version.split(".")[2]);
    return cur_version >= req_version;
};

var to_teleport = function (url, args, func_success, func_error) {
    var auth_id = args['auth_id'];
    // 开始Ajax调用
    var args_ = JSON.stringify({auth_id: auth_id});
    $.ajax({
        url: url,
        type: 'POST',
        timeout: 6000,
        //data: {_xsrf: get_cookie('_xsrf'), args: args_},
        data: {args: args_},
        dataType: 'json',
        success: function (ret) {
            if (ret.code === 0) {
                var session_id = ret.data.session_id;
                var data = {
                    server_ip: g_host_name,	//args.server_ip,
                    server_port: parseInt(args.server_port),
                    host_ip: args.host_ip,
                    size: parseInt(args.size),
                    console: args.console,
                    session_id: session_id,
                    pro_type: parseInt(args.pro_type),
                    pro_sub: parseInt(args.pro_sub)
                };
                var args_ = encodeURIComponent(JSON.stringify(data));
                $.ajax({
                    type: 'GET',
                    timeout: 5000,
                    url: 'http://127.0.0.1:50022/ts_op/' + args_,
                    jsonp: 'callback',
                    dataType: 'json',
                    success: function (ret) {
                        error_process(ret, func_success, func_error);
                    },
                    error: function () {
                        func_error(TPE_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
                    }
                });
            } else {
                func_error(TPE_NO_CORE_SERVER, '远程连接请求失败，可能teleport核心服务尚未启动！' + ret.message);
            }
        },
        error: function () {
            func_error(TPE_NETWORK, '远程网络通讯失败！');
        }
    });
};

var to_admin_teleport = function (url, args, func_success, func_error) {
    var host_auth_id = args['host_auth_id'];
    // 开始Ajax调用
    var args_ = JSON.stringify({host_auth_id: host_auth_id});
    $.ajax({
        url: url,
        type: 'POST',
        timeout: 6000,
        //data: {_xsrf: get_cookie('_xsrf'), args: args_},
        data: {args: args_},
        dataType: 'json',
        success: function (ret) {
            if (ret.code === 0) {
                var session_id = ret.data.session_id;
                var data = {
                    server_ip: g_host_name,
                    server_port: parseInt(args.server_port),
                    host_ip: args.host_ip,
                    size: parseInt(args.size),
                    console: args.console,
                    session_id: session_id,
                    pro_type: parseInt(args.pro_type),
                    pro_sub: parseInt(args.pro_sub)
                };
                var args_ = encodeURIComponent(JSON.stringify(data));
                $.ajax({
                    type: 'GET',
                    timeout: 5000,
                    url: 'http://127.0.0.1:50022/ts_op/' + args_,
                    jsonp: 'callback',
                    dataType: 'json',
                    success: function (ret) {
                        error_process(ret, func_success, func_error);
                    },
                    error: function () {
                        func_error(TPE_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
                    }
                });
            } else {
                func_error(TPE_NO_CORE_SERVER, '远程连接请求失败，可能teleport核心服务尚未启动！' + ret.message);
            }
        },
        error: function () {
            func_error(TPE_NETWORK, '远程网络通讯失败！');
        }
    });
};

var to_admin_fast_teleport = function (url, args, func_success, func_error) {
    // 开始Ajax调用
    var args_ = JSON.stringify(args);
    $.ajax({
        url: url,
        type: 'POST',
        timeout: 6000,
        //data: {_xsrf: get_cookie('_xsrf'), args: args_},
        data: {args: args_},
        dataType: 'json',
        success: function (ret) {
            if (ret.code === 0) {
                var session_id = ret.data.session_id;
                var data = {
                    server_ip: g_host_name,
                    server_port: parseInt(args.server_port),
                    host_ip: args.host_ip,
                    size: parseInt(args.size),
                    session_id: session_id,
                    pro_type: parseInt(args.protocol),
                    pro_sub: parseInt(args.protocol_sub)
                };
                var args_ = encodeURIComponent(JSON.stringify(data));
                $.ajax({
                    type: 'GET',
                    timeout: 5000,
                    url: 'http://127.0.0.1:50022/ts_op/' + args_,
                    jsonp: 'callback',
                    dataType: 'json',
                    success: function (ret) {
                        error_process(ret, func_success, func_error);
                    },
                    error: function (jqXhr, _error, _e) {
                        console.log('jqXhr', jqXhr);
                        console.log('error', _error);
                        console.log('e', _e);

                        console.log('state:', jqXhr.state());
                        func_error(TPE_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
                    }
                });
            } else {
                func_error(TPE_NO_CORE_SERVER, '远程连接请求失败，可能teleport核心服务尚未启动！' + ret.message);
            }
        },
        error: function () {
            func_error(TPE_NETWORK, '远程网络通讯失败！');
        }
    });
};

var start_rdp_replay = function (args, func_success, func_error) {
    var args_ = encodeURIComponent(JSON.stringify(args));
    $.ajax({
        type: 'GET',
        timeout: 6000,
        url: $assist.api_url + '/rdp_play/' + args_,
        jsonp: 'callback',
        dataType: 'json',
        success: function (ret) {
            if (ret.code === TPE_OK) {
                error_process(ret, func_success, func_error);
            } else {
                func_error(ret.code, '查看录像失败！');
            }
            console.log('ret', ret);
        },
        error: function () {
            func_error(TPE_NETWORK, '与助手的络通讯失败！');
        }
    });
};
*/
