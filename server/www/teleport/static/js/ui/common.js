/*! ywl v1.0.1, (c)2015 eomsoft.net */
"use strict";


ywl.notify_error = function (message_, title_) {
    var _title = title_ || '';
    $.gritter.add({
        //sticky:true,
        class_name: 'gritter-error',
        time: 10000,
        title: '<i class="fa fa-warning fa-fw"></i> 错误：' + _title,
        text: message_
    });
};

ywl.notify_success = function (message_, title_) {
    var _title = title_ || null;
    if (_title !== null)
        _title = '<i class="fa fa-check-square fa-fw"></i> ' + _title;
    $.gritter.add({
        //sticky:true,
        class_name: 'gritter-success',
        time: 10000,
        title: _title,
        text: message_
    });
};


function get_host_group_by_id(gid) {
    var _all = {id: 0, group_name: '全部'};
    return _all;
}

function get_user_info_by_id(user_id) {
    var _all = {id: 0, nickname: '未知'};
    return _all;
}

function get_event_code_by_id(e_id) {
    var _all = {id: 0, e_desc: '未知'};
    var ret = ywl.assist.get_cache_by_id(CACHE_TYPE_EVENT_CODE, e_id);

    if (ret == null)
        return _all;
    else
        return ret;
}
function get_current_system_group() {
    return get_system_group_by_id(0);
}

function get_system_group_by_id(gid) {
    var _all = {id: 0, name: '全部'};
    var ret = null;

    $.each(system_group, function (i, group) {
        if (group.id == gid) {
            ret = group;
            return false;
        }
    });

    if (ret == null)
        return _all;
    else
        return ret;
}


//function get_command_name_by_id(cmd_id) {
//	return ywl.assist.get_cache_by_id(CACHE_TYPE_COMMAND, cmd_id);
//}

//function notify_error(message_, title_) {
//	var _title = title_ || '';
//	$.gritter.add({
//		sticky: true,
//		class_name: 'gritter-error',
//		time: 10000,
//		title: '<i class="fa fa-warning fa-fw"></i> 错误：' + _title,
//		text: message_
//	});
//}
//function notify_success(message_, title_) {
//	var _title = title_ || null;
//	if (_title !== null)
//		_title = '<i class="fa fa-check-square fa-fw"></i> ' + _title;
//	$.gritter.add({
//		//sticky:true,
//		class_name: 'gritter-success',
//		time: 10000,
//		title: _title,
//		text: message_
//	});
//}

// 切换一个dom节点显示与否
ywl.toggle_display = function (selector) {
    var obj = $(selector);
    if (typeof(obj) == 'undefined')
        return;

    if (obj.is(':hidden')) {
        obj.show();
    } else {
        obj.hide();
    }
};

//======================================================
// Dialog-box for confirm operation.
//======================================================
ywl.dlg_confirm = function (cb_stack, cb_args) {
    var self = {};
    self._cb_stack = cb_stack;
    self._title = cb_args.title || '操作确认：';
    self._msg = cb_args.msg || '';
    self._btn_yes = cb_args.btn_yes || '确定';
    self._btn_no = cb_args.btn_no || '取消';
    self._fn_yes = cb_args.fn_yes || null;
    self._fn_no = cb_args.fn_no || null;
    self._dlg_id = _.uniqueId('dlg-confirm-');
    self._cb_args = cb_args.cb_args || {};

    self._make_message_box = function () {
        var _html = [
            '<div class="modal fade" id="' + self._dlg_id + '" tabindex="-1" role="dialog">',
            '<div class="modal-dialog" role="document">',
            '<div class="modal-content">',
            '<div class="modal-header">',
            '<h4 class="modal-title">' + self._title + '</h4>',
            '</div>',
            '<div class="modal-body">',
            '<div>' + self._msg + '</div>',
            '</div>',
            '<div class="modal-footer">',
            '<button type="button" class="btn btn-primary" id="dlg-btn-' + self._dlg_id + '-yes"><i class="fa fa-check fa-fw"></i> ' + self._btn_yes + '</button>',
            '<button type="button" class="btn btn-default" id="dlg-btn-' + self._dlg_id + '-no"><i class="fa fa-close fa-fw"></i> ' + self._btn_no + '</button>',
            '</div>',
            '</div>',
            '</div>',
            '</div>'].join('\n');
        $('body').append($(_html));
    };

    self._destroy = function () {
        $('#' + self._dlg_id).remove();
    };

    self._on_btn_yes = function () {
        $('#' + self._dlg_id).modal('hide');
        if (_.isFunction(self._fn_yes)) {
            self._cb_stack
                .add(self._fn_yes, self._cb_args)
                .exec();
        }
    };
    self._on_btn_no = function () {
        $('#' + self._dlg_id).modal('hide');
        if (_.isFunction(self._fn_no)) {
            self._cb_stack
                .add(self._fn_no, self._cb_args)
                .exec();
        }
    };

    self.show = function () {
        $('#dlg-btn-' + self._dlg_id + "-yes").click(self._on_btn_yes);
        $('#dlg-btn-' + self._dlg_id + "-no").click(self._on_btn_no);
        $('#' + self._dlg_id)
            .modal()
            //.on('hide.bs.modal', self._on_cancel)
            .on('hidden.bs.modal', self._destroy);
    };

    self._make_message_box();
    self.show();
};


//======================================================
// Dialog-box for modify host description
//======================================================
ywl.create_dlg_modify_host_desc = function (tbl, row_id, host_id, host_ip, host_desc) {
    var self = {};

    self.dlg_id = _.uniqueId('dlg-modify-host-desc-');
    self._table_ctrl = tbl;
    self.host_id = host_id;
    self.host_ip = host_ip;
    self.host_desc = host_desc;

    self.show = function (pos_obj) {
        self._make_dialog_box();
        $('body')
            .addClass('modal-open')
            .append($('<div class="modal-backdrop fade in"></div>'))
            .keydown(function (event) {
                if (event.which == 27) {
                    self._destroy();
                }
            });
        $('.modal-backdrop').click(function () {
            self._destroy();
        });

        var t_obj = $('#' + self.dlg_id + ' .popover');
        t_obj.css({
            'top': pos_obj.offset().top + pos_obj.height() - 5,
            'left': pos_obj.offset().left
        }).show();

        $('#' + self.dlg_id + " [ywl-input='desc']").focus();
    };

    self._save = function () {
        var dlg_dom_id = "[ywl-dlg='modify-host-desc']";

        var val = $(dlg_dom_id + " input[ywl-input='desc']").val();
        if (val === self.host_desc) {
            self._destroy();
            return;
        }

        ywl.ajax_post_json('/host/update', {host_id: host_id, kv: {host_desc: val}},
            function (ret) {
                if (ret.code === TPE_OK) {
                    self._table_ctrl.update_row(row_id, {host_desc: val});
                    ywl.notify_success('主机 ' + self.host_ip + ' 的描述已保存！');
                } else {
                    ywl.notify_error('主机 ' + self.host_ip + ' 的描述修改未能成功保存：' + ret.message);
                }
                self._destroy();
            },
            function () {
                ywl.notify_error('网络故障，主机 ' + self.host_ip + ' 的描述修改未能成功保存！');
                self._destroy();
            }
        );

    };

    self._destroy = function () {
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();

        $('#' + self.dlg_id).remove();
    };

    self._make_dialog_box = function () {
        var _html = [
            '<div class="popover-inline-edit" id="' + self.dlg_id + '">',
            '	<div class="popover fade bottom in" role="tooltip" ywl-dlg="modify-host-desc">',
            '		<div class="arrow" style="left:50px;"></div>',
            '		<h3 class="popover-title">为主机 ' + self.host_ip + ' 添加备注，以便识别</h3>',
            '		<div class="popover-content">',
            '			<div style="display:inline-block;float:right;">',
            '				<a href="javascript:;" class="btn btn-success btn-sm" ywl-btn="ok"><i class="glyphicon glyphicon-ok"></i></a>',
            '				<a href="javascript:;" class="btn btn-danger btn-sm" ywl-btn="cancel"><i class="glyphicon glyphicon-remove"></i></a>',
            '			</div>',
            '			<div style="padding-right:80px;">',
            '				<input type="text" ywl-input="desc" class="form-control" value="' + self.host_desc + '">',
            '			</div>',
            '		</div>',
            '	</div>',
            '</div>'].join('\n');

        $('body').append($(_html));

        // “修改主机描述” 对话框上的两个按钮的点击事件
        $('#' + self.dlg_id + " [ywl-btn='ok']").click(function () {
            self._save();
        });
        $('#' + self.dlg_id + " [ywl-btn='cancel']").click(function () {
            self._destroy();
        });
        // 绑定“修改主机描述” 对话框中的输入框的回车事件
        $('#' + self.dlg_id + " [ywl-input='desc']").keydown(function (event) {
            if (event.which == 13) {
                self._save();
            } else if (event.which == 27) {
                self._destroy();
            }
        });

    };

    return self;
};

ywl.create_dlg_show_rdp_advance = function (row_data) {
    var self = {};

    self.dlg_id = _.uniqueId('dlg-rdp-advance-');
//	self._table_ctrl = tbl;
//	self.host_id = host_id;
//	self.host_ip = host_ip;
//	self.host_desc = host_desc;

    self.show = function (pos_obj) {
        self._make_dialog_box();
        $('body')
            .addClass('modal-open')
            .append($('<div class="modal-backdrop fade in"></div>'))
            .keydown(function (event) {
                if (event.which == 27) {
                    self._destroy();
                }
            });
        $('.modal-backdrop').click(function () {
            self._destroy();
        });

        var t_obj = $('#' + self.dlg_id + ' .popover');
        t_obj.css({
            'top': pos_obj.offset().top + pos_obj.height() + 5,
            'left': pos_obj.offset().left - 10
        }).show();

        //$('#' + self.dlg_id + " [ywl-input='desc']").focus();
    };

    self._save = function () {
        var dlg_dom_id = '[data-dlg="show-rdp-advance"]';

        var val = $(dlg_dom_id + " input[ywl-input='desc']").val();
        if (val === self.host_desc) {
            self._destroy();
            return;
        }

        ywl.ajax_post_json('/host/update', {host_id: host_id, kv: {host_desc: val}},
            function (ret) {
                if (ret.code === TPE_OK) {
                    self._table_ctrl.update_row(row_id, {host_desc: val});
                    ywl.notify_success('主机 ' + self.host_ip + ' 的描述已保存！');
                } else {
                    ywl.notify_error('主机 ' + self.host_ip + ' 的描述修改未能成功保存：' + ret.message);
                }
                self._destroy();
            },
            function () {
                ywl.notify_error('网络故障，主机 ' + self.host_ip + ' 的描述修改未能成功保存！');
                self._destroy();
            }
        );

    };

    self._destroy = function () {
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();

        $('#' + self.dlg_id).remove();
    };

    self._make_dialog_box = function () {
        var _html = [
            '<div class="xx-popover-inline-edit" id="' + self.dlg_id + '">',
            '	<div class="popover fade bottom in" role="tooltip" data-dlg="show-rdp-advance" style="width:300px;">',
            '		<div class="arrow" style="left:50px;"></div>',
            '		<h3 class="popover-title" style="font-weight:bold;">RDP连接选项（仅本次连接有效）</h3>',
            '		<div class="popover-content">',
//			'			<div style="">',
//			'				<input type="text" ywl-input="desc" class="form-control" value="' + self.host_desc + '">',
//			'			</div>',

            '			<div style="">',
            '				<p style="margin:0;"><strong>分辨率：</strong></p>',
            '					<label class="radio-inline">',
            '						<input type="radio" name="radio-rdp-size" id="dlg-action-rdp-size-small" value="overwrite">小 （800x600）',
            '					</label><br/>',
            '					<label class="radio-inline">',
            '						<input type="radio" name="radio-rdp-size" id="dlg-action-rdp-size-middle" value="skip" checked="checked">中 （1024x768）',
            '					</label><br/>',
            '					<label class="radio-inline">',
            '						<input type="radio" name="radio-rdp-size" id="dlg-action-rdp-size-large" value="error">大 （1280x800）',
            '					</label>',
            '			</div>',

            '			<div style="margin-top:5px;">',
            '				<p style="margin:0;"><strong>Console模式：</strong></p>',
            '					<label>',
            '						<input type="checkbox" id="dlg-action-rdp-console"> 以Console模式运行',
            '					</label>',
            '			</div>',


            '			<hr style="margin:3px 0;"/><div style="margin-top:10px;text-align:right;">',
            '				<a href="javascript:;" class="btn btn-success btn-sm" data-action="ok"><i class="fa fa-check fa-fw"></i> 确定连接</a>',
            '				<a href="javascript:;" class="btn btn-default btn-sm" data-actioin="cancel"><i class="fa fa-times fa-fw"></i> 取消</a>',
            '			</div>',
            '		</div>',
            '	</div>',
            '</div>'].join('\n');

        $('body').append($(_html));

        // “修改主机描述” 对话框上的两个按钮的点击事件
        $('#' + self.dlg_id + " [data-action='ok']").click(function () {
            self._save();
        });
        $('#' + self.dlg_id + " [data-action='cancel']").click(function () {
            self._destroy();
        });

//		// 绑定“修改主机描述” 对话框中的输入框的回车事件
//		$('#' + self.dlg_id + " [ywl-input='desc']").keydown(function (event) {
//			if (event.which == 13) {
//				self._save();
//			} else if (event.which == 27) {
//				self._destroy();
//			}
//		});

    };

    return self;
};
