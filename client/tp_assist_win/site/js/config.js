"use strict";

var g_url_base = 'http://127.0.0.1:50022';

var g_cfg = null;



var get_config = function () {
	$.ajax({
		type: 'GET',
		timeout: 5000,
		url: g_url_base + '/api/get_config',
		jsonp: 'callback',
		dataType: 'json',
		success: function (ret) {
			if (ret.code == 0) {
				console.log(ret.data);
				g_cfg = ret.data;
				//init_config_list(type, ret.config_list);
			} else {
				alert("获取配置信息失败!");
			}
		},
		error: function (jqXhr, _error, _e) {
			console.log('state:', jqXhr.state());
			alert("获取配置信息失败!");
		}
	});
}

var set_current_client_config = function (tpye, name, path, commandline, desc) {
	var data = {
		type: tpye,
		name: name,
		path: path,
		commandline: commandline
	};
	var args_ = encodeURIComponent(JSON.stringify(data));

	$.ajax({
		type: 'GET',
		timeout: 5000,
		url: 'http://127.0.0.1:50022/ts_set_config/' + args_,
		jsonp: 'callback',
		dataType: 'json',
		success: function (ret) {
			if (ret.code == 0) {
				alert("保存成功");
			} else {
				alert("保存成功" + ret.code);
			}

		},
		error: function (jqXhr, _error, _e) {
			console.log('state:', jqXhr.state());
			alert("保存失败");
		}
	});
}

var open_exist_file = function (callback) {
	var data = {
		action: 1
	};
	var args_ = encodeURIComponent(JSON.stringify(data));

	$.ajax({
		type: 'GET',
		timeout: -1,
		url: 'http://127.0.0.1:50022/ts_file_action/' + args_,
		jsonp: 'callback',
		dataType: 'json',
		success: function (ret) {
			callback(0, ret.path);
		},
		error: function (jqXhr, _error, _e) {
			console.log('state:', jqXhr.state());
			callback(-1, "");
		}
	});
}

var init_config_list = function (type, config_list) {

	var html = "";
	if (type == 1) {
		$("#ssh-client-type").html(html);
		for (var i = 0; i < config_list.length; i++) {
			var item = config_list[i];
			html = '<option id="ssh-' + item.name + '" value="' + item.name + '">' + item.alias_name + '</option>';
			$('#ssh-client-type').append(html);
			if (item.current == 1) {
				$('#ssh-' + item.name).attr('selected', true);
				init_config_param(type, item.build_in, item.path, item.commandline);
				g_current_ssh = item.name;
			}
			g_ssh_config_dict[item.name] = item;
		}
	} else if(type == 2) {
		$('#sftp-client-type').html(html);
		for (var i = 0; i < config_list.length; i++) {
			var item = config_list[i];
			html = '<option id="sftp-' + item.name + '" value="' + item.name + '">' + item.alias_name + '</option>';
			$('#sftp-client-type').append(html);
			if (item.current == 1) {
				$('#sftp-' + item.name).attr('selected', true);
				init_config_param(type, item.build_in, item.path, item.commandline);
				g_current_sftp = item.name;
			}
			g_sftp_config_dict[item.name] = item;
		}
	} else if(type == 3) {
		$('#telnet-client-type').html(html);
		for (var i = 0; i < config_list.length; i++) {
			var item = config_list[i];
			html = '<option id="telnet-' + item.name + '" value="' + item.name + '">' + item.alias_name + '</option>';
			$("#telnet-client-type").append(html);
			if (item.current == 1) {
				$('#telnet-' + item.name).attr('selected', true);
				init_config_param(type, item.build_in, item.path, item.commandline);
				g_current_telnet = item.name;
			}
			g_telnet_config_dict[item.name] = item;
		}
	}
}

var init_config_param = function (type, build_in, path, command_line) {
	if (type == 1) {
		if (build_in == 1) {
			$("#ssh-exec-args").attr("readonly", "readonly");
			$("#ssh-select-path").attr("disabled", "disabled");
		} else {
			$("#ssh-exec-args").removeAttr("readonly");
			$("#ssh-select-path").removeAttr("disabled");
		}
		$("#ssh-exec-path").val(path);
		$("#ssh-exec-args").val(command_line);
	} else if (type == 2) {
		if (build_in == 1) {
			$("#sftp-exec-args").attr("readonly", "readonly");
			$("#sftp-select-path").attr("disabled", "disabled");
		} else {
			$("#sftp-exec-args").removeAttr("readonly");
			$("#sftp-select-path").removeAttr("disabled");
		}
		$("#sftp-exec-path").val(path);
		$("#sftp-exec-args").val(command_line);
	} else if(type == 3) {
		if (build_in == 1) {
			$("#telnet-exec-args").attr("readonly", "readonly");
			$("#telnet-select-path").attr("disabled", "disabled");
		} else {
			$("#telnet-exec-args").removeAttr("readonly");
			$("#telnet-select-path").removeAttr("disabled");
		}
		$("#telnet-exec-path").val(path);
		$("#telnet-exec-args").val(command_line);
	}
}

$(document).ready(function () {
	get_config();
	// get_client_config_list(1);
	// get_client_config_list(2);
	// get_client_config_list(3);

	$("#ssh-client-type").change(function () {
		var i = 0;
		var name = $("#ssh-client-type").val();
		var item = g_ssh_config_dict[name];
		init_config_param(1, item.build_in, item.path, item.commandline);
		g_current_ssh = item.name;
	});
	$("#ssh-select-path").click(function () {
		open_exist_file(function (code, path) {
			if (code == 0) {
				$("#ssh-exec-path").val(path);
			} else {
				console.log("can not select file.");
			}
		});
	});
	$("#ssh-btn-save").click(function () {
		var name = $("#ssh-client-type").val();
		var path = $("#ssh-exec-path").val();
		if (path == "") {
			alert("请选择路径");
			return;
		}
		var command_line = $("#ssh-exec-args").val();
		if (command_line == "") {
			alert("请输入命令行");
			return;
		}
		set_current_client_config(1, name, path, command_line);
	});


	$("#sftp-client-type").change(function () {
		var i = 0;
		var name = $("#sftp-client-type").val();
		var item = g_sftp_config_dict[name];
		init_config_param(2, item.build_in, item.path, item.commandline);
		g_current_sftp = item.name;
	});
	$("#sftp-select-path").click(function () {
		open_exist_file(function (code, path) {
			if (code == 0) {
				$("#sftp-exec-path").val(path);
			} else {
				console.log("can not select file.");
			}
		});
	});
	$("#sftp-btn-save").click(function () {
		var name = $("#sftp-client-type").val();
		var path = $("#sftp-exec-path").val();
		if (path == "") {
			alert("请选择路径");
			return;
		}
		var command_line = $("#sftp-exec-args").val();
		if (command_line == "") {
			alert("请输入命令行");
			return;
		}
		set_current_client_config(2, name, path, command_line);
	});


	$("#telnet-client-type").change(function () {
		var i = 0;
		var name = $("#telnet-client-type").val();
		var item = g_telnet_config_dict[name];
		init_config_param(3, item.build_in, item.path, item.commandline);
		g_current_telnet = item.name;
	});
	$("#telnet-select-path").click(function () {
		open_exist_file(function (code, path) {
			if (code == 0) {
				$("#telnet-exec-path").val(path);
			} else {
				console.log("can not select file.");
			}
		});
	});
	$("#telnet-btn-save").click(function () {
		var name = $("#telnet-client-type").val();
		var path = $("#telnet-exec-path").val();
		if (path == "") {
			alert("请选择路径");
			return;
		}
		var command_line = $("#telnet-exec-args").val();
		if (command_line == "") {
			alert("请输入命令行");
			return;
		}
		set_current_client_config(3, name, path, command_line);
	});
});