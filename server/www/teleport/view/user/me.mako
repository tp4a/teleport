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

        </div>
    </div>

</div>

