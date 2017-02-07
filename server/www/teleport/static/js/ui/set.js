/**
 * Created by mi on 2016/7/4.
 */

var REFRESH_TIMEOUT = 10;

var g_assist = null;

ywl.on_init = function (cb_stack, cb_args) {
	ywl.refresh_timeout = REFRESH_TIMEOUT;

	g_assist = ywl.create_assist();

	var config_list = ywl.page_options.config_list;

//	var ts_server_ip = config_list['ts_server_ip'];
//	$("#current-ts-server-ip").val(ts_server_ip);

//	var ts_server_rpc_ip = config_list['ts_server_rpc_ip'];
//	$("#current-rpc-ip").val(ts_server_rpc_ip);
//
//	var ts_server_rpc_port = config_list['ts_server_rpc_port'];
//	$("#current-rpc-port").val(ts_server_rpc_port);

	var ts_server_rdp_port = config_list['ts_server_rdp_port'];
	$("#current-rdp-port").val(ts_server_rdp_port);

	var ts_server_ssh_port = config_list['ts_server_ssh_port'];
	$("#current-ssh-port").val(ts_server_ssh_port);

    var ts_server_telnet_port = config_list['ts_server_telnet_port'];
	$("#current-telnet-port").val(ts_server_telnet_port);
    
//	var ip_html = [];
//	for (var i = 0; i < config_list['_ip_list'].length; i++) {
//		ip_html.push('<li><a href="javascript:;">' + config_list['_ip_list'][i] + '</a></li>');
//	}
//	$('#select-ip').html(ip_html.join(''));

	$('#select-ip li a').click(function () {
		$("#current-ts-server-ip").val($(this).text());
	});

	$("#btn-check").click(function () {
		var ts_server_ip = $("#current-ts-server-ip").val();
//		var ts_server_rpc_ip = $("#current-rpc-ip").val();
//		var ts_server_rpc_port = $("#current-rpc-port").val();
		var ts_server_rdp_port = $("#current-rdp-port").val();
		var ts_server_ssh_port = $("#current-ssh-port").val();
        var ts_server_telnet_port = $("#current-telnet-port").val();
        
		var list = [];
		var item_1 = {name: 'ts_server_ip', value: ts_server_ip};
		list.push(item_1);

//		var item_2 = {name: 'ts_server_rpc_ip', value: ts_server_rpc_ip};
//		list.push(item_2);
//
//		var item_3 = {name: 'ts_server_rpc_port', value: ts_server_rpc_port};
//		list.push(item_3);

		var item_4 = {name: 'ts_server_rdp_port', value: ts_server_rdp_port};
		list.push(item_4);

		var item_5 = {name: 'ts_server_ssh_port', value: ts_server_ssh_port};
		list.push(item_5);
		var rdp_port = parseInt(ts_server_rdp_port);
		var ssh_port = parseInt(ts_server_ssh_port);
		var args_ = encodeURIComponent(JSON.stringify({server_ip: ts_server_ip, rdp_port: rdp_port, ssh_port: ssh_port}));
		$.ajax({
			type: 'GET',
			timeout: 60000,
			url: 'http://127.0.0.1:50022/ts_check/' + args_,
			jsonp: 'callback',
			dataType: 'json',
			success: function (ret) {
				if (ret.code === 0) {
					ywl.notify_success("测试通过，可以正常使用 teleport 堡垒机！");
				} else if (ret.code === 7) {
					ywl.notify_error("PING测试通过，TCP端口测试未通过，请检查防火墙设置！");
				} else {
					console.log('ret', ret);
					ywl.notify_error("测试失败，请检查 teleport 堡垒机地址是否正确，并检查防火墙设置！");
				}
			},
			error: function () {
				g_assist.alert_assist_not_found();
			}
		});
	});

	$("#btn-save-config").click(function () {
		var ts_server_ip = $("#current-ts-server-ip").val();
//			var ts_server_rpc_ip = $("#current-rpc-ip").val();
//			var ts_server_rpc_port = $("#current-rpc-port").val();
		var ts_server_rdp_port = $("#current-rdp-port").val();
		var ts_server_ssh_port = $("#current-ssh-port").val();
        var ts_server_telnet_port = $("#current-telnet-port").val();

		var reboot = false;
		var new_config = [];

		var old_config = ywl.page_options.config_list;
		if (ts_server_ip != old_config['ts_server_ip']) {
			new_config.push({name: 'ts_server_ip', value: ts_server_ip});
		}

		if (ts_server_rdp_port != old_config['ts_server_rdp_port']) {
			new_config.push({name: 'ts_server_rdp_port', value: ts_server_rdp_port});
			reboot = true;
		}

		if (ts_server_ssh_port != old_config['ts_server_ssh_port']) {
			new_config.push({name: 'ts_server_ssh_port', value: ts_server_ssh_port});
			reboot = true;
		}
		if (ts_server_telnet_port != old_config['ts_server_telnet_port']) {
			new_config.push({name: 'ts_server_telnet_port', value: ts_server_telnet_port});
			reboot = true;
		}
		if (new_config.length == 0) {
			// nothing changed.
			ywl.notify_error('配置未改变，无需保存！');
			return;
		}

		if (!reboot) {
			ywl.ajax_post_json('/set/update-config', {cfg: new_config, reboot: false},
				function (ret) {
					if (ret.code == 0) {
						ywl.notify_success('配置保存成功！');
						ywl.page_options.config_list['ts_server_ip'] = ts_server_ip;
					}
					else {
						ywl.notify_error('配置保存失败！');
					}
				},
				function () {
					ywl.notify_error('配置保存失败！');
				}
			);

			return;
		}


		// if need reboot, let user confirm.

		var _fn_sure = function (cb_stack, cb_args) {

			ywl.ajax_post_json('/set/update-config', {cfg: new_config, reboot: true},
				function (ret) {
					if (ret.code == 0) {
						$('#dlg_restart_service').modal({backdrop: 'static', keyboard: false});

						ywl.refresh_timeout = REFRESH_TIMEOUT;
						setInterval(ywl.refresh, 1000);

						// 5 秒之后刷新页面，导致重定向到登录页面
//						setTimeout(function () {
//							location.reload(true);
//						}, 5000);
					}
					else {
						ywl.notify_error('配置信息保存失败！');
					}
				},
				function () {
					ywl.notify_error('配置信息保存失败！');
				}
			);
		};

		var cb_stack = CALLBACK_STACK.create();
		ywl.dlg_confirm(cb_stack, {
			msg: '<p><strong>为使设置生效，需要重启teleport服务！服务重启过程中，WEB后台和跳板连接均会中断！</strong></p><p>您确定要保存设置并重启teleport服务吗？</p>',
			fn_yes: _fn_sure
		});
	});

//	$("#btn-os-reboot").click(function () {
//		var _fn_sure = function (cb_stack, cb_args) {
//			ywl.ajax_post_json('/set/os-operator', {OP: 1},
//				function (ret) {
//					if (ret.code == 0) {
//						ywl.notify_success('正在重新启动系统');
//					}
//					else {
//						ywl.notify_error('重启系统失败');
//					}
//				},
//				function () {
//					ywl.notify_error('重启系统失败');
//				}
//			);
//		};
//		var cb_stack = CALLBACK_STACK.create();
//
//		ywl.dlg_confirm(cb_stack, {
//			msg: '<p>您确定要重启系统吗？！！</p>',
//			fn_yes: _fn_sure
//		});
//
//	});

//    $("#btn-os-shut").click(function () {
//        var _fn_sure = function (cb_stack, cb_args) {
//        ywl.ajax_post_json('/set/os-operator', {OP: 2},
//            function (ret) {
//                if (ret.code == 0) {
//                    ywl.notify_success('正在关闭系统');
//                }
//                else {
//                    ywl.notify_error('关闭系统失败');
//                }
//            },
//            function () {
//                ywl.notify_error('关闭系统失败');
//            }
//        );
//        };
//        var cb_stack = CALLBACK_STACK.create();
//
//        ywl.dlg_confirm(cb_stack, {
//                msg: '<p>您确定要关闭系统吗？！！</p>',
//                fn_yes: _fn_sure
//        });
//    });

	cb_stack.exec();
};

ywl.refresh = function () {
	ywl.refresh_timeout -= 1;
	if (0 == ywl.refresh_timeout) {
		location.reload(true);
	} else {
		$('#reboot_time').html(ywl.refresh_timeout);
	}
};
