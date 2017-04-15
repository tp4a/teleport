"use strict";

var g_cert_dlg_info = null;

ywl.on_init = function (cb_stack, cb_args) {
	var dom_id = '#ywl_cert_list';

	//===================================
	// 创建页面控件对象
	//===================================
	// 表格数据
	var host_table_options = {
		selector: dom_id + " [ywl-table='cert-list']",
		data_source: {
			type: 'ajax-post',
			url: '/cert/list'
		},
		column_default: {sort: false, header_align: 'center', cell_align: 'center'},
		columns: [
			{title: "编号", key: "cert_id", width: 80},
			{title: "密钥名称", key: "cert_name", width: 240, header_align: 'left', cell_align: 'left'},
			{title: "公钥", key: "cert_pub", render: 'cert_pub', header_align: 'left', cell_align: 'left'},
			//{title: "私钥", key: "cert_pri"},
			{title: "操作", key: "action", width: 180, render: 'make_action_btn', fields: {id: 'cert_id'}}
		],
		paging: {selector: dom_id + " [ywl-paging='cert-list']", per_page: paging_normal},

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
	g_cert_dlg_info = ywl.create_cert_info_dlg(host_table);
	$(dom_id + " [ywl-filter='reload']").click(host_table.reload);
	$("#btn-add-cert").click(function () {
		g_cert_dlg_info.create_show();
	});
	cb_stack
		.add(host_table.load_data)
		.add(host_table.init)
		.exec();
};

// 扩展/重载表格的功能
ywl.on_host_table_created = function (tbl) {

	tbl.on_cell_created = function (row_id, col_key, cell_obj) {
		if (col_key === 'action') {
			var row_data = tbl.get_row(row_id);
			//console.log('row_data', row_data);
			$(cell_obj).find('[ywl-btn-edit]').click(function () {
				g_cert_dlg_info.update_show(row_data.cert_name, row_data.cert_id, row_data.cert_pub, row_data.cert_pri, row_id);
			});
			$(cell_obj).find('[ywl-btn-delete]').click(function () {
				var cert_id = row_data.cert_id;
				var _fn_sure = function (cb_stack, cb_args) {
					ywl.ajax_post_json('/host/delete-cert', {cert_id: cert_id},
						function (ret) {
							if (ret.code === TPE_OK) {
								tbl.remove_row(row_id);
								ywl.notify_success('删除成功！');
							} else if (ret.code === -2) {
								ywl.notify_error('不能删除，有主机使用了此密钥！');
							} else {
								ywl.notify_error('删除失败！错误代码：'+ret.code);
							}

						},
						function () {
							ywl.notify_error('网络通讯失败！');
						}
					);
				};
				var cb_stack = CALLBACK_STACK.create();

				ywl.dlg_confirm(cb_stack,
					{
						msg: '<p><strong>删除操作不可恢复！！</strong></p><p>您确定要删除此密钥吗？</p>',
						fn_yes: _fn_sure
					});
			});

		}
	};

	// 重载表格渲染器的部分渲染方式，加入本页面相关特殊操作
	tbl.on_render_created = function (render) {
		render.make_action_btn = function (row_id, fields) {
			var ret = [];
			ret.push('<a href="javascript:;" class="btn btn-primary btn-success btn-group-sm" ywl-btn-edit="' + fields.id + '">编辑</a>&nbsp');
			ret.push('<a href="javascript:;" class="btn btn-primary btn-danger btn-group-sm" ywl-btn-delete="' + fields.id + '">删除</a>');
			return ret.join('');
		};

		render.cert_pub = function (row_id, fields) {
			return '<textarea class="textarea-code textarea-resize-none cert_pub" readonly="readonly">' + fields.cert_pub + '</textarea>';
		};
	};
};

ywl.on_host_table_header_created = function (tbl) {
};

ywl.create_cert_info_dlg = function (tbl) {
	var cert_info_dlg = {};
	cert_info_dlg.dom_id = "#dialog_cert_info";
	cert_info_dlg.update = 1;
	cert_info_dlg.tbl = tbl;
	cert_info_dlg.cert_name = '';
	cert_info_dlg.cert_id = 0;
	cert_info_dlg.cert_pub = 0;
	cert_info_dlg.cert_pri = 0;
	cert_info_dlg.row_id = 0;
	cert_info_dlg.title = '';

	cert_info_dlg.update_show = function (cert_name, cert_id, cert_pub, cert_pri, row_id) {
		cert_info_dlg.update = 1;
		cert_info_dlg.title = '编辑SSH密钥';
		cert_info_dlg.init(cert_name, cert_id, cert_pub, cert_pri, row_id);
		var msg = '如果您只是希望修改密钥名称，那么本区域可以忽略不填写！';
		$(cert_info_dlg.dom_id + ' #dlg-cert-pub').attr('placeholder', msg);
		$(cert_info_dlg.dom_id + ' #dlg-cert-pri').attr('placeholder', msg);
		$(cert_info_dlg.dom_id).modal();
	};
	cert_info_dlg.create_show = function () {
		cert_info_dlg.update = 0;
		cert_info_dlg.title = '添加SSH密钥';
		cert_info_dlg.init('', 0, '', '', 0);
		$(cert_info_dlg.dom_id + ' #dlg-cert-pub').attr('placeholder', '');
		$(cert_info_dlg.dom_id + ' #dlg-cert-pri').attr('placeholder', '');
		$(cert_info_dlg.dom_id).modal();
	};
	cert_info_dlg.hide = function () {
		$(cert_info_dlg.dom_id).modal('hide');
	};

	cert_info_dlg.init = function (cert_name, cert_id, cert_pub, cert_pri, row_id) {
		cert_info_dlg.cert_name = cert_name;
		cert_info_dlg.cert_id = cert_id;
		cert_info_dlg.cert_pub = cert_pub;
		cert_info_dlg.cert_pri = '';//cert_pri;
		cert_info_dlg.row_id = row_id;
		cert_info_dlg.init_dlg();
	};

	cert_info_dlg.init_dlg = function () {
		$(cert_info_dlg.dom_id + ' #title').html(cert_info_dlg.title);
		$(cert_info_dlg.dom_id + ' #dlg-cert-name').val(cert_info_dlg.cert_name);
		$(cert_info_dlg.dom_id + ' #dlg-cert-pub').val(cert_info_dlg.cert_pub);
//		$(cert_info_dlg.dom_id + ' #dlg-cert-pri').val(cert_info_dlg.cert_pri);
		$(cert_info_dlg.dom_id + ' #dlg-cert-pri').val('');
	};

	cert_info_dlg.check_args = function () {
		cert_info_dlg.cert_name = $(cert_info_dlg.dom_id + ' #dlg-cert-name').val();
		cert_info_dlg.cert_pub = $(cert_info_dlg.dom_id + ' #dlg-cert-pub').val();
		cert_info_dlg.cert_pri = $(cert_info_dlg.dom_id + ' #dlg-cert-pri').val();
		if (cert_info_dlg.cert_name === '') {
			ywl.notify_error('必须为密钥设置一个名称！');
			return false;
		}
		if (cert_info_dlg.cert_pub === '') {
			ywl.notify_error('必须填写公钥内容！');
			return false;
		}
		if (cert_info_dlg.update === 0 && cert_info_dlg.cert_pri.length === 0) {
			ywl.notify_error('添加密钥时，必须填写私钥内容！');
			return false;
		}
		return true;
	};

	cert_info_dlg.post = function () {
		if (cert_info_dlg.update === 1) {
			ywl.ajax_post_json('/host/update-cert', {cert_id: cert_info_dlg.cert_id, cert_name: cert_info_dlg.cert_name, cert_pub: cert_info_dlg.cert_pub, cert_pri: cert_info_dlg.cert_pri},
				function (ret) {
					var update_args = {cert_id: cert_info_dlg.cert_id, cert_name: cert_info_dlg.cert_name};
					cert_info_dlg.tbl.update_row(cert_info_dlg.row_id, update_args);
					ywl.notify_success('密钥更新成功！');
					cert_info_dlg.hide();
				},
				function () {
					ywl.notify_error('密钥更新失败！');
				}
			);
		} else {
			ywl.ajax_post_json('/host/add-cert', {cert_name: cert_info_dlg.cert_name, cert_pub: cert_info_dlg.cert_pub, cert_pri: cert_info_dlg.cert_pri},
				function (ret) {
                    if(ret.code === TPE_OK){
                        cert_info_dlg.tbl.reload();
                        ywl.notify_success('密钥添加成功！');
                        cert_info_dlg.hide();
                    }else if(ret.code === TPE_NO_CORE_SERVER){
                        ywl.notify_error('错误，没有启动核心服务！');
                    }else{
                        ywl.notify_error('密钥添加失败！code:' + ret.code);
                    }
		
				},
				function (ret) {
					ywl.notify_error('密钥添加失败！');
				}
			);
		}
		return true;
	};

	$(cert_info_dlg.dom_id + " #btn-save").click(function () {
		if (!cert_info_dlg.check_args()) {
			return;
		}

		cert_info_dlg.post();
//		if (cert_info_dlg.update == 0) {
//			cert_info_dlg.on_get_enc_pri();
//		} else {
//			if (cert_info_dlg.cert_pri.length > 0)
//				cert_info_dlg.on_get_enc_pri();
//			else
//				cert_info_dlg.post();
//		}
	});
//
//	cert_info_dlg.on_get_enc_pri = function () {
//		ywl.ajax_post_json('/auth/get-enc-data', {pwd: cert_info_dlg.cert_pri},
//			function (ret) {
//				var data = ret.data;
//				if (data.code == 0) {
////					var temp_password = data.data;
//
//					cert_info_dlg.cert_pri = data.data;
//
//					cert_info_dlg.post();
//
//
////					$("#dlg-cert-pri").val(temp_password);
////					ywl.notify_success('成功得到私钥加密字符串');
//				} else {
//					ywl.notify_error('获取加密私钥失败！ [' + data.code + ']');
//				}
//
//			},
//			function () {
//				ywl.notify_error('获取加密私钥失败');
//			}
//		);
//
//	};

//	$(cert_info_dlg.dom_id + " #btn-get-enc-data").click(function () {
//		var temp_dlg_cer__pri = $("#temp-dlg-cert-pri").val();
//		if (temp_dlg_cer__pri == '') {
//			ywl.notify_error('私钥不能为空!');
//			return;
//		}
//		ywl.ajax_post_json('/auth/get-enc-data', {pwd: temp_dlg_cer__pri},
//			function (ret) {
//				var data = ret.data;
//				if (data.code == 0) {
//					var temp_password = data.data;
//					$("#dlg-cert-pri").val(temp_password);
//					ywl.notify_success('成功得到私钥加密字符串');
//				} else {
//					ywl.notify_error('获取加密私钥失败 ' + data.code);
//				}
//
//			},
//			function () {
//				ywl.notify_error('获取加密私钥失败');
//			}
//		);
//	});

	return cert_info_dlg
};

