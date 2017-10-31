<%!
    page_title_ = '错误'
    page_menu_ = ['error']
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
            <div id="title" class="title"></div>
            <hr/>
            <div id="content" class="content"></div>
        </div>
    </div>
</div>

<%block name="embed_js">
    <script type="text/javascript">
        "use strict";
        $app.add_options(${page_param});

        var err_info = {};
        err_info['err_' + TPE_PRIVILEGE] = ['权限不足', '您没有访问权限！<br/><br/>如果您确定应该具有此访问权限，请联系系统管理员！<br/><br/>或者您可以选择访问<a href="/">起始页面</a>。'];
        err_info['err_' + TPE_HTTP_404_NOT_FOUND] = ['404 NOT FOUND', '您访问的页面不存在！请向系统管理员汇报此问题！<br/><br/>或者您可以选择访问<a href="/">起始页面</a>。'];
        err_info['err_unknown'] = ['未知错误', '发生未知错误，错误编号：'+ $app.options.err_code+'。<br/><br/>请联系系统管理员进行处理！'];

        var err_index = 'err_' + $app.options.err_code;
        if (!err_info.hasOwnProperty(err_index)) {
            err_index = 'err_unknown';
        }

        $('#title').html(err_info[err_index][0]);
        $('#content').html(err_info[err_index][1]);
    </script>
</%block>
