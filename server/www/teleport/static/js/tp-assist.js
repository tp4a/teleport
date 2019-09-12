"use strict";

$tp.assist = {
    running: false,
    version: '',
    ver_require: '0.0.0',
    errcode: TPE_OK,
    api_url: '',
    teleport_ip: window.location.hostname,

    dom: {
        msg_box_title: null,
        msg_box_info: null,
        msg_box_desc: null
    }
};

// console.log(window.location.protocol);

// $assist 是 $tp.assist 的别名，方便使用。
var $assist = $tp.assist;

$assist.init = function (cb_stack) {
    if(location.protocol === 'http:') {
        $assist.api_url = 'http://localhost:50022/api';
    } else {
        $assist.api_url = 'https://localhost:50023/api';
    }

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

            if (_.isFunction($tp.assist_checked)) {
                $tp.assist_checked();
            }
            // if (version_compare()) {
            //     error_process(ret, func_success, func_error);
            // } else {
            //     func_error(ret, TPE_OLD_ASSIST, '助手版本太低，请<a style="color:#aaaaff;" target="_blank" href="http://tp4a.com/download">下载最新版本</a>！');
            // }
        },
        error: function () {
            $assist.running = false;
            if (_.isFunction($tp.assist_checked)) {
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
    console.log($assist.errcode);
    if($assist.errcode === TPE_NO_ASSIST) {
        $assist.dom.msg_box_title.html('未检测到TELEPORT助手');
        $assist.dom.msg_box_info.html('需要TELEPORT助手来辅助远程连接，请确认本机运行了TELEPORT助手！');
        $assist.dom.msg_box_desc.html('如果您尚未运行TELEPORT助手，请 <a href="http://tp4a.com/download" target="_blank"><strong>下载最新版TELEPORT助手安装包</strong></a> 并安装。一旦运行了TELEPORT助手，即可重新进行远程连接。');
        //$assist.dom.msg_box_desc.html('如果您尚未运行TELEPORT助手，请 <a href="/static/download/teleport-assist-windows.exe" target="_blank"><strong>下载最新版TELEPORT助手安装包</strong></a> 并安装。一旦运行了TELEPORT助手，即可重新进行远程连接。');
    } else if($assist.errcode === TPE_OLD_ASSIST) {
        $assist.dom.msg_box_title.html('TELEPORT助手需要升级');
        $assist.dom.msg_box_info.html('检测到TELEPORT助手版本 v'+ $assist.version +'，但需要最低版本 v'+ $assist.ver_require+'。');
        $assist.dom.msg_box_desc.html('请 <a href="http://tp4a.com/download" target="_blank"><strong>下载最新版TELEPORT助手安装包</strong></a> 并安装。一旦升级了TELEPORT助手，即可重新进行远程连接。');
        //$assist.dom.msg_box_desc.html('请 <a href="/static/download/teleport-assist-windows.exe" target="_blank"><strong>下载最新版TELEPORT助手安装包</strong></a> 并安装。一旦升级了TELEPORT助手，即可重新进行远程连接。');
    }

    $('#dialog-need-assist').modal();
};

// 1.2.0  > 1.1.0
// 1.2    = 1.2.0
// 2.1.1  > 1.2.9
// 2.1.10 > 2.1.9
$assist._version_compare = function () {
    var ver_current = $assist.version.split(".");
    var ver_require = $assist.ver_require.split(".");

    var count = ver_current.length;
    if(ver_require.length > count)
        count = ver_require.length;

    var c, r;
    for(var i = 0; i < count; ++i) {
        c = ver_current[i] || 0;
        r = ver_require[i] || 0;
        if(c < r)
            return false;
    }

    return true;
};

$assist._make_message_box = function () {
    var _html = [
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
        '<p id="assist-msg-box-desc"></p>',
        '</div>',
        '<div class="modal-footer">',
        '<button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 我知道了</button>',
        '</div>',
        '</div>',
        '</div>',
        '</div>',
        '</div>'
    ].join('\n');
    $('body').append($(_html));

    $assist.dom.msg_box_title = $('#assist-msg-box-tittle');
    $assist.dom.msg_box_info = $('#assist-msg-box-info');
    $assist.dom.msg_box_desc = $('#assist-msg-box-desc');
};

$assist.do_teleport = function (args, func_success, func_error) {
    if(!$app.options.url_proto){
        if(!$assist.running) {
            $assist.errcode = TPE_NO_ASSIST;
            func_error(TPE_NO_ASSIST, '');
            return;
        } else if(!$assist._version_compare()) {
            $assist.errcode = TPE_OLD_ASSIST;
            func_error(TPE_NO_ASSIST, '');
            return;
	}
    }

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
                var remote_host_name = ret.data.host_name;
                var teleport_port = ret.data.teleport_port;
                var data = {
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
                    protocol_flag: parseInt(ret.data.protocol_flag)
                };

                if(args.protocol_type === TP_PROTOCOL_TYPE_RDP) {
                    data.rdp_width = args.rdp_width;
                    data.rdp_height = args.rdp_height;
                    data.rdp_console = args.rdp_console;
                }

                // console.log('---', data);
                var args_ = encodeURIComponent(JSON.stringify(data));
                // 判断是否使用 url-protocol 处理方式
				if ($app.options.url_proto){
					if(!$("#url-protocol").length) {
						var _html = '<div id="url-protocol" style="display:none;z-index=-1;"><iframe src=""/></div>';
						$('body').append($(_html));
					}
					$("#url-protocol").find("iframe").attr("src",'teleport://' + JSON.stringify(data));
				}else{
                    $.ajax({
                        type: 'GET',
                        timeout: 5000,
                        url: $assist.api_url + '/run/' + args_,
                        jsonp: 'callback',
                        dataType: 'json',
                        success: function (ret) {
                            console.log('ret', ret);
                            if (ret.code === TPE_OK) {
                                func_success();
                            } else {
                                func_error(ret.code, ret.message);
                            }
                        },
                        error: function () {
                            func_error(TPE_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
                        }
                    });
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

$assist.do_rdp_replay = function (args, func_success, func_error) {
    // ==================================================
    // args is dict with fields shown below:
    //   rid: (int) - record-id in database.
    //   user: (string) - who did the RDP connection.
    //   acc: (string) - account to login to remote RDP server.
    //   host: (string) - IP of the remote RDP server.
    //   start: (string) - when start the RDP connection, should be a UTC timestamp.
    // ==================================================

    // now fix the args.
    args.web = $tp.web_server; // (string) - teleport server base address, like "http://127.0.0.1:7190", without end-slash.
    args.sid = Cookies.get('_sid'); // (string) - current login user's session-id.
    args.start = tp_format_datetime(tp_utc2local(args.start), 'yyyyMMdd-HHmmss'); // (string) - convert UTC timestamp to local human-readable string.

    console.log('do-rdp-replay:', args);

    var args_ = encodeURIComponent(JSON.stringify(args));
    $.ajax({
        type: 'GET',
        timeout: 6000,
        url: $assist.api_url + '/rdp_play/' + args_,
        jsonp: 'callback',
        dataType: 'json',
        success: function (ret) {
            console.log('ret', ret);
            if (ret.code === TPE_OK) {
                func_success();
            } else {
                // func_error(ret.code, '查看远程桌面操作录像失败！');
                func_error(ret.code, ret.message);
            }
        },
        error: function () {
            func_error(TPE_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
        }
    });
};

/*

var version_compare = function () {
    var cur_version = parseInt(g_current_version.split(".")[2]);
    var req_version = parseInt(g_req_version.split(".")[2]);
    return cur_version >= req_version;
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
