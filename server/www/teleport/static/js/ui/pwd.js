/**
 * Created by mi on 2016/7/4.
 */

ywl.clear_input = function() {
	$("#current-pwd").val('');
	$("#new-pwd-1").val('');
	$("#new-pwd-2").val('');
};

ywl.on_init = function (cb_stack, cb_args) {
	$("#btn-modify-pwd").click(function () {
		var old_pwd = $("#current-pwd").val();
		var new_pwd_1 = $("#new-pwd-1").val();
		var new_pwd_2 = $("#new-pwd-2").val();
		if(old_pwd.length == 0) {
			ywl.notify_error('请输入当前密码！');
			return;
		}
		if(new_pwd_1.length == 0) {
			ywl.notify_error('请设置新密码！');
			return;
		}
		if (new_pwd_1 != new_pwd_2) {
			ywl.notify_error('两次密码输入不一致！');
			return;
		}
		ywl.ajax_post_json('/auth/modify-pwd', {o_pwd: old_pwd, n_pwd: new_pwd_1, callback: 1},
			function (ret) {
				if (ret.code === TPE_OK) {
					ywl.notify_success('密码修改成功！');
					ywl.clear_input();
				} else if (ret.code === -101) {
					ywl.notify_error('密码错误！');
				} else {
					ywl.notify_error('密码修改失败：'+ret.message);
				}

			},
			function () {
				ywl.notify_error('密码修改失败！');
			}
		);
	});
};