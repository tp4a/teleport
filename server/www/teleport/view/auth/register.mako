<!DOCTYPE html>
<html>
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
	<meta http-equiv="X-UA-Compatible" content="IE=edge"/>
	<meta content="yes" name="apple-mobile-web-app-capable">
	<meta content="black-translucent" name="apple-mobile-web-app-status-bar-style">
	<title>TELEPORT::注册</title>
	<link rel="shortcut icon" href="${ static_url('favicon.png') }">

	<link href="${ static_url('plugins/bootstrap/css/bootstrap.min.css') }" rel="stylesheet" type="text/css"/>
	<link href="${ static_url('plugins/font-awesome/css/font-awesome.min.css') }" rel="stylesheet">
	<link href="${ static_url('css/main.css') }" rel="stylesheet" type="text/css"/>
	<link href="${ static_url('css/auth.css') }" rel="stylesheet" type="text/css"/>

	<!--[if lt IE 9]>
	<script src="${ static_url('plugins/html5shiv/html5shiv.min.js') }"></script>
	<![endif]-->
	<script type="text/javascript" src="${ static_url('plugins/jquery/jquery.min.js') }"></script>
	<script type="text/javascript" src="${ static_url('plugins/bootstrap/js/bootstrap.min.js') }"></script>
	<script type="text/javascript" src="${ static_url('js/ywl_const.js') }"></script>
	<script type="text/javascript" src="${ static_url('js/ywl_common.js') }"></script>
	<script type="text/javascript" src="${ static_url('js/ywl_assist.js') }"></script>
	<script type="text/javascript" src="${ static_url('js/ywl.js') }"></script>
	<script type="text/javascript" src="${ static_url('js/ui/common.js') }"></script>
	##     <script type="text/javascript" src="${ static_url('js/ywl_const.js') }"></script>
    ##     <script type="text/javascript" src="${ static_url('js/ywl_common.js') }"></script>
    ##     <script type="text/javascript" src="${ static_url('js/ywl_assist.js') }"></script>
    ##     <script type="text/javascript" src="${ static_url('js/ui/common.js') }"></script>

</head>

<body>

<div id="head">
	<nav class="navbar navbar-default navbar-fixed-top">
		<div class="container">
			<ul class="nav navbar-nav navbar-left">
				<li>
					<div class="logo">
						<a href="/"><img src="${ static_url('img/site-logo.png') }" alt="TELEPORT，触维软件旗下产品。"/></a>
						<span class="desc">连接 &middot; 尽在指掌中</span>
					</div>
				</li>
			</ul>
		</div>
	</nav>
</div>

<div id="content">
	<div class="container">
		<div class="row">
			<div class="col-md-5">
				<div id="leftside">
				</div>
			</div>


			<div class="col-md-6">


				<div class="auth-box">
					<div class="header">
						<a id="register_type_email" class="title selected" href="javascript:void(0);" onclick="change_register_type('email');">用邮箱注册</a>
						<a id="register_type_phone" class="title " href="javascript:void(0);" onclick="change_register_type('phone');">用手机号注册</a>
					</div>

					<div class="inputarea">
						<p>欢迎在TELEPORT创建团队。您将成为此团队管理员，需要先注册您的个人账号。</p>
						<div class="inputbox" id="account_with_email">
							<div class="input-group input-group-lg">
								<span class="input-group-addon"><i class="fa fa-user fa-fw"></i></span>
								<input id="account_email" type="text" class="form-control" placeholder="请输入您的电子邮箱用作登录账号"
									   data-toggle="popover" data-trigger="manual" data-placement="top">
							</div>
						</div>

						<div class="inputbox" id="account_with_phone" style="display:none;">
							<div class="input-group">
								<span class="input-group-addon"><i class="fa fa-user fa-fw"></i></span>
								<input id="account_phone" type="text" class="form-control" placeholder="请输入手机号码作为登录账号"
									   data-toggle="popover" data-trigger="manual" data-placement="top">
								<span class="input-group-addon"><a id="send_phone_captcha" href="javascript:void(0);" onclick="send_phone_captcha();">发送手机验证码</a></span>
							</div>
						</div>
						<div class="inputbox" id="captcha_with_phone" style="display:none;">
							<div class="input-group">
								<span class="input-group-addon"><i class="fa fa-hashtag fa-fw"></i></span>
								<input id="captcha_phone" type="text" class="form-control" placeholder="手机收到的验证码（6位数字）"
									   data-toggle="popover" data-trigger="manual" data-placement="top">
							</div>
						</div>


						##                     <div class="inputbox">
                        ##                         <div class="input-group">
                        ##                             <span class="input-group-addon"><i class="fa fa-key fa-fw"></i></span>
                        ##                             <input id="password" type="password" class="form-control" placeholder="设置个人账号密码"
                        ##                                    data-toggle="popover" data-trigger="manual" data-placement="top">
                        ##                         </div>
                        ##                     </div>
                        ##                     <div class="inputbox">
                        ##                         <div class="input-group">
                        ##                             <span class="input-group-addon"><i class="fa fa-key fa-fw"></i></span>
                        ##                             <input id="confirm_password" type="password" class="form-control" placeholder="确认个人账号密码"
                        ##                                    data-toggle="popover" data-trigger="manual" data-placement="top">
                        ##                         </div>
                        ##                     </div>


						<div class="inputbox" id="captcha_with_email">
							<div class="input-group input-group-lg">
								<span class="input-group-addon"><i class="fa fa-key fa-fw"></i></span>
								<input id="captcha_email" type="text" class="form-control" placeholder="验证码"
									   data-toggle="popover" data-trigger="manual" data-placement="top">
								<span class="input-group-addon"><a href="javascript:void(0);" onclick="change_captcha();"><img id="captcha_image" src="/auth/get-captcha?{{ captcha_random }}"></a></span>
							</div>
							<p class="input-addon-desc">验证码，点击图片可更换</p>
						</div>

						<hr>


						<div ywl-team-reg style="display: none">
							<p>创建一个运维管理团队，您可以随时在团队管理界面修改下列信息。</p>
							<div class="inputbox">
								<div class="input-group">
									<span class="input-group-addon"><i class="fa fa-group fa-fw"></i></span>
									<input id="ywl-create-team_name" type="text" class="form-control" placeholder="团队名称"
										   data-toggle="popover" data-trigger="manual" data-placement="top">
								</div>
							</div>
						</div>

						<div ywl-user-reg style="font-size:20px" style="display: none">
							<span>您正在加入团队是:</span><span ywl-team-name></span>
						</div>

						<hr/>


						<div class="inputbox">
							<div class="checkbox">
								<label><input id="chk_license" type="checkbox" checked onclick="change_license();"> 我已阅读并同意<a href="#">《TELEPORT服务协议》</a></label>
							</div>
						</div>

						<div class="inputbox">
							<button id="btn_register" class="btn btn-primary btn-lg btn-block" onclick="register();">提交注册</button>
							<p id="register_message" class="op_box" style="display:none;"></p>
						</div>

					</div>

				</div>
			</div>
		</div>
	</div>
</div>

<div id="foot">
	<nav class="navbar navbar-default navbar-fixed-bottom">
		<div class="container">
			<p>触维软件旗下产品 | TELEPORT | &copy;2015 - 2016 <a href="http://www.eomsoft.net/" target="_blank">触维软件</a>，保留所有权利。<a href="/auth/logout">Logout</a></p>
		</div>
	</nav>
</div>



	## 模式对话框：页面加载后先让用户输入邀请码

<div class="modal fade" id="dialog_invite_code" tabindex="-1" role="dialog">
	<div class="modal-dialog" role="document">
		<div class="modal-content">
			<div class="modal-header">
				<h4 class="modal-title">注册邀请码</h4>
			</div>
			<div class="modal-body">
				<p>目前TELEPORT采用邀请注册机制，您需要一个注册邀请码才能创建运维团队。邀请码有效时间为两天（48小时），请及时注册！</p>

				<div class="inputbox">
					<div class="input-group input-group-lg">
						<span class="input-group-addon"><i class="fa fa-code fa-fw"></i>邀请码</span>
						<input id="ywl-invite-code" type="text" class="form-control" placeholder="团队注册邀请码" data-toggle="popover" data-trigger="manual" data-placement="top">
					</div>
					##             <p id="invite_message" class="op_box op_wait" style="display:-none;"><i class="fa fa-circle-o-notch fa-spin"></i> 正在验证邀请码，请稍候......</p>
                            </div>

				<p>&nbsp;</p>
				<p>如果您没有邀请码，可以<a href="#">与我们联系获取</a>！</p>

			</div>
			<div class="modal-footer">
				<div class="inputbox text-centear">
					<button id="btn_register" class="btn btn-primary btn-lg" onclick="check_btn_invite();">确定</button>
				</div>

			</div>
		</div>
	</div>
</div>

<script type="text/javascript">

	g_invite_code = '${ invite_code }';
	g_team_id = '${ team_id }';
	g_register_type = 'email';
	g_reference = '${ reference }';
	g_assist = null;

	$(document).ready(function () {
		// g_assist = new ywl_assist();

		// $('#username_account').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { $('#password_account').focus(); } });
		// $('#password_account').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { $('#captcha').focus(); } });
		// $('#username_usbkey').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { $('#password_usbkey').focus(); } });
		// $('#password_usbkey').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { $('#captcha').focus(); } });
		// $('#captcha').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { register(); } });

		//g_assist.init();

		// $('#dialog_invite_code').modal({backdrop:'static', keyboard:false});
		if (g_team_id === "0") {
			$('[ywl-team-reg]').css('display', 'block');
			$('[ywl-user-reg]').css('display', 'none');
		} else {
			$('[ywl-team-reg]').css('display', 'none');
			$('[ywl-user-reg]').css('display', 'block');
		}

		if (g_invite_code == '') {
			$('#dialog_invite_code').modal({backdrop: 'static', keyboard: false});
		} else {
			##         check_invite_code();
                }
	});
	function check_btn_invite() {
		g_invite_code = $('#ywl-invite-code').val();
		check_invite_code(g_invite_code)
	}


	function check_invite_code(invite_code) {
		// 通过ajax方式检查邀请码是否有效，如果无效，显示输入邀请码对话框。

		// $('#dialog_invite_code').modal({backdrop:'static', keyboard:false});
		ywl.ajax_post_json('/auth/check-invite', {'t_id': g_team_id, 'code': invite_code},
				function (ret) {
					console.log('team-manage', ret);
					##                 console.log('team-code', ret.data.code);
                    ##                 console.log('team-invite', ret.data.in);
                                    if (ret.data.code == 0) {
						var team_name = '[ ywl-team-name]';
						$(team_name).html(ret.data.name);

						##                     var invite_value = '[ywl-inivite-code-value]';
                        ##                     $(invite_value).html( ret.data.in);
                        ##
                        ##                     var invite_link = '[ywl-inivite-code-link]';
                        ##                     //var _web_link = "http://ywl.eomsoft.net/auth/register_team?c=" + ret.data.in;
                        ##                     $(invite_link).html( ret.data.url);
                                            $('#dialog_invite_code').modal('hide');
					} else {
						alert('邀请码验证失败');
						##                         $('#dialog_invite_code').modal({backdrop:'static', keyboard:false});
                        ##                     $('#dialog_invite_code').modal({backdrop:'static', keyboard:false});

					}
				},
				function () {
					alert('邀请码验证失败');
				}
		);
		##     /auth/check-invite
        }

	function change_captcha() {
		$('#captcha_image').attr('src', '/auth/get-captcha?' + Math.random());
	}

	function change_license() {
		if ($('#chk_license').is(':checked')) {
			$('#btn_register').removeAttr('disabled');
		} else {
			$('#btn_register').attr('disabled', 'disabled');
		}
	}

	function change_register_type(register_type) {
		if (register_type === 'phone') {
			alert('暂时不支持手机注册');
			return;
		}
		if (register_type == g_register_type)
			return;

		$('#account_with_' + register_type).show('fast');
		$('#captcha_with_' + register_type).show('fast');
		$('#account_with_' + g_register_type).hide('fast');
		$('#captcha_with_' + g_register_type).hide('fast');

		$('#register_type_' + register_type).addClass('selected');
		$('#register_type_' + g_register_type).removeClass('selected');

		if (register_type == 'usbkey')
			$('#btn_register').attr('disabled', 'disabled');
		else
			$('#btn_register').removeAttr('disabled');

		g_register_type = register_type;
	}

	function hide_op_box() {
		$('#register_message').hide();
	}

	function show_op_box(op_type, op_msg) {
		var obj_box = $('#register_message');

		obj_box.html(op_msg);
		obj_box.removeClass().addClass('op_box op_' + op_type);
		obj_box.show();
	}

	function register() {
		hide_op_box();
		if (!$('#chk_license').is(':checked')) {
			show_op_box('error', '请勾选注册协议！');
			return;
		}


		var str_username = '';
		var str_password = '';
		var str_confirm_password = '';
		var str_captcha = '';

		str_username = $('#account_' + g_register_type).val();
		##     str_password = $('#password').val();
        ##     str_confirm_password = $('#confirm_password').val();
            str_captcha = $('#captcha_' + g_register_type).val();

		if (str_username.length == 0) {
			show_op_box('error', '缺少账号！');
			$('#username_' + g_register_type).attr('data-content', "请填写您的账号！").popover('show');
			$('#username_' + g_register_type).focus();
			return;
		}
		var macth = /^(?:[a-zA-Z0-9]+[_\-\+\.]?)*[a-zA-Z0-9]+@(?:([a-zA-Z0-9]+[_\-]?)*[a-zA-Z0-9]+\.)+([a-zA-Z]{2,})+$/;
		var s = new RegExp(macth);
		if (!s.test(str_username)) {
			show_op_box('error', '邮箱地址不正确！');
			return;
		}

		##     if(str_password.length == 0) {
        ##         show_op_box('error', '缺少密码！');
        ##         $('#password_'+g_register_type).attr('data-content', "请填写密码！").popover('show');
        ##         $('#password_'+g_register_type).focus();
        ##         return;
        ##     }

		if (str_captcha.length != 4) {
			show_op_box('error', '验证码错误！');
			$('#captcha').attr('data-content', "验证码为4位数字和字母的组合，请重新填写！").popover('show').focus();
			return;
		}

		$('#btn_register').attr('disabled', 'disabled');
		show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> 正在进行身份认证，请稍候...');

		##     if(g_register_type == 'usbkey') {
        ##         do_auth(g_register_type, str_username, str_password, str_captcha);
        ##         return;
        ##     }

		// 先判断一下captcha是否正确，如果不正确，拒绝登录
		$.ajax({
			type: 'GET',
			url: '/auth/verify-captcha',
			jsonp: "callback",
			//jsonpCallback:"login_ret",
			data: {captcha: str_captcha},
			dataType: 'jsonp',
			success: function (data) {
				if (data.code == 0) {
					// 验证成功
					var team_id = parseInt(g_team_id);
					if (team_id === 0) {
						var team_name = '#ywl-create-team_name';
						var team_name = $(team_name).val();
						do_create_team(str_username, team_name, g_invite_code)
					} else {
						do_join_team(str_username, g_team_id, g_invite_code);
					}

				}
				else {
					hide_op_box();
					show_op_box('error', '验证码错误！');
					// renew the captcha.
					change_captcha();
				}

				$('#btn_register').removeAttr('disabled');
			},
			error: function () {
				hide_op_box();
				show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
				$('#btn_register').removeAttr('disabled');
			}
		});
	}
	function do_join_team(username, team_id, invite_code) {
		var param = {'t_id': team_id, 'u_n': username, 'code': invite_code};
		ywl.ajax_post_json('/auth/reg-user', param,
				function (ret) {
					console.log('ajax_post_json ret', ret);
					hide_op_box();
					if (ret.code === 0) {
						console.log('url', g_reference);
						window.location.href = g_reference;

						console.log('用户注册成功');
					} else {
						if (ret.code === -110) {
							show_op_box('error', '没有输入邀请码');
						}
						else if (ret.code === -111) {
							show_op_box('error', '邀请码已经失效');
						} else if (ret.code === -201) {
							show_op_box('error', '用户已经注册');
						} else if (ret.code === -202) {
							show_op_box('error', '团队已经注册');
						} else {
							console.log('用户注册失败', ret.code);
						}

					}
				},
				function () {
					hide_op_box();
					show_op_box('error', '请求超时');
					##         notify_error('邀请链接已经发送失败', '');
                        });
	}

	function do_create_team(username, team_name, invite_code) {
		var param = {'t_n': team_name, 'u_n': username, 'code': invite_code};
		ywl.ajax_post_json('/auth/reg-team', param,
				function (ret) {
					console.log('ajax_post_json ret', ret);
					hide_op_box();
					if (ret.code === 0) {
						console.log('url', g_reference);
						window.location.href = g_reference;
					} else {
						if (ret.code === -110) {
							show_op_box('error', '没有输入邀请码');
						}
						else if (ret.code === -111) {
							show_op_box('error', '邀请码已经失效');
						} else if (ret.code === -201) {
							show_op_box('error', '用户已经注册');
						} else if (ret.code === -202) {
							show_op_box('error', '团队已经注册');
						} else {
							console.log('用户注册失败', ret.code);
						}

					}
				},
				function () {
					hide_op_box();
					show_op_box('error', '请求超时');
					##         notify_error('邀请链接已经发送失败', '');
                        });
	}

	function do_register(username, ticket, captcha) {

		$.ajax({
			type: 'GET',
			url: '/auth/verify-ticket',
			jsonp: "callback",
			data: {username: username, ticket: ticket, captcha: captcha},
			dataType: 'jsonp',
			success: function (data) {
				if (data.code == 0) {
					// 验证成功
					window.location.href = g_reference;
				}
				else {
					hide_op_box();
					show_op_box('error', '无法登录TELEPORT！');
				}

				$('#btn_register').removeAttr('disabled');
			},
			error: function () {
				hide_op_box();
				show_op_box('error', '很抱歉，无法连接服务器！请稍后再试一次！');
				$('#btn_register').removeAttr('disabled');
			}
		});
	}


</script>

</body>
</html>