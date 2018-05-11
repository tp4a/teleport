<%!
    page_title_ = '绑定身份验证器'
%>
<%inherit file="../page_single_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/user/bind-oath.js') }"></script>
</%block>

<%block name="embed_css">
    <style type="text/css">
        .step-name {
            font-size: 18px;
            ##             font-weight:bold;
            color: #e55a1d;
        }

        .input-addon-desc {
            text-align: right;
            font-size: 90%;
            color: #707070;
        }

        .time-box {
            display: inline-block;
            margin: 10px;
            padding: 10px;
            border: 1px solid #bcffbd;
            background-color: #d0ffcd;
            border-radius: 5px;
            color: #646464;
        }

        .tp-time {
            font-weight: bold;
            font-size: 16px;
            color: #063c06;
        }

        #area-qrcode {
            margin: 10px auto 0;
            text-align: center;
        }

        #area-qrcode .qrcode-name {
            font-size: 18px;
            color: #5483ff;
        }

        img.qrcode-img {
            margin: 5px;
            padding: 10px;
        }

        img.qrcode-img.selected {
            border: 1px solid #bdbdbd;
        }

        .oath-code {
            font-family: 'Courier New', Consolas, Lucida Console, Monaco, Courier, monospace;
            font-size: 26px;
            line-height: 26px;
            font-weight: bold;
            color: #559f47;
        }

    </style>
</%block>

<%block name="page_header">
    <div class="container-fluid top-navbar">
        <div class="brand"><a href="/"><span class="site-logo"></span></a></div>
        <div class="breadcrumb-container">
            <ol class="breadcrumb">
                <li><i class="fa fa-key"></i> 绑定身份验证器</li>
            </ol>
        </div>
    </div>
</%block>

<div class="page-content">
    <div class="info-box">
        <div class="info-icon-box">
            <i class="fas fa-shield-alt" style="color:#8140f1;"></i>
        </div>
        <div class="info-message-box">
            <div class="title">绑定身份验证器</div>
            <hr/>
            <div id="content" class="content">
                <p class="step-name">第一步：安装身份验证器</p>
                <p>请在你的手机上安装身份验证器App。<a href="javascript:;" id="btn-show-oath-app">点击此处获取安装方式</a></p>

                <hr/>
                <p class="step-name">第二步：检查服务器时间</p>
                <p>请注意检查您的手机时间与teleport服务器时间是否同步，如果两者<span class="important">时间偏差超过两分钟则无法绑定</span>，请及时通知系统管理员处理！</p>
                <div class="time-box"><i class="fa fa-clock-o"></i> TELEPORT服务器时间：<span class="tp-time mono" id="teleport-time">-</span></div>

                <hr/>
                <p class="step-name">第三步：认证并绑定</p>
                <div class="row" style="padding:0 20px;">
                    <div id="area-auth">
                        <div class="col-md-5">
                            <div class="input-group">
                                <span class="input-group-addon"><i class="far fa-user fa-fw"></i></span>
                                <input data-field="input-username" type="text" class="form-control mono" placeholder="teleport系统用户名" data-toggle="popover" data-trigger="manual" data-placement="top">
                            </div>
                            <div class="input-group" style="margin-top:10px;">
                                <span class="input-group-addon"><i class="fa fa-key fa-fw"></i></span>
                                <input data-field="input-password" type="password" class="form-control mono" placeholder="请输入密码" data-toggle="popover" data-trigger="manual" data-placement="top">
                            </div>

                            <div style="margin:20px 0;">
                                <button type="button" class="btn btn-primary" data-field="btn-submit" style="width:100%;"><i class="fa fa-check fa-fw"></i> 用户身份认证</button>
                                <div data-field="message" class="alert alert-danger" style="display: none;"></div>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>
</div>

<%block name="extend_content">
    <div class="modal fade" id="dlg-oath-app" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title"><i class="fas fa-shield-alt"></i> 身份验证器</h3>
                </div>
                <div class="modal-body">

                    <p>选择您喜欢的身份验证器进行安装：</p>

                    <div class="row">
                        <div class="col-md-4">
                            <ul class="list">
                                <li>微信小程序
                                    <ul class="list">
                                        <li><a href="javascript:;" data-switch="wechat"><i class="fab fa-weixin fa-fw"></i> 二次验证码</a> <span class="label label-success">推荐</span></li>
                                    </ul>
                                </li>
                                <li>谷歌身份验证器
                                    <ul class="list">
                                        <li><a href="javascript:;" data-switch="g-ios-appstore"><i class="fab fa-apple fa-fw"></i> iOS（Apple Store）</a></li>
                                        <li><a href="javascript:;" data-switch="g-android-baidu"><i class="fab fa-android fa-fw"></i> Android（百度手机助手）</a></li>
                                        <li><a href="javascript:;" data-switch="g-android-google"><i class="fab fa-android fa-fw"></i> Android（Google Play）</a></li>
                                    </ul>
                                </li>
                                <li>小米安全令牌
                                    <ul class="list">
                                        <li><a href="javascript:;" data-switch="mi-ios-appstore"><i class="fab fa-apple fa-fw"></i> iOS（Apple Store）</a></li>
                                        <li><a href="javascript:;" data-switch="mi-android-mi"><i class="fab fa-android fa-fw"></i> Android（小米应用商店）</a></li>
                                    </ul>
                                </li>
                            </ul>
                        </div>
                        <div class="col-md-8">
                            <div id="area-qrcode">
                                <p data-field="name" class="qrcode-name"></p>
                                <img class="qrcode-img" data-field="qrcode" src="${ static_url('img/qrcode/select-oath-app.png') }">
                                <p data-field="desc"></p>
                            </div>
                        </div>
                    </div>

                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-bind-oath" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">绑定身份验证器</h3>
                </div>
                <div class="modal-body">

                    <p>请在手机上打开身份验证器，点击增加账号按钮，然后选择“扫描条形码”并扫描下面的二维码来完成账号绑定。</p>
                    <p style="text-align: center;"><img data-field="oath-secret-qrcode" src="" style="border:1px solid #b7b7b7;"></p>
                    <p>如果无法扫描二维码，则可以选择“手动输入验证码”，设置一个容易记忆的账号名称，并确保“基于时间”一项是选中的，然后在“密钥”一项中输入下列密钥：</p>
                    <div style="text-align:center;" class="oath-code"><span data-field="tmp-oath-secret"></span></div>

                    <hr/>
                    <p>然后请在下面的动态验证码输入框中输入身份验证器提供的6位数字：</p>
                    <div class="row">
                        <div class="col-sm-4" style="text-align:right;">
                            <span style="line-height:34px;">动态验证码：</span>
                        </div>
                        <div class="col-sm-4">
                            <input type="text" class="form-control" data-field="oath-code" data-toggle="popover" data-trigger="manual" data-placement="top">
                        </div>
                    </div>
                    <div data-field="message" class="alert alert-danger" style="display:none;margin-top:10px;">aabb</div>

                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-primary" data-field="btn-submit"><i class="fa fa-check fa-fw"></i> 验证并完成绑定</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 取消</button>
                </div>
            </div>
        </div>
    </div>
</%block>

<%block name="embed_js">
    <script type="text/javascript">
        "use strict";
            ##         $app.add_options(${page_param});
            ##         console.log($app.options);
    </script>
</%block>
