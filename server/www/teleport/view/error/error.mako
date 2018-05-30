<%!
    page_title_ = '错误'
    page_menu_ = ['error']
%>
<%inherit file="../page_single_base.mako"/>

<%block name="page_header">
    <div class="container-fluid top-navbar">
        <div class="brand"><a href="/" target="_blank"><span class="site-logo"></span></a></div>
        <div class="breadcrumb-container">
            <ol class="breadcrumb">
                <li><i class="far fa-file-alt"></i> <span id="page-title"></span></li>
            </ol>
        </div>
    </div>
</%block>


<div class="page-content">
    <div class="info-box">
        <div class="info-icon-box">
            <i id="icon" class="fas" style="color:#ff7545;"></i>
        </div>
        <div class="info-message-box">
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
        err_info['err_' + TPE_PRIVILEGE] = ['fa-ban', '权限不足', '您没有此访问权限！<br/><br/>如果您确定应该具有此访问权限，请联系系统管理员！<br/><br/>或者您可以选择访问<a href="/">起始页面</a>。'];
        err_info['err_' + TPE_HTTP_404_NOT_FOUND] = ['fa-unlink', '404 NOT FOUND', '您访问的地址不存在！请向系统管理员汇报此问题！<br/><br/>或者您可以选择访问<a href="/">起始页面</a>。'];
        err_info['err_' + TPE_NOT_IMPLEMENT] = ['fa-coffee', '功能未实现', '哎呀呀~~~<br/><br/>很抱歉，此功能尚未实现！敬请期待新版本！'];
        err_info['err_unknown'] = ['fa-exclamation-circle', '未知错误', '发生未知错误，错误编号：' + $app.options.err_code + '。<br/><br/>请联系系统管理员进行处理！'];

        var err_index = 'err_' + $app.options.err_code;
        if (!err_info.hasOwnProperty(err_index)) {
            err_index = 'err_unknown';
        }

        $('#icon').addClass(err_info[err_index][0]);
        $('#page-title').html(err_info[err_index][1]);
        $('#title').html(err_info[err_index][1]);
        $('#content').html(err_info[err_index][2]);
    </script>
</%block>
