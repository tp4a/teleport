/**
 * Created by mi on 2016/6/28.
 */
"use strict";

var TP_ERR_NETWORK = 1;
var TP_ERR_START_CLIENT = 2;
var TP_ERR_NO_ASSIST = 3;
//var TP_ERR_ASSIST_DENIED = 4;
var TP_ERR_CORE_SRV = 5;
var TP_ERR_TRIAL_LIMITED = 6;
var TP_ERR_VERSION_TOO_LOW = 7;

var g_low_version = "";
var g_last_version = "";
var g_current_version = "";

var g_host_name = window.location.hostname;

var error_process = function (ret, func_success, func_error) {
	console.log("ret", ret);
	var code = ret.code;
	if (code == 0) {
		func_success(ret);
		return;
	}

	if (code == 0x1006) {
		func_error(TP_ERR_START_CLIENT, '启动本地客户端进程失败，请检查命令行是否正确：' + ret.path);
		console.log('启动本地进程失败，命令行：', ret.path);
	} else if (code == 0x1004) {
		func_error(TP_ERR_START_CLIENT, "启动本地客户端进程失败：启动参数错误！");
	} else if (code == TP_ERR_VERSION_TOO_LOW) {
		func_error(TP_ERR_VERSION_TOO_LOW, '助手版本太低，请下载最新版本！');
	}
	else {
		func_error(TP_ERR_START_CLIENT, '启动本地客户端失败，错误代码：' + ret.code);
	}
};

var teleport_init = function (low_version, last_version, func_success, func_error) {

	g_low_version = low_version;
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
			console.log("current_version", g_current_version);
			if (version_compare()) {
				error_process(ret, func_success, func_error);
			} else {
				func_error(ret, TP_ERR_VERSION_TOO_LOW, '助手版本太低，请<a style="color:#aaaaff;" href="http://teleport.eomsoft.net/static/download/teleport-assist-last-win.zip">下载最新版本</a>！');
			}
		},
		error: function (jqXhr) {
			func_error({}, TP_ERR_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
		}
	});
};

var version_compare = function () {

	var cur_version = parseInt(g_current_version.split(".")[2]);
//	var last_version = parseInt(g_last_version.split(".")[2]);
	var low_version = parseInt(g_low_version.split(".")[2]);
	return cur_version >= low_version;
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
					error: function (jqXhr) {
						func_error(TP_ERR_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
					}
				});
			} else {
				func_error(TP_ERR_CORE_SRV, 'Web:远程连接请求失败，可能teleport核心服务尚未启动！');
			}
		},
		error: function () {
			func_error(TP_ERR_NETWORK, 'Web:远程网络通讯失败！');
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
					server_ip: g_host_name, // args.server_ip,
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
						func_error(TP_ERR_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
					}
				});
			} else {
				func_error(TP_ERR_CORE_SRV, 'Web:远程连接请求失败，可能teleport核心服务尚未启动！');
			}
		},
		error: function () {
			func_error(TP_ERR_NETWORK, 'Web:远程网络通讯失败！');
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
					server_ip: g_host_name, //args.server_ip,
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
						func_error(TP_ERR_NO_ASSIST, '无法连接到teleport助手，可能尚未启动！');
					}
				});
			} else {
				func_error(TP_ERR_CORE_SRV, 'Web:远程连接请求失败，可能teleport核心服务尚未启动！');
			}
		},
		error: function () {
			func_error(TP_ERR_NETWORK, 'Web:远程网络通讯失败！');
		}
	});
};

var start_rdp_replay = function (args, func_success, func_error) {

	var args_ = encodeURIComponent(JSON.stringify(args));
	$.ajax({
		type: 'GET',
		timeout: 6000,
		url: 'http://127.0.0.1:50022/ts_rdp_play/' + args_,
		jsonp: 'callback',
		dataType: 'json',
		success: function (ret) {
			if (ret.code === 0) {
				error_process(ret, func_success, func_error);
			} else {
				func_error(1, '查看录像失败！');
			}
			console.log('ret', ret);
		},
		error: function () {
			func_error(TP_ERR_NETWORK, 'Web:远程网络通讯失败！');
		}
	});
};
