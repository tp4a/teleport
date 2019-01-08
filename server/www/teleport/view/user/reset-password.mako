<%!
    page_title_ = '密码管理'
%>
<%inherit file="../page_single_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/user/reset-password.js') }"></script>
</%block>

<%block name="embed_css">
    <style type="text/css">
        .input-addon-desc {
            text-align: right;
            font-size: 90%;
            color: #707070;
        }

        .captcha-box {
            padding: 0 5px;
        }
    </style>
</%block>

<%block name="page_header">
    <div class="container-fluid top-navbar">
        <div class="brand"><a href="/"><span class="site-logo"></span></a></div>
        <div class="breadcrumb-container">
            <ol class="breadcrumb">
                <li><i class="fa fa-key"></i> 密码管理</li>
            </ol>
        </div>
    </div>
##     <a href="http://tp4a.com/" target="_blank"><span class="logo"></span></a>
</%block>

<div class="page-content">
    <div class="info-box">
        <div class="info-icon-box">
            <i class="fa fa-key" style="color:#ffa043;"></i>
        </div>
        <div class="info-message-box">
            <div id="title" class="title">设置密码</div>
            <hr/>
            <div id="content" class="content">

                <div id="area-error" style="display:none;">
                    <div data-field="message" class="alert alert-danger"></div>
                    <div>
                        您可以：
                        <ul>
                            <li>联系管理员手工重置密码</li>
                            <li><a href="/user/reset-password">重新重置密码</a></li>
                        </ul>
                    </div>
                </div>

                <div id="area-find-password" style="display: none;">
                    <div class="row" style="padding:0 20px;">
                        <div class="col-md-5">
                            <div class="input-group">
                                <span class="input-group-addon"><i class="far fa-user-circle fa-fw"></i></span>
                                <input data-field="input-username" type="text" class="form-control mono" placeholder="teleport系统用户名" data-toggle="popover" data-trigger="manual" data-placement="top">
                            </div>
                            <div class="input-group" style="margin-top:10px;">
                                <span class="input-group-addon"><i class="far fa-envelope fa-fw"></i></span>
                                <input data-field="input-email" type="text" class="form-control mono" placeholder="用户绑定的电子邮箱" data-toggle="popover" data-trigger="manual" data-placement="top">
                            </div>

                            <div class="input-group" style="margin-top:10px;">
                                <span class="input-group-addon"><i class="far fa-check-square fa-fw"></i></span>
                                <input data-field="input-captcha" type="text" class="form-control" placeholder="验证码" data-toggle="popover" data-trigger="manual" data-placement="top">
                                <span class="input-group-addon captcha-box"><a href="javascript:;" tabindex="-1"><img data-field="captcha-image" src=""></a></span>
                            </div>
                            <p class="input-addon-desc">验证码，点击图片可更换</p>

                            <div style="margin:20px 0;">
                                <button type="button" class="btn btn-primary" data-field="btn-submit" style="width:100%;"><i class="fa fa-send fa-fw"></i> 发送密码重置确认函</button>
                                <div data-field="message" class="alert alert-danger" style="display: none;"></div>
                            </div>
                        </div>
                        <div class="col-md-7">
                            <div class="alert alert-info">
                                <p>请填写用户信息，随后一封密码重置确认函将发送到您的邮箱。</p>
                                <p>请注意，密码重置确认函在24小时内有效！</p>
                                <p>&nbsp;</p>
                                <p>如果您的用户账号没有设置关联邮箱，请联系系统管理员为您重置密码。</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="area-set-password" style="display:none;">
                    <div class="row">
                        <div class="col-md-5">
                            <div class="input-group">
                                <span class="input-group-addon"><i class="fa fa-edit"></i></span>
                                <input data-field="input-password" type="password" class="form-control mono" placeholder="设置新密码" data-toggle="popover" data-trigger="manual" data-placement="top">
                                <span class="input-group-btn"><button class="btn btn-default" type="button" data-field="btn-switch-password"><i class="fa fa-eye fa-fw"></i></button></span>
                            </div>

                            <div style="margin:20px 0;">
                                <button type="button" class="btn btn-primary" data-field="btn-submit" style="width:100%;"><i class="fa fa-check fa-fw"></i> 重置密码</button>
                                <div data-field="message" style="display: none;"></div>
                            </div>
                        </div>
                        <div class="col-md-7">
                            <div data-field="info" class="alert alert-warning" style="display:none;">
                                <p>注意，系统启用强密码策略，要求密码至少8位，必须包含大写字母、小写字母以及数字。</p>
                            </div>
                        </div>
                    </div>

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
    </script>
</%block>
