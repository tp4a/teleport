<%!
	# -*- coding: utf-8 -*-
	page_title_ = '登录'
	## 	page_menu_ = ['host']
	## 	page_id_ = 'host'
%>
<%inherit file="page_base.mako"/>

<%block name="extend_js">
    <script type="text/javascript" src="${ static_url('js/ui/auth/login.js') }"></script>
</%block>

<%block name="embed_js" >
	<script type="text/javascript">
		ywl.add_page_options({
			login_type: 'account',
			reference: '${ reference }'
		});

	</script>
</%block>

<div class="row">
	<div class="col-md-6">
		<div id="leftside">
		</div>
	</div>


	<div class="col-md-5">
		<div class="auth-box auth-box-lg">
			<div class="header">
				<a id="login-type-account" class="title" href="javascript:void(0);">账号/密码 登录</a>
				## 				<a id="login_type_usbkey" class="title" href="javascript:void(0);" onclick="change_login_type('usbkey');">USB-Key 登录</a>
            </div>

			<div id="input-area-quick" class="quick-area" style="display: none;">
				<div class="quick-yes" style="display: none;">
					<div class="quick-disc">请点击头像进行快速登录！</div>
					<a id="btn-login-quick" class="quick-account" href="javascript:void(0);">
						<span class="quick-image"><i class="fa fa-male fa-fw"></i></span>
						<span id="quick-username" class="label label-primary quick-name">User Name</span>
					</a>
				</div>

				<div class="quick-no" style="display: none;">
					<div class="quick-disc">未发现已登录账号，无法进行快速登录！</div>
				</div>
			</div>

			<div id="input-area-account" class="inputarea" >
				<div id="login_account" class="login-account">
					<div class="inputbox">
						<div class="input-group input-group-lg">
							<span class="input-group-addon"><i class="fa fa-user fa-fw"></i></span>
							<input id="username_account" type="text" class="form-control" placeholder="账号：邮箱地址或手机号"
								   data-toggle="popover" data-trigger="manual" data-placement="top">
						</div>
					</div>

					<div class="inputbox">
						<div class="input-group input-group-lg">
							<span class="input-group-addon"><i class="fa fa-key fa-fw"></i></span>
							<input id="password_account" type="password" class="form-control" placeholder="密码"
								   data-toggle="popover" data-trigger="manual" data-placement="top">
						</div>
					</div>

				</div>

				<div id="login_usbkey" class="login-usbkey" style="display:none;">
					<div class="inputbox">
						<div class="input-group input-group-lg">
							<span class="input-group-addon"><i class="fa fa-user fa-fw"></i></span>
							<input id="username_usbkey" type="text" class="form-control" placeholder="账号，支持邮箱/手机号" value="设备查找中..." disabled>
						</div>
						<p id="usbkey_message" class="op_box op_wait"><i class="fa fa-circle-o-notch fa-spin"></i> 正在查找USB-Key，请稍候...</p>
					</div>

					<div class="inputbox">
						<div class="input-group input-group-lg">
							<span class="input-group-addon"><i class="fa fa-key fa-fw"></i></span>
							<input id="password_usbkey" type="password" class="form-control" placeholder="USB-Key设备密码">
						</div>
					</div>

				</div>


				<div class="inputbox">
					<div class="input-group input-group-lg">
						<span class="input-group-addon"><i class="fa fa-check-square-o fa-fw"></i></span>
						<input id="captcha" type="text" class="form-control" placeholder="验证码"
							   data-toggle="popover" data-trigger="manual" data-placement="top">
						<span class="input-group-addon"><a href="javascript:;"><img id="captcha_image" src="/auth/get-captcha?{{ captcha_random }}"></a></span>
					</div>
					<p class="input-addon-desc">验证码，点击图片可更换</p>
				</div>

				<div class="inputbox">
					<div class="checkbox">
						<label><input type="checkbox" value=""> 记住我，12小时内无需重新登录。</label>
					</div>
				</div>

				<div class="inputbox">
					<button id="btn-login-account" class="btn btn-primary btn-lg btn-block">登 录</button>
				</div>

			</div>
			<div>
				<p id="login_message" class="op_box" style="display:none;"></p>
			</div>

		</div>
	</div>
</div>

