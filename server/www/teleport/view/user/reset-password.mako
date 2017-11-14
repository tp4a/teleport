<%!
    page_title_ = '密码管理'
%>
<%inherit file="../page_single_base.mako"/>

<%block name="page_header">
    <a href="http://teleport.eomsoft.net" target="_blank"><span class="logo"></span></a>
</%block>

<%block name="embed_css">
    <style type="text/css">
        .input-addon-desc {
            text-align: right;
            font-size: 80%;
            color: #707070;
        }

        .captcha-box {
            padding: 0 5px;
        }
    </style>
</%block>

<div class="page-content">
    <div class="error-box">
        <div class="error-icon-box">
            <i id="icon-bg" class="fa fa-warning"></i>
        </div>
        <div class="error-message-box">
            <div id="title" class="title">设置密码</div>
            <hr/>
            <div id="content" class="content">
                <div id="error-area" style="display:none;">
                    <div id="message" class="alert alert-danger"></div>
                    <div id="actions" style="display: none;">
                        您可以：
                        <ul>
                            <li>重新找回密码</li>
                            <li>联系管理员重置密码</li>
                        </ul>
                    </div>
                </div>

                <div id="find-my-password" style="display: none;">
                    <div class="row" style="padding:0 20px;">
                        <div class="col-sm-4">
                            <div class="input-group">
                                <span class="input-group-addon"><i class="fa fa-user-circle-o fa-fw"></i></span>
                                <input data-field="username" type="text" class="form-control mono" placeholder="登录teleport系统的用户名">
                            </div>
                            <div class="input-group" style="margin-top:10px;">
                                <span class="input-group-addon"><i class="fa fa-envelope-o fa-fw"></i></span>
                                <input data-field="email" type="text" class="form-control mono" placeholder="用户绑定的电子邮箱">
                            </div>

                            <div class="input-group" style="margin-top:10px;">
                                <span class="input-group-addon"><i class="fa fa-check-square-o fa-fw"></i></span>
                                <input id="captcha" type="text" class="form-control" placeholder="验证码"
                                       data-toggle="popover" data-trigger="manual" data-placement="top">
                                <span class="input-group-addon captcha-box"><a href="javascript:;"><img id="captcha-image" src=""></a></span>
                            </div>
                            <p class="input-addon-desc">验证码，点击图片可更换</p>
                        </div>
                        <div class="col-sm-8">
                            <div class="alert alert-info">
                                <p>请填写用户信息，随后一封密码重置确认函将发送到您的邮箱。</p>
                                <p>请注意，密码重置确认函在24小时内有效！</p>
                                <p>&nbsp;</p>
                                <p>如果您的用户账号没有设置关联邮箱，请联系系统管理员为您重置密码。</p>
                            </div>
                        </div>
                    </div>

                    <div class="row" style="padding:0 20px;margin-top:10px;">
                        <div class="col-sm-4">
                            <button type="button" class="btn btn-primary" id="btn-send-email" style="width:100%;"><i class="fa fa-search-plus fa-fw"></i> 找回密码</button>
                        </div>
                        <div class="col-sm-8">
                            <div id="send-result" class="alert alert-danger" style="display: none;"></div>
                        </div>
                    </div>
                </div>

                <div id="password-area" style="display:none;">
                    <div class="row" style="padding:0 20px;">
                        <div class="col-sm-4">
                            <div class="input-group">
                                <span class="input-group-addon"><i class="fa fa-key fa-fw"></i></span>
                                <input data-field="password" type="password" class="form-control mono" placeholder="设置新密码">
                                <span class="input-group-btn"><button class="btn btn-default" type="button" id="btn-switch-password"><i class="fa fa-eye fa-fw"></i></button></span>
                            </div>

                        </div>
                        <div class="col-sm-8">
                            <div class="alert alert-warning">
                                <p>注意，系统启用强密码策略，要求密码至少8位，必须包含大写字母、小写字母以及数字。</p>
                            </div>
                        </div>
                    </div>

                    <div class="row" style="padding:0 20px;margin-top:10px;">
                        <div class="col-sm-4">
                            <button type="button" class="btn btn-primary" id="btn-reset-password" style="width:100%;"><i class="fa fa-check fa-fw"></i> 重置密码</button>
                        </div>
                        <div class="col-sm-8">
                            <div id="reset-result" class="alert alert-danger" style="display: none;"></div>
                        </div>
                    </div>



                    ##                     <div class="form-group form-group-sm">
                    ##                         <div class="col-sm-4">
                    ##                             <div class="input-group">
                    ##                                 <input data-field="password" type="password" class="form-control mono" placeholder="设置新密码">
                    ##                                 <span class="input-group-btn"><button class="btn btn-sm btn-default" type="button" id="btn-switch-password"><i class="fa fa-eye fa-fw"></i></button></span>
                    ##                             </div>
                    ##                         </div>
                    ##                         <div class="col-sm-8">
                    ##                             <button type="button" class="btn btn-sm btn-primary" id="btn-reset-password"><i class="fa fa-check fa-fw"></i> 重置密码</button>
                    ##                         </div>
                    ##                     </div>
                    ##                     <div class="clear-float"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<%block name="embed_js">
    <script type="text/javascript">
        "use strict";
        $app.add_options(${page_param});
        console.log($app.options);

        $app.dom = {
            title: $('#title'),
            icon_bg: $('#icon-bg'),

            err_area: $('#error-area'),
            message: $('#message'),
            actions: $('#actions'),

            find_password_area: $('#find-my-password'),
            captcha_image: $('#captcha-image'),

            password_area: $('#password-area')
        };

        $app.dom.captcha_image.click(function () {
            $(this).attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
            $app.dom.input_captcha.focus().val('');
        });

        if ($app.options.mode === 1) {
            // show 'find-my-password' page
            $app.dom.title.text('找回密码');
            $app.dom.icon_bg.removeClass().addClass('fa fa-search-plus');
            $app.dom.captcha_image.attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
            $app.dom.find_password_area.show();
        } else if ($app.options.mode === 2) {
            // show 'password-expired' page
            $app.dom.title.text('更新密码');
        } else if ($app.options.mode === 3) {
            // show 'set-new-password' page
            $app.dom.title.text('重置密码');
            $app.dom.password_area.show();
        }
    </script>
</%block>
