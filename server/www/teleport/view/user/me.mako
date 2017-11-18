<%!
    page_icon_class_ = 'fa fa-vcard fa-fw'
    page_title_ = ['个人中心']
    page_id_ = ['me']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/user/me.js') }"></script>
</%block>

<%block name="embed_css">
    <style type="text/css">
        .oath-code {
            font-family: Consolas, Lucida Console, Monaco, Courier, 'Courier New', monospace;
            font-size: 18px;
            line-height: 26px;
            font-weight: bold;
            color: #559f47;
        }

    </style>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <div class="box box-nav-tabs">
        <!-- Nav tabs -->
        <ul class="nav nav-tabs">
            <li class="active"><a href="#info" data-toggle="tab">个人信息</a></li>
            <li><a href="#password" data-toggle="tab">修改密码</a></li>
            <li><a href="#oath" data-toggle="tab">身份验证器</a></li>
        </ul>

        <!-- Tab panes -->
        <div class="tab-content">
            <div class="tab-pane active" id="info">
                <table class="table table-info-list">
                    <tr>
                        <td class="key">登录名：</td>
                        <td class="value">${current_user['username']}</td>
                    </tr>
                    <tr>
                        <td class="key">姓名：</td>
                        <td class="value">${current_user['surname']}</td>
                    </tr>
                    <tr>
                        <td class="key">邮箱：</td>
                        <td class="value">${current_user['email']}</td>
                    </tr>
                    <tr>
                        <td class="key">手机：</td>
                        <td class="value">${current_user['mobile']}</td>
                    </tr>
                    <tr>
                        <td class="key">注册时间：</td>
                        <td class="value"><span data-field="create-time" data-value="${current_user['create_time']}"></span></td>
                    </tr>
                    <tr>
                        <td class="key">上次登录时间：</td>
                        <td class="value"><span data-field="last-login" data-value="${current_user['last_login']}"></span></td>
                    </tr>
                    <tr>
                        <td class="key">上次登录地址：</td>
                        <td class="value">${current_user['last_ip']}</td>
                    </tr>
                </table>
            </div>

            <div class="tab-pane" id="password">
                <div class="input-group input-group-sm" style="margin-top: 10px">
                    <span class="input-group-addon" style="width:90px;">当前密码:</span>
                    <input type="password" class="form-control" id="current-password">
                </div>
                <div class="input-group input-group-sm" style="margin-top: 10px">
                    <span class="input-group-addon" style="width:90px;">新密码:</span>
                    <input type="password" class="form-control" id="new-password-1">
                </div>
                <div class="input-group input-group-sm" style="margin-top: 10px">
                    <span class="input-group-addon" style="width:90px;">重复新密码:</span>
                    <input type="password" class="form-control" id="new-password-2">
                </div>
                <div style="margin-top:20px;">
                    <a href="javascript:;" id="btn-modify-password" class="btn btn-sm btn-primary"><i class="fa fa-check fa-fw"></i> 确认修改</a>
                </div>
            </div>

            <div class="tab-pane" id="oath">
                <p>请在你的手机上安装身份验证器，然后在验证器中添加你的登录账号。</p>
                <div id="oath-app-download-box" style="display:none;">
                    <p>选择你喜欢的身份验证器，扫描二维码进行安装：</p>
                    <div class="row">
                        <div class="col-md-2">
                            <p style="text-align: center;">
                                <i class="fa fa-apple"></i> iOS（Apple Store）<br/>
                                <img src="${ static_url('img/qrcode/google-oath-appstore.png') }"><br/>
                                Google身份验证器
                            </p>
                        </div>
                        <div class="col-md-2">
                            <p style="text-align: center;">
                                <i class="fa fa-android"></i> Android（百度手机助手）<br/>
                                <img src="${ static_url('img/qrcode/google-oath-baidu.png') }"><br/>
                                Google身份验证器
                            </p>
                        </div>
                        <div class="col-md-2">
                            <p style="text-align: center;">
                                <i class="fa fa-android"></i> Android（Google Play）<br/>
                                <img src="${ static_url('img/qrcode/google-oath-googleplay.png') }"><br/>
                                Google身份验证器
                            </p>
                        </div>
                        <div class="col-md-2">
                            <p style="text-align: center;">
                                <i class="fa fa-apple"></i> iOS（Apple Store）<br/>
                                <img src="${ static_url('img/qrcode/xiaomi-oath-appstore.png') }"><br/>
                                小米安全令牌
                            </p>
                        </div>
                        <div class="col-md-2">
                            <p style="text-align: center;">
                                <i class="fa fa-android"></i> Android（小米应用商店）<br/>
                                <img src="${ static_url('img/qrcode/xiaomi-oath-xiaomi.png') }"><br/>
                                小米安全令牌
                            </p>
                        </div>
                    </div>
                </div>
                <p style="margin-top:5px;"><a href="javascript:;" id="toggle-oath-download">显示下载地址 <i class="fa fa-angle-down"></i></a></p>

                <hr/>
                <p>要验证已经绑定的身份验证器，可在下面的输入框中输入验证器器上显示的动态验证码，然后点击验证。</p>
                <p>如果验证失败，请注意检查您的身份验证器的时间与服务器时间是否一致，如果两者时间偏差超过两分钟则无法验证通过！</p>
                <div style="width:360px;">
                    <div style="text-align:center;margin:20px 0 10px 0;">TELEPORT服务器时间：<span style="font-weight:bold;" class="mono" id="teleport-time">-</span></div>
                    <div class="input-group input-group-sm" style="margin-top: 10px">
                        <span class="input-group-addon">动态验证码（6位数字）：</span>
                        <input type="text" class="form-control" id="oath-code">

                        <div class="input-group-btn">
                            <button id="btn-verify-oath-code" class="btn btn-primary"><i class="fa fa-check"></i> 验证</button>
                        </div>
                    </div>
                </div>

                <hr/>
                <p>要将你的登录账号添加到身份验证器中，请点击下面的“绑定身份验证器”按钮。</p>
                <p>
                    <button id="btn-reset-oath-code" class="btn btn-sm btn-success"><i class="fa fa-refresh"></i> 绑定身份验证器</button>
                </p>

            </div>
        </div>
    </div>

</div>






<%block name="extend_content">
    <div class="modal fade" id="dialog-reset-oath-code" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">绑定身份验证器</h3>
                </div>
                <div class="modal-body">

                    <p>请在手机上打开身份验证器，点击增加账号按钮，然后选择“扫描条形码”并扫描下面的二维码来完成账号绑定。</p>
                    <p style="text-align: center;"><img id="oath-secret-qrcode" src=""></p>
                    <p>如果无法扫描二维码，则可以选择“手动输入验证码”，设置一个容易记忆的账号名称，并确保“基于时间”一项是选中的，然后在“密钥”一项中输入下列密钥：</p>
                    <div class="row">
                        <div class="col-sm-4" style="text-align:right;">
                            <span style="line-height:25px;">密钥：</span>
                        </div>
                        <div class="col-sm-8">
                            <span class="oath-code"><span id="tmp-oath-secret"></span></span>
                        </div>
                    </div>

                    <hr/>
                    <p>然后请在下面的动态验证码输入框中输入身份验证器提供的6位数字：</p>
                    <div class="row">
                        <div class="col-sm-4" style="text-align:right;">
                            <span style="line-height:34px;">动态验证码：</span>
                        </div>
                        <div class="col-sm-4">
                            <input type="text" class="form-control" id="oath-code-verify">
                        </div>
                    </div>

                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-primary" id="btn-verify-oath-and-save"><i class="fa fa-check fa-fw"></i> 验证动态验证码并完成绑定</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-close fa-fw"></i> 取消</button>
                </div>
            </div>
        </div>
    </div>
</%block>
