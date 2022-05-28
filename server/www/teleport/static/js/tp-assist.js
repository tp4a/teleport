"use strict";

// 页面访问助手的流程：
// 1. 通过ajax查询当前是否有已经绑定的助手连接可用，有则直接使用（避免每次刷新页面都调用一次url-protocol）
// 2. 如果没有，则打开ws通道，服务端会返回一个临时的助手id，页面再通过url-protocol去调用助手
// 3. 调用成功的话，ws通道会返回当前会话实际绑定的助手连接，后续操作可以通过助手连接来向助手发送操作命令

$tp.assist = {
    running: false,
    assist_id: 0,
    version: '',
    ver_require: '0.0.0',
    // api_url: '',
    teleport_ip: window.location.hostname,
    url_scheme: '',
    ws_url: '',
    ws: null,
    ws_keep_alive_timer_id: 0,

    next_commands: [],

    dom: {
        msg_box_title: null,
        msg_box_info: null,
        msg_box_desc: null
    },

    ws_response_callback: {
        start_assist: null,
        update_assist_info: null,
        assist_disconnected: null,
        run: null
    }
};

// $assist 是 $tp.assist 的别名，方便使用。
let $assist = $tp.assist;

$assist.init = function (cb_stack) {
    console.log('assist.init().');

    $assist._make_message_box();
    $('#dialog-need-assist-a').modal();

    $('#btn-assist-reload-page').click(function () {
        window.location.reload();
    });

    $assist.ws_response_callback['start_assist'] = $assist._on_ret_start_assist;
    $assist.ws_response_callback['update_assist_info'] = $assist._on_ret_update_assist_info;
    $assist.ws_response_callback['assist_disconnected'] = $assist._on_ret_assist_disconnected;
    $assist.ws_response_callback['run'] = $assist._on_ret_run;
    $assist.ws_response_callback['replay_rdp'] = $assist._on_ret_replay_rdp;

    $.ajax({
        url: '/assist/get-assist-info',
        type: 'POST',
        timeout: 5000,
        //data: {_xsrf: get_cookie('_xsrf'), args: args_},
        data: {},
        dataType: 'json',
        success: function (ret) {
            console.log('get-assist-info', ret);
            if (ret.code === TPE_OK) {
                $assist.running = true;
                $assist.assist_id = ret.data.assist_id;
                $assist.version = ret.data.assist_ver;

                if (_.isFunction($tp.assist_checked)) {
                    $tp.assist_checked();
                }

                if ($assist.next_commands.length > 0) {
                    $assist._bind_assist_and_exec(null);
                }
            } else if (ret.code === TPE_NOT_EXISTS) {
                // 还没有绑定助手，需要通过 url-protocol 方式启动一下
                $assist._bind_assist_and_exec(null);
            } else {
                // 其他错误
                $tp.notify_error('无法获取助手信息：' + tp_error_msg(ret.code, ret.message));
            }
        },
        error: function () {
            $tp.notify_error('无法获取助手信息：远程网络通讯失败！');
        }
    });

    cb_stack.exec();
};

$assist.add_next_command = function (cmd) {
    $assist.next_commands.push(cmd);
}

$assist.exec_next_command = function () {
    while ($assist.next_commands.length > 0) {
        console.log('send command: ', $assist.next_commands[0]);
        $assist.ws.send(JSON.stringify($assist.next_commands[0]));
        $assist.next_commands.pop();
    }
}

$assist.register_response_handler = function (method, fn) {
    $assist.ws_response_callback[method] = fn;
};

$assist.keep_alive = function () {
    if ($assist.ws.readyState === $assist.ws.OPEN) {
        $assist.ws.send('PING');
    }
    $assist.ws_keep_alive_timer_id = setTimeout($assist.keep_alive, 15000);
};

$assist._bind_assist_and_exec = function (cmd) {
    let msg_obj = {
        'type': ASSIST_WS_COMMAND_TYPE_REQUEST,
        'method': 'register',
        'param': {
            'client': 'web'
        }
    }

    if (!_.isNull(cmd)) {
        $assist.add_next_command(cmd);
    }

    if (!$assist.running && !_.isNull($assist.ws)) {
        console.log('ws-send:', msg_obj);
        $assist.ws.send(JSON.stringify(msg_obj));
        return;
    }

    if (_.isNull($assist.ws)) {
        console.log('create web-ws.');

        if (location.protocol === 'http:') {
            $assist.ws_url = 'ws://' + location.host + '/ws/assist/';
        } else {
            $assist.ws_url = 'wss://' + location.host + '/ws/assist/';
        }


        $assist.ws = new WebSocket($assist.ws_url + encodeURIComponent(JSON.stringify(msg_obj)));

        $assist.ws.onopen = function (e) {
            console.log('web-ws: connected.');

            $assist.ws_keep_alive_timer_id = setTimeout($assist.keep_alive, 15000);
        };

        $assist.ws.onclose = function (e) {
            console.log('web-ws: disconnected.');
            if ($assist.ws_keep_alive_timer_id) {
                clearTimeout($assist.ws_keep_alive_timer_id);
                $assist.ws_keep_alive_timer_id = 0;
            }
            $assist.ws = null;
            $assist.assist_id = 0;
            $assist.assist_ver = '';
        };

        $assist.ws.onmessage = function (e) {
            if (e.data === 'PONG')
                return;

            let t = JSON.parse(e.data);

            if (_.isUndefined(t.type)) {
                console.log('invalid message format: ', e.data);
                return;
            }

            if (t.type === ASSIST_WS_COMMAND_TYPE_RESPONSE) {
                if (!_.isUndefined($assist.ws_response_callback[t.method])) {
                    let fn = $assist.ws_response_callback[t.method];
                    fn(t.code, t.message, t.data);
                } else {
                    console.error('There are no callback for method: ', t.method);
                    // return;
                }
            } else {
                console.log('unknown type:', t.type)
            }

        };
    }
};

$assist._on_ret_start_assist = function (code, message, ret) {
    if (code !== TPE_OK) {
        console.log('show error: code=', code, ', message=', message);
        $tp.notify_error('发生错误：' + tp_error_msg(code, message));
        return;
    }

    let session_id = Cookies.get('_sid');
    let data = {'method': 'register', 'ws_url': $assist.ws_url, 'assist_id': ret.request_assist_id, 'session_id': session_id}
    $assist.url_scheme = 'teleport://register?param=' + JSON.stringify(data);
    if (!$('#url-protocol').length) {
        let _html = '<div id="url-protocol" style="display:none;z-index=-1;"><iframe src=""/></div>';
        $('body').append($(_html));
    }
    console.log($assist.url_scheme);
    $('#url-protocol').find("iframe").attr("src", $assist.url_scheme);

    // 在macOS平台，如果助手尚未运行，首次通过 teleport:// 调起助手，只会运行助手，并不会触发其连接服务端
    // 试图5秒后，检查是否获取到助手版本，如果没有，再尝试一次启动助手，会被浏览器安全设置限制
    // 错误原因：由于用户并未触发，或此 iframe 上次加载以来的时间不足，已屏蔽使用外部协议的 iframe。
    // 这种情况下，只能再次刷新页面来触发一次，即可正常连接上。
    setTimeout($assist.check_assist, 3000);
};

$assist._on_ret_update_assist_info = function (code, message, ret) {
    if (code !== TPE_OK) {
        console.log('show error: code=', code, ', message=', message);
        $tp.notify_error('发生错误：' + tp_error_msg(code, message));
        return;
    }

    if (ret.assist_ver === '') {
        console.log("so bad.");
    } else {
        $assist.running = true;
        $assist.version = ret.assist_ver;

        if (_.isFunction($tp.assist_checked)) {
            $tp.assist_checked();
        }

        $assist.exec_next_command();
    }
}

$assist._on_ret_assist_disconnected = function (code, message, ret) {
    console.log('assist-ws disconnected.');
    $assist.running = false;
    $assist.version = '';
    $assist.url_scheme = '';

    if (_.isFunction($tp.assist_checked)) {
        $tp.assist_checked();
    }
}

$assist._on_ret_run = function (code, message, ret) {
    console.log('_on_ret_run(), code=', code, 'message=', message, 'ret=', ret);

    if (code !== TPE_OK) {
        console.log('show error: code=', code, ', message=', message);
        $tp.notify_error('发生错误：' + tp_error_msg(code, message));
        return;
    }

    $tp.notify_success('已通知助手启动本地客户端进行远程连接!');
}

$assist._on_ret_replay_rdp = function (code, message, ret) {
    console.log('_on_ret_replay_rdp(), code=', code, 'message=', message, 'ret=', ret);

    if (code !== TPE_OK) {
        console.log('show error: code=', code, ', message=', message);
        $tp.notify_error('发生错误：' + tp_error_msg(code, message));
        return;
    }

    $tp.notify_success('已通知助手启动本地RDP录像播放器!');
}

$assist.check_assist = function () {
    console.log('check assist...');
    if (!$assist.running) {
        $assist.alert_assist_not_found(TPE_NO_ASSIST);
        return false;
    } else if (!$assist._version_compare()) {
        $assist.alert_assist_not_found(TPE_OLD_ASSIST);
        return false;
    }
    return true;
};

$assist.alert_assist_not_found = function (errcode) {
    if (errcode === TPE_NO_ASSIST) {
        $assist.dom.msg_box_title.html('未检测到Teleport助手');
        $assist.dom.msg_box_info.html('需要Teleport助手来辅助远程连接，请确认本机运行了TELEPORT助手！');
        $assist.dom.msg_box_desc.html(
            '<p>如果您已经安装运行了Teleport助手（系统托盘区可见到 <img src="/static/favicon.png" width="18"/> 图标），可尝试刷新页面。如果本提示持续出现，请联系管理员。</p>' +
            '<p>如果您尚未运行Teleport助手，请先下载Teleport助手安装包并安装。一旦运行了Teleport助手，即可刷新页面，重新进行远程连接。</p>');
    } else if (errcode === TPE_OLD_ASSIST) {
        $assist.dom.msg_box_title.html('Teleport助手需要升级');
        $assist.dom.msg_box_info.html('检测到Teleport助手版本 v' + $assist.version + '，但需要最低版本 v' + $assist.ver_require + '。');
        $assist.dom.msg_box_desc.html('<p>请下载最新版Teleport助手安装包并安装、运行。一旦升级了Teleport助手，即可刷新页面，重新进行远程连接。</p>');
    }

    $('#dialog-need-assist').modal();
};

// 1.2.0  > 1.1.0
// 1.2    = 1.2.0
// 2.1.1  > 1.2.9
// 2.1.10 > 2.1.9
$assist._version_compare = function () {
    let ver_current = $assist.version.split(".");
    let ver_require = $assist.ver_require.split(".");

    let count = ver_current.length;
    if (ver_require.length > count)
        count = ver_require.length;

    for (let i = 0; i < count; ++i) {
        let c = ver_current[i] || 0;
        let r = ver_require[i] || 0;
        if (c < r)
            return false;
    }

    return true;
};

$assist._make_message_box = function () {
    let _html = [
        '<div class="modal fade" id="dialog-need-assist">',
        '<div class="modal-dialog" role="document">',
        '<div class="modal-content">',
        '<div class="modal-header">',
        '<h4 class="modal-title" id="assist-msg-box-tittle"></h4>',
        '</div>',
        '<div class="modal-body">',
        '<div class="alert alert-danger" role="alert">',
        '<p id="assist-msg-box-info"></p>',
        '</div>',
        '<div id="assist-msg-box-desc">',
        '</div>',
        '<div>',
        '<hr/>',
        '<p class="bold">下载安装Teleport助手</p>',
        '<div class="raw">',
        '<div class="col-sm-6 center">',
        '<a class="btn btn-success" type="button" style="width:100%;" href="/assist/download/windows">',
        '<i class="fab fa-windows fa-fw" style="font-size:36px"></i><br/>',
        '<i class="fa fa-download fa-fw"></i> 下载 Windows 版本助手',
        '</a>',
        '</div>',
        '<div class="col-sm-6 center">',
        '<a class="btn btn-info" type="button" style="width:100%;" href="/assist/download/macos">',
        '<i class="fab fa-apple fa-fw" style="font-size:36px"></i><br/>',
        '<i class="fa fa-download fa-fw"></i> 下载 macOS 版本助手',
        '</a>',
        '</div>',
        '</div>',
        '</div>',
        '<div class="clear-float"></div>',
        '</div>',
        '<div class="modal-footer">',
        '<button type="button" class="btn btn-sm btn-primary" id="btn-assist-reload-page"><i class="fa fa-sync fa-fw"></i> 刷新页面</button>',
        '<button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 我知道了</button>',
        '</div>',
        '</div>',
        '</div>',
        '</div>',
        '</div>'
    ].join('');
    $('body').append($(_html));

    $assist.dom.msg_box_title = $('#assist-msg-box-tittle');
    $assist.dom.msg_box_info = $('#assist-msg-box-info');
    $assist.dom.msg_box_desc = $('#assist-msg-box-desc');
};

$assist.select_local_file = function (app_type) {
    let cmd = {
        type: ASSIST_WS_COMMAND_TYPE_REQUEST,
        method: 'select_file',
        param: {
            app_type: app_type
        }
    };

    $assist.ws.send(JSON.stringify(cmd));
};

$assist.do_teleport = function (args, func_success, func_error) {
    // todo: 将args传给服务端，由服务端直接组一个命令发给对应的assist-websocket进行执行即可，无需再返回到页面中转一次。

    // 第一步：将参数传递给web服务，准备获取一个远程连接会话ID
    let args_ = JSON.stringify(args);
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
                let session_id = ret.data.session_id;
                let remote_host_ip = ret.data.host_ip;
                let remote_host_name = ret.data.host_name;
                let teleport_port = ret.data.teleport_port;
                let data = {
                    //server_ip: g_host_name,	//args.server_ip,
                    //server_port: parseInt(args.server_port),
                    teleport_ip: $assist.teleport_ip,
                    teleport_port: teleport_port,
                    remote_host_ip: remote_host_ip,
                    remote_host_name: remote_host_name,
                    // remote_host_port: args.host_port,
                    // rdp_size: args.rdp_size,
                    // rdp_console: args.rdp_console,
                    session_id: session_id,
                    protocol_type: parseInt(args.protocol_type),
                    protocol_sub_type: parseInt(args.protocol_sub_type),
                    protocol_flag: parseInt(ret.data.protocol_flag),
                    is_interactive: args.is_interactive
                };

                if (args.protocol_type === TP_PROTOCOL_TYPE_RDP) {
                    data.rdp_width = args.rdp_width;
                    data.rdp_height = args.rdp_height;
                    data.rdp_console = args.rdp_console;
                }

                console.log('---run---', data);
                let _exec = {type: ASSIST_WS_COMMAND_TYPE_REQUEST, method: 'run', param: data};

                // 注意：这里不能在再用iframe调用teleport://的方式来让助手启动本地程序了，web页面先于助手启动时，点击远程连接
                // 会导致连续两次调用url-protocol，第一次是让助手进行ws注册，此处是第二次，因为是连续调用，会导致firefox报错：
                // 错误：由于用户并未触发，或此 iframe 上次加载以来的时间不足，已屏蔽使用外部协议的 iframe。
                // 因此直接通过ws到TP服务端转发给助手。

                if (_.isNull($assist.ws) || !$assist.running) {
                    $assist._bind_assist_and_exec(_exec);
                } else {
                    // _exec($assist);
                    $assist.ws.send(JSON.stringify(_exec));
                }
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

$assist.do_rdp_replay = function (rid, func_success, func_error) {
    let data = {
        rid: rid,
        web: $tp.web_server,
        sid: Cookies.get('_sid')
    };

    console.log('---replay_rdp---', data);
    let _exec = {type: ASSIST_WS_COMMAND_TYPE_REQUEST, method: 'replay_rdp', param: data};

    if (_.isNull($assist.ws) || !$assist.running) {
        $assist._bind_assist_and_exec(_exec);
    } else {
        $assist.ws.send(JSON.stringify(_exec));
    }
}
