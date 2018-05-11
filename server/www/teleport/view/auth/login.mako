<%!
    page_title_ = '登录'
%>
<%inherit file="../page_login_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/auth/login.js') }"></script>
</%block>

<%block name="embed_js" >
    <script type="text/javascript">
        $app.add_options(${ page_param });
    </script>
</%block>

<div class="auth-box-container">
    <div class="container">
        <div class="row">
            <div id="slogan-box" class="col-md-5">
                <div id="msg-slogan" style="display: none;"></div>
            </div>

            <div id="auth-box-container" style="display: none;" class="col-md-6">
                <div id="auth-box" class="auth-box auth-box-lg">
                    <div class="header">
                        <a id="login-type-password" class="title selected" href="javascript:;">账号/密码登录</a>
                        <a id="login-type-oath" class="title" href="javascript:;">身份验证器登录</a>
                    </div>

                    <div class="inputarea">
                        <div id="login-area-username" class="login-account">
                            <div class="inputbox">
                                <div class="input-group input-group-lg">
                                    <span class="input-group-addon"><i class="far fa-user fa-fw"></i></span>
                                    <input data-field="username" type="text" class="form-control" placeholder="用户名" data-toggle="popover" data-trigger="manual" data-placement="top">
                                </div>
                            </div>

                            <div class="inputbox">
                                <div class="input-group input-group-lg">
                                    <span class="input-group-addon"><i class="fa fa-key fa-fw"></i></span>
                                    <input data-field="password" type="password" class="form-control" placeholder="密码" data-toggle="popover" data-trigger="manual" data-placement="top">
                                </div>
                                <p class="input-addon-desc"><a href="/user/reset-password" tabindex="-1">忘记密码？</a></p>
                            </div>

                        </div>

                        <div id="login-area-captcha" class="inputbox" style="display:none;">
                            <div class="input-group input-group-lg">
                                <span class="input-group-addon"><i class="far fa-check-square fa-fw"></i></span>
                                <input id="captcha" type="text" class="form-control" placeholder="验证码" data-toggle="popover" data-trigger="manual" data-placement="top">
                                <span class="input-group-addon"><a href="javascript:;" tabindex="-1"><img id="captcha-image" src=""></a></span>
                            </div>
                            <p class="input-addon-desc">验证码，点击图片可更换</p>
                        </div>

                        <div id="login-area-oath" class="inputbox" style="display:none;">
                            <div class="input-group input-group-lg">
                                <span class="input-group-addon"><i class="fas fa-shield-alt fa-fw"></i></span>
                                <input id="oath-code" type="text" class="form-control" placeholder="6位数字身份验证器动态验证码" data-toggle="popover" data-trigger="manual" data-placement="top">
                            </div>
                            <p class="input-addon-desc"><a href="/user/bind-oath" tabindex="-1">尚未绑定身份验证器？</a></p>
                        </div>


                        <div class="inputbox">
                            <div class="checkbox">
                                <label><input id="remember-me" type="checkbox" value=""> 记住我，12小时内无需重新登录。</label>
                            </div>
                        </div>

                        <div class="inputbox">
                            <button id="btn-login" class="btn btn-primary btn-lg btn-block">登 录</button>
                        </div>

                    </div>
                    <div>
                        <p id="message" class="op_box" style="display:none;"></p>
                    </div>

                </div>
            </div>
        </div>
    </div>
</div>