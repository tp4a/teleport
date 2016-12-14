/*! ywl v1.0.1, (c)2015 eomsoft.net */
"use strict";
var OS_TYPE_WINDOWS = 1;
var OS_TYPE_LINUX = 2;
var PROTOCOL_TYPE_RDP = 1;
var PROTOCOL_TYPE_SSH = 2;
var PROTOCOL_TYPE_TELNET = 3;
var AUTH_TYPE_PASSWORD = 1;
var AUTH_TYPE_SSHKEY = 2;
var AUTH_NONE = 0;
var g_cert_list = {};
var g_group_list = {};
var g_user_host_list = null;

ywl.on_init = function (cb_stack, cb_args) {
	ywl.create_host_table(cb_stack, cb_args);
	ywl.create_user_host_table(cb_stack, cb_args);
	cb_stack.exec();
};


ywl.create_host_table = function (cb_stack, cb_args) {
	var dom_id = '#ywl_host_list';

	//===================================
	// 创建页面控件对象
	//===================================
	// 表格数据
	var host_table_options = {
		selector: dom_id + " [ywl-table='host-list']",
		data_source: {
			type: 'ajax-post',
			url: '/host/list'
		},
		//render: ywl.create_table_render(ywl.on_host_table_render_created),//ywl_TableRender.create();
		column_default: {sort: false, header_align: 'center', cell_align: 'center'},
		columns: [
			{title: '<input type="checkbox" id="host-select-all" value="">', key: 'select_all', sort: false, width: 24, render: 'make_check_box', fields: {id: 'host_id'}},
			{title: "远程协议", key: "auth_list", width: 280, header_align: 'left', cell_align: 'left', sort: false, render: 'auth_list', fields: {id: 'host_id', protocol: 'protocol', auth_list: 'auth_list'}},
			{title: "主机", key: "host_id", width: 240, sort: true, render: 'host_id', fields: {id: 'host_ip', host_desc: 'host_desc', host_port: 'host_port'}},
			{title: "分组", key: "group_name", width: 240},
			{title: "系统", key: "host_sys_type", width: 64, render: 'sys_type', fields: {sys_type: 'host_sys_type'}},
			{title: "状态", key: "host_lock", render: 'host_lock', fields: {host_lock: 'host_lock'}},
		],
		paging: {selector: dom_id + " [ywl-paging='host-list']", per_page: paging_normal},

		// 可用的属性设置
		//have_header: true or false

		// 可用的回调函数
		on_created: ywl.on_host_table_created,
		on_header_created: ywl.on_host_table_header_created

		// 可重载的函数（在on_created回调函数中重载）
		// on_render_created
		// on_header_created
		// on_paging_created
		// on_data_loaded
		// on_row_rendered
		// on_table_rendered
		// on_cell_created
		// on_begin_load
		// on_after_load

		// 可用的函数
		// load_data
		// cancel_load
		// set_data
		// add_row
		// remove_row
		// get_row
		// update_row
		// clear
		// reset_filter
	};

	var host_table = ywl.create_table(host_table_options);

	// 主机分组过滤器
	g_cert_list = ywl.page_options.cert_list;
	g_group_list = ywl.page_options.group_list;
	ywl.create_table_filter_host_group(host_table, dom_id + " [ywl-filter='host-group']", g_group_list);

	ywl.create_table_filter_system_type(host_table, dom_id + " [ywl-filter='system-type']");
	// 搜索框
	ywl.create_table_filter_search_box(host_table, dom_id + " [ywl-filter='search']");

	//======================================================
	// 事件绑定
	//======================================================
	$("#btn-add-host").click(function () {
//		var _data_list = [];
		var host_list = [];
		var _host_id_objs = $(host_table.selector + " tbody tr td [data-check-box]");
		$.each(_host_id_objs, function (i, _host_id_objs) {
			if ($(_host_id_objs).is(':checked')) {
				var _row_data = host_table.get_row(_host_id_objs);
				var data = {host_id: _row_data.host_id, row_id: _row_data.ywl_row_id};
				host_list.push(data)
			}
		});
		console.log('host_list', host_list);
		var user_dict = {};
		var _user_objs = $(host_table.selector + " tbody tr td [user-check-box]");
		$.each(_user_objs, function (i, _user_objs) {
			if ($(_user_objs).is(':checked')) {
				var _row_data = host_table.get_row(_user_objs);
				var host_auth_id = parseInt($(_user_objs).attr('user-check-box'));
//				var data = {host_id: _row_data.host_id, row_id: _row_data.ywl_row_id};

				if (typeof(user_dict[_row_data.ywl_row_id]) == "undefined") {
					user_dict[_row_data.ywl_row_id] = [];
				}
				user_dict[_row_data.ywl_row_id].push(host_auth_id);
			}
		});
		console.log('user_dict', user_dict);
		var length = 0;
		var args = {};

		for (var i = 0; i < host_list.length; i++) {
			var host_id = host_list[i].host_id;
			var row_id = host_list[i].row_id;
			var host_auth_list = user_dict[row_id];
			if (typeof(host_auth_list) == "undefined") {
				continue;
			}
			args[host_id] = host_auth_list;
			length += 1;
		}
		console.log('args', args);
		if (length === 0) {
			ywl.notify_error('请先选择要批量授权的主机！');
			return;
		}

		ywl.ajax_post_json('/user/alloc-host-user', {host_list: args, user_name: ywl.page_options.user_name},
			function (ret) {
				g_user_host_list.reload();
				ywl.notify_success("主机授权操作成功！");
			},
			function () {
				ywl.notify_error("主机授权操作时发生错误！");
			}
		);
	});

	// 将刷新按钮点击事件绑定到表格的重新加载函数上，这样，点击刷新就导致表格数据重新加载。
	$(dom_id + " [ywl-filter='reload']").click(host_table.reload);

	cb_stack
		.add(host_table.load_data)
		.add(host_table.init)
		.exec();
};

ywl.create_user_host_table = function (cb_stack, cb_args) {
	var dom_id = '#ywl_user_host_list';
	//===================================
	// 创建页面控件对象
	//===================================
	// 表格数据
	var host_table_options = {
		selector: dom_id + " [ywl-table='host-list']",
		data_source: {
			type: 'ajax-post',
			url: '/user/host-list'
		},
		//render: ywl.create_table_render(ywl.on_host_table_render_created),//ywl_TableRender.create();
		column_default: {sort: false, header_align: 'center', cell_align: 'center'},
		columns: [
			{title: '<input type="checkbox" id="user-host-select-all" value="">', key: 'select_all', sort: false, width: 24, render: 'make_check_box', fields: {id: 'host_id'}},
			{title: "远程协议", key: "auth_list", header_align: 'left', cell_align: 'left', render: 'auth_list', fields: {id: 'host_id', protocol: 'protocol', auth_list: 'auth_list'}},
			{title: "主机", key: "host_id", width: 240, sort: true, render: 'host_id', fields: {id: 'host_ip', host_desc: 'host_desc', host_port: 'host_port'}},
			{title: "分组", key: "group_name", width: 240},
			{title: "系统", key: "host_sys_type", width: 64, render: 'sys_type', fields: {sys_type: 'host_sys_type'}},
			{title: "状态", key: "host_lock", render: 'host_lock', fields: {host_lock: 'host_lock'}},
			{title: "操作", key: "action", width: 160, render: 'make_action_btn', fields: {id: 'host_id', host_lock: 'host_lock'}}
		],
		paging: {selector: dom_id + " [ywl-paging='host-list']", per_page: paging_normal},

		// 可用的属性设置
		//have_header: true or false

		// 可用的回调函数
		on_created: ywl.on_user_host_table_created,
		on_header_created: ywl.on_user_host_table_header_created

		// 可重载的函数（在on_created回调函数中重载）
		// on_render_created
		// on_header_created
		// on_paging_created
		// on_data_loaded
		// on_row_rendered
		// on_table_rendered
		// on_cell_created
		// on_begin_load
		// on_after_load

		// 可用的函数
		// load_data
		// cancel_load
		// set_data
		// add_row
		// remove_row
		// get_row
		// update_row
		// clear
		// reset_filter
	};

	var host_table = ywl.create_table(host_table_options);
	g_user_host_list = host_table;
	// 主机分组过滤器
	g_group_list = ywl.page_options.group_list;
	ywl.create_table_filter_host_group(host_table, dom_id + " [ywl-filter='host-group']", g_group_list);

	ywl.create_table_filter_system_type(host_table, dom_id + " [ywl-filter='system-type']");
	// 搜索框
	ywl.create_table_filter_search_box(host_table, dom_id + " [ywl-filter='search']");

	ywl.create_table_filter_user_name(host_table);

	//======================================================
	// 事件绑定
	//======================================================
	$("#btn-delete-host").click(function () {
		var _data_list = [];
		var _objs = $(host_table.selector + " tbody tr td [data-check-box]");
		$.each(_objs, function (i, _obj) {
			if ($(_obj).is(':checked')) {
				var _row_data = host_table.get_row(_obj);
				var data = {host_id: _row_data.host_id, row_id: _row_data.ywl_row_id};
				_data_list.push(data);
			}
		});
		if (_data_list.length === 0) {
			ywl.notify_error('请先选择要回收授权的主机！');
			return;
		}

		var _fn_sure = function (cb_stack, cb_args) {
			// var _data_list = cb_args._data_list || [];
			var host_list = [];
			for (var i = 0; i < _data_list.length; i++) {
				var host_id = _data_list[i].host_id;
				host_list.push(host_id);
			}
			host_list.push(host_id);
			ywl.ajax_post_json('/user/delete-host', {host_list: host_list, user_name: ywl.page_options.user_name},
				function (ret) {
					g_user_host_list.reload();
					ywl.notify_success('成功回收主机授权！');
				},
				function () {
					ywl.notify_error('回收主机授权时发生错误！');
				}
			);
		};

		var cb_stack = CALLBACK_STACK.create();
		ywl.dlg_confirm(cb_stack,
			{
				msg: '<p>此操作不可恢复！！</p><p>您确定要回收选中主机的授权吗？</p>',
				fn_yes: _fn_sure
				// cb_args: _data_list
			});


	});

	// $("#user-host-titile").html('已经授权给用户' + ywl.page_options.user_name + "的主机列表");
	// 将刷新按钮点击事件绑定到表格的重新加载函数上，这样，点击刷新就导致表格数据重新加载。
	$(dom_id + " [ywl-filter='reload']").click(host_table.reload);

	cb_stack
		.add(host_table.load_data)
		.add(host_table.init)
		.exec();
};

// 扩展/重载表格的功能
ywl.on_host_table_created = function (tbl) {

	tbl.on_cell_created = function (row_id, col_key, cell_obj) {
		if (col_key == 'select_all') {
			// 选择
			$('#host-select-' + row_id).click(function () {
				console.log('host-sel');
				var _all_checked = true;
				var _objs = $(tbl.selector + ' tbody').find('[data-check-box]');
				$.each(_objs, function (i, _obj) {
					if (!$(_obj).is(':checked')) {
						_all_checked = false;
						return false;
					}
				});

				var select_all_dom = $('#host-select-all');
				if (_all_checked) {
					select_all_dom.prop('checked', true);
				} else {
					select_all_dom.prop('checked', false);
				}
				if ($(this).is(':checked')) {
					$(this).parent().parent().parent().find("[user-check-box]").prop('checked', true);
				} else {
					$(this).parent().parent().parent().find("[user-check-box]").prop('checked', false);
				}
				//ywl.update_add_to_batch_btn();
			});

		} else if (col_key == 'host_id') {
			// 为主机描述绑定点击事件
			var _link = $(cell_obj).find(" [ywl-host-desc]");
			_link.click(function () {
				var row_data = tbl.get_row(row_id);
				ywl.create_dlg_modify_host_desc(tbl, row_data.ywl_row_id, row_data.host_id, row_data.host_ip, row_data.host_desc).show(_link);
			});
		} else if (col_key == 'auth_list') {
			$('#user-check-box-row-' + row_id).click(function () {
				var _checked = false;
				var _objs = $(this).parent().parent().parent().parent().find('[user-check-box]');
				$.each(_objs, function (i, _obj) {
					if ($(_obj).is(':checked')) {
						_checked = true;
						return false;
					}
				});
				var select = $('#host-select-' + row_id);

				if (_checked) {
					select.prop('checked', true);
				} else {
					select.prop('checked', false);
				}
				console.log("xxxxxxx");
			});
		}
	};

	// 重载表格渲染器的部分渲染方式，加入本页面相关特殊操作
	tbl.on_render_created = function (render) {

		render.auth_list = function (row_id, fields) {
			// TODO: 这里应该从fields里拿一个数组，是本主机上开放的所有远程访问协议和登录账号的组合
			var auth_list = fields.auth_list;
			var protocol = fields.protocol;
			var ret = [];

			if (auth_list.length == 0) {
				ret.push('<span class="badge badge-danger">尚未添加系统用户</span>');
				return ret.join('');
			}

			for (var i = 0; i < auth_list.length; i++) {
				var auth = auth_list[i];
				ret.push('<div class="remote-action-group">');
				if (protocol == PROTOCOL_TYPE_RDP) {

					ret.push('<ul>');
					ret.push('<li class="remote-action-chk-protocol"><input type="checkbox" id=user-check-box-row-' + parseInt(row_id) + ' user-check-box=' + auth.host_auth_id + '"> RDP</label></li>');
					ret.push('<li class="remote-action-username">' + auth.user_name + '</li>');
					if (auth.auth_mode == AUTH_TYPE_PASSWORD) {
						ret.push('<li class="remote-action-password">密码</li>');
					} else if (auth.auth_mode == AUTH_TYPE_SSHKEY) {
						ret.push('<li class="remote-action-sshkey">私钥</li>');
					} else if (auth.auth_mode == AUTH_NONE) {
						ret.push('<li class="remote-action-noauth">无</li>');
					} else {
						ret.push('<li class="remote-action-noauth">未知</li>');
					}
					ret.push('</ul>');

				} else if (protocol == PROTOCOL_TYPE_SSH) {
					ret.push('<ul>');
					ret.push('<li class="remote-action-chk-protocol"><input type="checkbox" id=user-check-box-row-' + parseInt(row_id) + ' user-check-box=' + auth.host_auth_id + '"> SSH</label></li>');
					ret.push('<li class="remote-action-username">' + auth.user_name + '</li>');
					if (auth.auth_mode == AUTH_TYPE_PASSWORD) {
						ret.push('<li class="remote-action-password">密码</li>');
					} else if (auth.auth_mode == AUTH_TYPE_SSHKEY) {
						ret.push('<li class="remote-action-sshkey">私钥</li>');
					} else if (auth.auth_mode == AUTH_NONE) {
						ret.push('<li class="remote-action-noauth">无</li>');
					} else {
						ret.push('<li class="remote-action-noauth">未知</li>');
					}
					ret.push('</ul>');
				} else if (protocol == PROTOCOL_TYPE_TELNET) {
					ret.push('<ul>');
					ret.push('<li class="remote-action-chk-protocol"><input type="checkbox" id=user-check-box-row-' + parseInt(row_id) + ' user-check-box=' + auth.host_auth_id + '"> TELNET</label></li>');
					ret.push('<li class="remote-action-username">' + auth.user_name + '</li>');
					if (auth.auth_mode == AUTH_TYPE_PASSWORD) {
						ret.push('<li class="remote-action-password">密码</li>');
					} else if (auth.auth_mode == AUTH_TYPE_SSHKEY) {
						ret.push('<li class="remote-action-sshkey">私钥</li>');
					} else if (auth.auth_mode == AUTH_NONE) {
						ret.push('<li class="remote-action-noauth">无</li>');
					} else {
						ret.push('<li class="remote-action-noauth">未知</li>');
					}
					ret.push('</ul>');
				} else {
					ret.push('<span class="badge badge-danger">没有添加系统用户</span>');
				}
				ret.push('</div>');
			}
			return ret.join('');
//			var ret = [];
//
//			return ret.join('');
		};

		render.host_id = function (row_id, fields) {
			var ret = '<span class="host-id">' + fields.id + ':' + fields.host_port + '</span>';
			ret += '<span class="host-desc">' + fields.host_desc + '</span>';

			return ret;
		};
		render.pro_type = function (row_id, fields) {
			switch (fields.pro_type) {
				case 1:
					return '<span class="badge badge-primary">RDP协议</span>';
				case 2:
					return '<span class="badge badge-success">SSH协议</span>';
				default:
					return '<span class="badge badge-danger">未知</span>';
			}
		};
		render.host_auth = function (row_id, fields) {
			switch (fields.host_auth) {
				case 0:
					return '<span class="badge badge-danger">无认证</span>';
				case 1:
					return '<span class="badge badge-primary">用户名/密码</span>';
				case 2:
					return '<span class="badge badge-success">用户名/SSH密钥</span>';
				default:
					return '<span class="badge badge-danger">未知</span>';
			}
		};
		render.host_lock = function (row_id, fields) {
			switch (fields.host_lock) {
				case 0:
					return '<span class="badge badge-success">允许访问</span>';
				case 1:
					return '<span class="badge badge-danger">禁止访问</span>';
				default:
					return '<span class="badge badge-danger">未知</span>';
			}
		};
		render.make_check_box = function (row_id, fields) {
			return '<span><input type="checkbox" data-check-box="' + fields.id + '" id="host-select-' + row_id + '"></span>';
		};
		// render.make_action_btn = function (row_id, fields) {
		// 	var ret = [];
		// 	ret.push('<a href="javascript:;" class="btn btn-primary btn-danger btn-group-sm" ywl-btn-delete="' + fields.id + '">删除</a>');
		// 	return ret.join('');
		// }

	};
};

ywl.on_host_table_header_created = function (tbl) {
	$('#host-select-all').click(function () {
		var _is_selected = $(this).is(':checked');
		$(tbl.selector + ' tbody').find('[data-check-box]').prop('checked', _is_selected);
		$(tbl.selector + ' tbody').find('[user-check-box]').prop('checked', _is_selected);

//        #################################################
		//ywl.update_add_to_batch_btn();
	});
};

ywl.on_user_host_table_header_created = function (tbl) {
	$('#user-host-select-all').click(function () {
		var _is_selected = $(this).is(':checked');
		$(tbl.selector + ' tbody').find('[data-check-box]').prop('checked', _is_selected);
		//ywl.update_add_to_batch_btn();
	});
};

ywl.on_user_host_table_created = function (tbl) {

	tbl.on_cell_created = function (row_id, col_key, cell_obj) {
		if (col_key == 'select_all') {
			// 选择
			$('#user-host-select-' + row_id).click(function () {
				var _all_checked = true;
				var _objs = $(tbl.selector + ' tbody').find('[data-check-box]');
				$.each(_objs, function (i, _obj) {
					if (!$(_obj).is(':checked')) {
						_all_checked = false;
						return false;
					}
				});

				var select_all_dom = $('#user-host-select-all');
				if (_all_checked) {
					select_all_dom.prop('checked', true);
				} else {
					select_all_dom.prop('checked', false);
				}

				//ywl.update_add_to_batch_btn();
			});

		} else if (col_key == 'host_id') {
			// 为主机描述绑定点击事件
			var _link = $(cell_obj).find(" [ywl-host-desc]");
			_link.click(function () {
				var row_data = tbl.get_row(row_id);
				ywl.create_dlg_modify_host_desc(tbl, row_data.ywl_row_id, row_data.host_id, row_data.host_ip, row_data.host_desc).show(_link);
			});
		} else if (col_key == 'action') {
			var row_data = tbl.get_row(row_id);
			$(cell_obj).find('[ywl-btn-delete]').click(function () {
				var host_id = row_data.host_id;
				var _fn_sure = function (cb_stack, cb_args) {
					var host_list = [];
					host_list.push(host_id);
					ywl.ajax_post_json('/user/delete-host', {host_list: host_list, user_name: ywl.page_options.user_name},
						function (ret) {
							tbl.remove_row(row_id);
							ywl.notify_success('删除用户拥有主机成功');
						},
						function () {
							ywl.notify_error('删除用户拥有主机失败');
						}
					);
				};
				var cb_stack = CALLBACK_STACK.create();

				ywl.dlg_confirm(cb_stack,
					{
						msg: '<p>此操作不可恢复！！</p><p>您确定要回收选中主机的授权吗？</p>',
						fn_yes: _fn_sure
					});
			});
		} else if (col_key == 'auth_list') {

			$(cell_obj).find('[data-remove]').click(function () {
				var row_data = tbl.get_row(row_id);
				var auth_id = parseInt($(this).attr('data-remove'));
//				var host_id = row_data.host_id;
				var _fn_sure = function (cb_stack, cb_args) {
					var auth_id_list = [];
					auth_id_list.push(auth_id);
					ywl.ajax_post_json('/user/delete-host-user', {auth_id_list: auth_id_list, user_name: ywl.page_options.user_name},
						function (ret) {
							if (ret.code == 0) {
								var auth_list = [];
								for (var i = 0; i < row_data.auth_list.length; i++) {
									var auth = row_data.auth_list[i];
									if (auth.auth_id == auth_id) {
										continue;
									} else {
										auth_list.push(auth);
									}
								}
								console.log('auth_list', auth_list);
								if (auth_list.length == 0) {
									tbl.remove_row(row_id);
								} else {
									tbl.update_row(row_id, {auth_list: auth_list});
								}
								ywl.notify_success('删除成功');
							} else {
								ywl.notify_error('删除成功失败' + ret.code);
							}
							console.log('row_data', row_data);
//							tbl.remove_row(row_id);

						},
						function () {
							ywl.notify_error('删除成功失败');
						}
					);
				};
				var cb_stack = CALLBACK_STACK.create();

				ywl.dlg_confirm(cb_stack,
					{
						msg: '<p>此操作不可恢复！！</p><p>您确定要回收选中的用户授权吗？</p>',
						fn_yes: _fn_sure
					});
			});
		}
	};

	// 重载表格渲染器的部分渲染方式，加入本页面相关特殊操作
	tbl.on_render_created = function (render) {
		render.auth_list = function (row_id, fields) {
			var auth_list = fields.auth_list;
			var protocol = fields.protocol;
			var ret = [];

			if (auth_list.length == 0) {
				ret.push('<span class="badge badge-danger">尚未添加系统用户</span>');
				return ret.join('');
			}

			for (var i = 0; i < auth_list.length; i++) {
				var auth = auth_list[i];
				ret.push('<div class="remote-action-group">');
				switch (protocol) {
					case PROTOCOL_TYPE_RDP:

						ret.push('<ul>');
						ret.push('<li class="remote-action-chk-protocol">RDP</li>');
						ret.push('<li class="remote-action-username">' + auth.user_name + '</li>');
						if (auth.auth_mode == AUTH_TYPE_PASSWORD) {
							ret.push('<li class="remote-action-password">密码</li>');
						} else if (auth.auth_mode == AUTH_TYPE_SSHKEY) {
							ret.push('<li class="remote-action-sshkey">私钥</li>');
						} else if (auth.auth_mode == AUTH_NONE) {
							ret.push('<li class="remote-action-noauth">无</li>');
						} else {
							ret.push('<li class="remote-action-noauth">未知</li>');
						}
						ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-danger" data-remove="' + auth.auth_id + '" data-sub-protocol="1">收回</a></li>');
						break;
					case PROTOCOL_TYPE_SSH:
						ret.push('<ul>');
						ret.push('<li class="remote-action-chk-protocol">SSH</li>');
						ret.push('<li class="remote-action-username">' + auth.user_name + '</li>');
						if (auth.auth_mode == AUTH_TYPE_PASSWORD) {
							ret.push('<li class="remote-action-password">密码</li>');
						} else if (auth.auth_mode == AUTH_TYPE_SSHKEY) {
							ret.push('<li class="remote-action-sshkey">私钥</li>');
						} else if (auth.auth_mode == AUTH_NONE) {
							ret.push('<li class="remote-action-noauth">无</li>');
						} else {
							ret.push('<li class="remote-action-noauth">未知</li>');
						}
						ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-danger" data-remove="' + auth.auth_id + '" data-sub-protocol="2">收回</a></li>');
						ret.push('</ul>');
						break;
					case PROTOCOL_TYPE_TELNET:
						ret.push('<ul>');
						ret.push('<li class="remote-action-chk-protocol">TELENT</li>');
						ret.push('<li class="remote-action-username">' + auth.user_name + '</li>');
						if (auth.auth_mode == AUTH_TYPE_PASSWORD) {
							ret.push('<li class="remote-action-password">密码</li>');
						} else if (auth.auth_mode == AUTH_TYPE_SSHKEY) {
							ret.push('<li class="remote-action-sshkey">私钥</li>');
						} else if (auth.auth_mode == AUTH_NONE) {
							ret.push('<li class="remote-action-noauth">无</li>');
						} else {
							ret.push('<li class="remote-action-noauth">未知</li>');
						}
						ret.push('<li class="remote-action-btn"><a href="javascript:;" class="btn btn-danger" data-remove="' + auth.auth_id + '" data-sub-protocol="2">收回</a></li>');
						ret.push('</ul>');
						break;
					default:
						ret.push('<span class="badge badge-danger">此主机尚未添加系统用户</span>');
				}
				ret.push('</div>');
			}


			return ret.join('');
		};
		render.host_id = function (row_id, fields) {
			var ret = '<span class="host-id">' + fields.id + ':' + fields.host_port + '</span>';
			ret += '<span class="host-desc">' + fields.host_desc + '</span>';

			return ret;
		};
		render.pro_type = function (row_id, fields) {
			switch (fields.pro_type) {
				case 1:
					return '<span class="badge badge-primary">RDP协议</span>';
				case 2:
					return '<span class="badge badge-success">SSH协议</span>';
				default:
					return '<span class="badge badge-danger">未知</span>';
			}
		};
		render.host_auth = function (row_id, fields) {
			switch (fields.host_auth) {
				case 0:
					return '<span class="badge badge-danger">无认证</span>';
				case 1:
					return '<span class="badge badge-primary">用户名/密码</span>';
				case 2:
					return '<span class="badge badge-success">用户名/SSH密钥</span>';
				default:
					return '<span class="badge badge-danger">未知</span>';
			}
		};
		render.host_lock = function (row_id, fields) {
			switch (fields.host_lock) {
				case 0:
					return '<span class="badge badge-success">允许访问</span>';
				case 1:
					return '<span class="badge badge-danger">禁止访问</span>';
				default:
					return '<span class="badge badge-danger">未知</span>';
			}
		};
		render.make_check_box = function (row_id, fields) {
			return '<span><input type="checkbox" data-check-box="' + fields.id + '" id="user-host-select-' + row_id + '"></span>';
		};
		render.make_action_btn = function (row_id, fields) {
			var ret = [];
			ret.push('<a href="javascript:;" class="btn btn-sm btn-primary btn-danger btn-group-sm" ywl-btn-delete="' + fields.id + '"><i class="fa fa-trash-o fa-fw"></i> 收回授权</a>');
			return ret.join('');
		}

	};
};


ywl.create_table_filter_user_name = function (tbl) {
	var _tblf_st = {};

	// 此表格绑定的DOM对象的ID，用于JQuery的选择器
	// 此过滤器绑定的表格控件
	_tblf_st._table_ctrl = tbl;
	_tblf_st._table_ctrl.append_filter_ctrl(_tblf_st);

	// 过滤器内容
	_tblf_st.filter_name = 'account_name';
	_tblf_st.filter_default = ywl.page_options.user_name;
	_tblf_st.filter_value = ywl.page_options.user_name;

	_tblf_st.get_filter = function () {
		var _ret = {};
		_ret[_tblf_st.filter_name] = _tblf_st.filter_value;
		return _ret;
	};

	_tblf_st.reset = function (cb_stack, cb_args) {
		return;
		//ywl.assist.set_cookie(cb_stack, {k: _tblf_st.filter_name, v: _tblf_st.filter_default});
	};

	_tblf_st.init = function (cb_stack) {
		return;

	};

	return _tblf_st;
};
