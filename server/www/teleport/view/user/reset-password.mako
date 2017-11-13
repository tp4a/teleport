<%!
    page_title_ = '设置密码'
    # page_menu_ = ['error']
%>
<%inherit file="../page_single_base.mako"/>

<%block name="header_title">
    <a href="http://teleport.eomsoft.net" target="_blank"><span class="logo"></span></a>
</%block>

<%block name="extend_css_file">
    <link href="${ static_url('css/error.css') }" rel="stylesheet" type="text/css"/>
</%block>


<div class="page-content">
    <div class="error-box">
        <div class="error-icon-box">
            <i class="fa fa-warning"></i>
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
                    find-my-password
                </div>

                <div id="password-area" style="display:none;">
                    <div id="policy" class="alert alert-warning" style="margin-top:10px;">
                        注意，为增强系统安全，系统启用强密码策略，要求密码至少8位，必须包含大写字母、小写字母以及数字。
                    </div>

                    <div class="form-group form-group-sm">
                        <div class="col-sm-4">
                            <div class="input-group">
                                <input data-field="password" type="password" class="form-control mono" placeholder="设置新密码">
                                <span class="input-group-btn"><button class="btn btn-sm btn-default" type="button" id="btn-switch-password"><i class="fa fa-eye fa-fw"></i></button></span>
                            </div>
                        </div>
                        <div class="col-sm-8">
                            <button type="button" class="btn btn-sm btn-primary" id="btn-reset-password"><i class="fa fa-check fa-fw"></i> 重置密码</button>
                        </div>
                    </div>
                    <div class="clear-float"></div>
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

            err_area: $('#error-area'),
            message: $('#message'),
            actions: $('#actions'),

            find_password_area: $('#find-my-password'),

            password_area: $('#password-area')
        };

        if($app.options.mode === 1) {
            // show 'find-my-password' page
            $app.dom.title.text('找回密码');
            $app.dom.find_password_area.show();
        } else if($app.options.mode === 2) {
            // show 'password-expired' page
            $app.dom.title.text('更新密码');
        } else if($app.options.mode === 3) {
            // show 'set-new-password' page
            $app.dom.title.text('重置密码');
            $app.dom.password_area.show();
        }

##         if($app.options.code !== TPE_OK) {
##             $app.dom.message.addClass('alert alert-danger');
##
##             if($app.options.code === TPE_EXPIRED)
##                 $app.dom.message.html('很抱歉，此密码重置链接已过期！');
##             else if($app.options.code === TPE_NOT_EXISTS)
##                 $app.dom.message.html('很抱歉，此密码重置链接是无效的！');
##
##             $app.dom.err_area.show();
##             $app.dom.actions.show();
##         } else {
##             $app.dom.password_area.show();
##         }
    </script>
</%block>
